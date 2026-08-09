import base64
import json
import time
import uuid
import zlib
from datetime import datetime, timezone
from io import BytesIO

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw

from common import (
    ConfirmView,
    config,
    dmUser,
    fetchUser,
    formatUsername,
    get_user_setting,
    handleCommandAccess,
    loadData,
    report_webhook_url,
    saveData,
    setCooldown,
    truncateMessage,
)

MAX_CANVAS = 512
MAX_STROKES = 300
MAX_POINTS_PER_STROKE = 3000
MAX_TOTAL_POINTS = 20000
MAX_CODE_CHARS = 4000
# generous upper bound on a decompressed v2 body: 6-byte header + MAX_STROKES * (6-byte
# stroke header + 4-byte first point) + MAX_TOTAL_POINTS * 2 bytes of deltas, rounded up.
# Used to cap zlib decompression so a crafted small compressed blob can't expand unbounded.
MAX_V2_BODY_BYTES = 45000


def decode_drawing(code: str) -> dict:
    """Decode a drawing code (see drawing.html for the matching encoder). Raises ValueError on any malformed/oversized input."""
    code = code.strip()
    if not code or len(code) > MAX_CODE_CHARS:
        raise ValueError("code is empty or too long")

    padded = code.replace("-", "+").replace("_", "/")
    padded += "=" * (-len(padded) % 4)
    try:
        raw = base64.b64decode(padded, validate=False)
    except Exception:
        raise ValueError("code isn't valid base64")

    if len(raw) < 1:
        raise ValueError("code is too short to be a drawing")

    version = raw[0]
    if version == 1:
        return {"version": 1, **_parse_stroke_body(raw[1:])}
    if version == 2:
        return {"version": 2, **_decode_drawing_v2(raw)}
    raise ValueError("unsupported drawing format version")


def _parse_stroke_body(body: bytes) -> dict:
    """Parses [width:u16le][height:u16le][strokeCount:u16le] followed by per-stroke data
    ([r:1][g:1][b:1][lineWidth:1][pointCount:u16le][x0:u16le][y0:u16le][dx:i8][dy:i8]...).
    Shared by the uncompressed v1 format and the deflate-decompressed v2 body — this is
    the original v1 body layout, unchanged, just factored out so v2 can reuse it."""
    if len(body) < 6:
        raise ValueError("code is too short to be a drawing")

    width = body[0] | (body[1] << 8)
    height = body[2] | (body[3] << 8)
    if not (1 <= width <= MAX_CANVAS and 1 <= height <= MAX_CANVAS):
        raise ValueError("invalid canvas size")

    stroke_count = body[4] | (body[5] << 8)
    if stroke_count > MAX_STROKES:
        raise ValueError("too many strokes")

    offset = 6
    strokes = []
    total_points = 0

    for _ in range(stroke_count):
        if offset + 6 > len(body):
            raise ValueError("truncated stroke header")
        r, g, b = body[offset], body[offset + 1], body[offset + 2]
        line_width = body[offset + 3]
        point_count = body[offset + 4] | (body[offset + 5] << 8)
        offset += 6

        if point_count == 0 or point_count > MAX_POINTS_PER_STROKE:
            raise ValueError("invalid point count")
        total_points += point_count
        if total_points > MAX_TOTAL_POINTS:
            raise ValueError("drawing is too complex")

        if offset + 4 > len(body):
            raise ValueError("truncated point data")
        x = body[offset] | (body[offset + 1] << 8)
        y = body[offset + 2] | (body[offset + 3] << 8)
        offset += 4

        points = [(x, y)]
        for _ in range(point_count - 1):
            if offset + 2 > len(body):
                raise ValueError("truncated delta data")
            dx, dy = body[offset], body[offset + 1]
            offset += 2
            dx = dx - 256 if dx > 127 else dx
            dy = dy - 256 if dy > 127 else dy
            x += dx
            y += dy
            points.append((x, y))

        strokes.append({"color": (r, g, b), "width": max(1, min(20, line_width)), "points": points})

    if offset != len(body):
        raise ValueError("code has trailing garbage")

    return {"width": width, "height": height, "strokes": strokes}


def _decode_drawing_v2(raw: bytes) -> dict:
    """Same stroke body as v1, but deflate-compressed (raw deflate, no gzip/zlib header —
    a few bytes cheaper per drawing). Real erasing happens client-side before export (a white
    brush splices/trims points out of existing strokes instead of adding a new one), so the
    wire format itself needs no special "eraser" concept — it's just fewer/shorter strokes."""
    compressed = raw[1:]
    decompressor = zlib.decompressobj(wbits=-15)
    try:
        # max_length caps decompressed output regardless of what the compressed stream
        # claims to encode — no zip bombs. _parse_stroke_body enforces the real limits.
        body = decompressor.decompress(compressed, MAX_V2_BODY_BYTES)
    except zlib.error:
        raise ValueError("corrupt drawing data")

    if not decompressor.eof or decompressor.unconsumed_tail or decompressor.unused_data:
        raise ValueError("drawing data is corrupt or too large")

    return _parse_stroke_body(body)


def render_drawing(drawing: dict) -> BytesIO:
    width, height, strokes = drawing["width"], drawing["height"], drawing["strokes"]
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    for stroke in strokes:
        points = stroke["points"]
        color = stroke["color"]
        line_width = stroke["width"]
        radius = max(1, line_width // 2)
        if len(points) == 1:
            x, y = points[0]
            draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)
        else:
            draw.line(points, fill=color, width=line_width, joint="curve")
            # PIL's draw.line has no round-cap option (joint="curve" only rounds internal
            # joints) - stamp a circle at each end to match the canvas's lineCap="round".
            for x, y in (points[0], points[-1]):
                draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


async def format_user_id(bot: commands.Bot, user_id: int) -> str:
    """formatUsername() by id — falls back to a raw mention if the user can't be resolved."""
    user = await fetchUser(bot, user_id)
    if user is None:
        return f"<@{user_id}>"
    return formatUsername(user)


def get_inbox(user_id: int):
    inbox = loadData("gimmickinbox")
    if inbox == "" or not isinstance(inbox, dict):
        return []
    return inbox.get(str(user_id), [])


def save_inbox(user_id: int, items: list):
    inbox = loadData("gimmickinbox")
    if inbox == "" or not isinstance(inbox, dict):
        inbox = {}
    inbox[str(user_id)] = items
    saveData("gimmickinbox", inbox)


def is_opted_in(user_id: int) -> bool:
    inbox = loadData("gimmickinbox")
    if inbox == "" or not isinstance(inbox, dict):
        return False
    return str(user_id) in inbox


def opt_in(user_id: int) -> bool:
    """Returns True if this call newly opted the user in, False if they already were."""
    inbox = loadData("gimmickinbox")
    if inbox == "" or not isinstance(inbox, dict):
        inbox = {}
    key = str(user_id)
    if key in inbox:
        return False
    inbox[key] = []
    saveData("gimmickinbox", inbox)
    return True


def opt_out(user_id: int) -> bool:
    """Removes the user's inbox entirely (opting out and deleting any pending gimmicks). Returns False if they weren't opted in."""
    inbox = loadData("gimmickinbox")
    if inbox == "" or not isinstance(inbox, dict):
        return False
    key = str(user_id)
    if key not in inbox:
        return False
    del inbox[key]
    saveData("gimmickinbox", inbox)
    return True


def get_blocked_list(blocker_id: int) -> list:
    blocked = loadData("gimmick-blocked-users")
    if blocked == "" or not isinstance(blocked, dict):
        return []
    return blocked.get(str(blocker_id), [])


def is_blocked(blocker_id: int, sender_id: int) -> bool:
    return sender_id in get_blocked_list(blocker_id)


def add_block(blocker_id: int, blocked_id: int):
    blocked = loadData("gimmick-blocked-users")
    if blocked == "" or not isinstance(blocked, dict):
        blocked = {}
    key = str(blocker_id)
    entries = blocked.setdefault(key, [])
    if blocked_id not in entries:
        entries.append(blocked_id)
    saveData("gimmick-blocked-users", blocked)


def remove_block(blocker_id: int, blocked_id: int) -> bool:
    blocked = loadData("gimmick-blocked-users")
    if blocked == "" or not isinstance(blocked, dict):
        return False
    key = str(blocker_id)
    if key not in blocked or blocked_id not in blocked[key]:
        return False
    blocked[key].remove(blocked_id)
    saveData("gimmick-blocked-users", blocked)
    return True


def get_pending_gimmick_ids() -> set:
    """IDs of gimmick log entries that are still sitting undismissed in someone's inbox."""
    inbox = loadData("gimmickinbox")
    if inbox == "" or not isinstance(inbox, dict):
        return set()
    ids = set()
    for items in inbox.values():
        for item in items:
            ids.add(item["id"])
    return ids


async def add_gimmick(bot: commands.Bot, target_id: int, gimmick_type: str, content: str, sender_id: int, anonymous: bool):
    inbox = loadData("gimmickinbox")
    if inbox == "" or not isinstance(inbox, dict):
        inbox = {}
    key = str(target_id)
    entry_id = uuid.uuid4().hex
    timestamp = time.time()
    inbox.setdefault(key, []).append({
        "id": entry_id,
        "type": gimmick_type,
        "content": content,
        "sender_id": sender_id,
        "anonymous": anonymous,
        "timestamp": timestamp,
    })
    saveData("gimmickinbox", inbox)

    log = loadData("gimmicklog")
    if log == "" or not isinstance(log, list):
        log = []
    log.append({
        "id": entry_id,
        "type": gimmick_type,
        "sender_id": sender_id,
        "target_id": target_id,
        "timestamp": timestamp,
    })
    saveData("gimmicklog", log)

    if get_user_setting(target_id, "gimmick_dm_notifications", False):
        await dmUser(bot, target_id, f"You received a new {gimmick_type} gimmick at <t:{round(timestamp)}:F>! Use `/etanbot-gimmicks` to view it.")


async def send_report(bot: commands.Bot, reporter: discord.User, target_id: int, item: dict):
    # sender_id is always included here for the power user/mods to trace and ban — this webhook
    # must point at a channel only they can read, never surfaced back to the reporter or recipient.
    if not report_webhook_url:
        return False

    embed = discord.Embed(title="Gimmick reported", color=discord.Color.red(), timestamp=datetime.now(timezone.utc))
    embed.add_field(name="Type", value=item["type"], inline=True)
    embed.add_field(name="Sender", value=f"{await format_user_id(bot, item['sender_id'])} (`{item['sender_id']}`)", inline=True)
    embed.add_field(name="Sent to", value=f"{await format_user_id(bot, target_id)} (`{target_id}`)", inline=True)
    embed.add_field(name="Shown as anonymous?", value="Yes" if item["anonymous"] else "No", inline=True)
    embed.add_field(name="Reported by", value=f"{formatUsername(reporter)} (`{reporter.id}`)", inline=True)
    embed.add_field(name="Sent at", value=f"<t:{round(item['timestamp'])}:F>", inline=True)

    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(report_webhook_url, session=session)
        if item["type"] == "draw":
            try:
                drawing = decode_drawing(item["content"])
                file = discord.File(render_drawing(drawing), filename="reported_drawing.png")
                embed.set_image(url="attachment://reported_drawing.png")
                await webhook.send(embed=embed, file=file)
            except ValueError:
                embed.add_field(name="Content", value="(drawing could not be decoded)", inline=False)
                await webhook.send(embed=embed)
        else:
            embed.add_field(name="Content", value=truncateMessage(item["content"], 1024), inline=False)
            await webhook.send(embed=embed)
    return True


async def confirm_and_report(interaction: discord.Interaction, target_id: int, item: dict):
    if not report_webhook_url:
        await interaction.response.send_message(content="This bot is missing `report_webhook_url` in `config.json`. You should contact the bot owner to configure it, then re-report the gimmick.", ephemeral=True)
        return

    view = ConfirmView(interaction.user.id)
    await interaction.response.send_message(
        content="Are you sure you want to report this gimmick? It'll be sent to etan bot's moderators for review.\n**Filing a false or malicious report may get you banned from etan bot entirely.** (don't be scared though! honest mistakes are ok)",
        view=view,
        ephemeral=True,
    )
    await view.wait()

    if view.value is not True:
        await interaction.edit_original_response(content="Cancelled." if view.value is False else "Confirmation timed out, cancelled.", view=None)
        return

    await send_report(interaction.client, interaction.user, target_id, item)
    await interaction.edit_original_response(content="Report sent!", view=None)


async def render_gimmick(bot: commands.Bot, item: dict, reveal_sender: bool, prefix: str = ""):
    header = prefix
    header += f"From: {await format_user_id(bot, item['sender_id'])}\n" if reveal_sender else "From: someone anonymous\n"

    file = None
    if item["type"] == "draw":
        try:
            drawing = decode_drawing(item["content"])
            file = discord.File(render_drawing(drawing), filename="gimmick.png")
            content = header
        except ValueError:
            content = header + "*(this drawing couldn't be displayed)*"
    else:
        content = header + item["content"]
    return content, file


async def render_current_gimmick(bot: commands.Bot, user_id: int, index: int):
    inbox = get_inbox(user_id)
    item = inbox[index]
    prefix = f"**Gimmick {index + 1}/{len(inbox)}**\n"
    return await render_gimmick(bot, item, reveal_sender=not item["anonymous"], prefix=prefix)


class GimmickViewerView(discord.ui.View):
    def __init__(self, user_id: int, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.index = 0
        self._update_button_state()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(content="These aren't your gimmicks.", ephemeral=True)
            return False
        return True

    def _update_button_state(self):
        inbox = get_inbox(self.user_id)
        self.previous_button.disabled = self.index <= 0
        self.next_button.disabled = self.index >= len(inbox) - 1

    async def refresh(self, interaction: discord.Interaction):
        self._update_button_state()
        content, file = await render_current_gimmick(interaction.client, self.user_id, self.index)
        if file is not None:
            await interaction.response.edit_message(content=content, attachments=[file], view=self)
        else:
            await interaction.response.edit_message(content=content, attachments=[], view=self)

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = max(0, self.index - 1)
        await self.refresh(interaction)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        inbox = get_inbox(self.user_id)
        self.index = min(len(inbox) - 1, self.index + 1)
        await self.refresh(interaction)

    @discord.ui.button(label="Dismiss", style=discord.ButtonStyle.danger)
    async def dismiss_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        inbox = get_inbox(self.user_id)
        if inbox:
            del inbox[self.index]
            save_inbox(self.user_id, inbox)
        if not inbox:
            self.stop()
            await interaction.response.edit_message(content="Inbox zero!", view=None, attachments=[])
            return
        self.index = min(self.index, len(inbox) - 1)
        await self.refresh(interaction)

    @discord.ui.button(label="Report", style=discord.ButtonStyle.danger, emoji="🚩")
    async def report_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        inbox = get_inbox(self.user_id)
        if not inbox or self.index >= len(inbox):
            await interaction.response.send_message(content="Nothing to report.", ephemeral=True)
            return
        await confirm_and_report(interaction, self.user_id, inbox[self.index])

    @discord.ui.button(label="Block sender", style=discord.ButtonStyle.secondary, emoji="🚫")
    async def block_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        inbox = get_inbox(self.user_id)
        if not inbox or self.index >= len(inbox):
            await interaction.response.send_message(content="Nothing to block.", ephemeral=True)
            return
        sender_id = inbox[self.index]["sender_id"]
        if sender_id == self.user_id:
            await interaction.response.send_message(content="That's self hate, dude! Not nice :(", ephemeral=True)
            return

        if is_blocked(self.user_id, sender_id):
            view = ConfirmView(interaction.user.id)
            await interaction.response.send_message(content="This sender is already blocked. Unblock them?", view=view, ephemeral=True)
            await view.wait()
            if view.value is not True:
                await interaction.edit_original_response(content="Cancelled." if view.value is False else "Confirmation timed out, cancelled.", view=None)
                return
            remove_block(self.user_id, sender_id)
            await interaction.edit_original_response(content="Unblocked.", view=None)
            return

        add_block(self.user_id, sender_id)
        await interaction.response.send_message(content="Blocked. They won't be able to send you any more gimmicks.\nGimmick broke the rules, was offensive, or otherwise? Report them as well!", ephemeral=True)

class PostedGimmickView(discord.ui.View):
    """Attached to a publicly posted gimmick. No interaction_check — anyone in the channel can report it, not just the poster."""

    def __init__(self, recipient_id: int, item: dict, timeout: float = 600):
        super().__init__(timeout=timeout)
        self.recipient_id = recipient_id
        self.item = item

    @discord.ui.button(label="Report", style=discord.ButtonStyle.danger, emoji="🚩")
    async def report_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await confirm_and_report(interaction, self.recipient_id, self.item)

    @discord.ui.button(label="Block sender", style=discord.ButtonStyle.secondary, emoji="🚫")
    async def block_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        sender_id = self.item["sender_id"]
        if sender_id == interaction.user.id:
            await interaction.response.send_message(content="That's self hate, dude! Not nice :(", ephemeral=True)
            return

        if is_blocked(interaction.user.id, sender_id):
            view = ConfirmView(interaction.user.id)
            await interaction.response.send_message(content="This sender is already blocked. Unblock them?", view=view, ephemeral=True)
            await view.wait()
            if view.value is not True:
                await interaction.edit_original_response(content="Cancelled." if view.value is False else "Confirmation timed out, cancelled.", view=None)
                return
            remove_block(interaction.user.id, sender_id)
            await interaction.edit_original_response(content="Unblocked.", view=None)
            return

        add_block(interaction.user.id, sender_id)
        await interaction.response.send_message(content="Blocked. They won't be able to send you any more gimmicks.\nGimmick broke the rules, was offensive, or otherwise? Report them as well!", ephemeral=True)

class DrawModal(discord.ui.Modal, title="Send a drawing"):
    code = discord.ui.TextInput(label="Drawing code", style=discord.TextStyle.paragraph, placeholder="Paste the code exported from the drawing page (etanbot.etangaming.xyz/drawing.html)", required=True, max_length=MAX_CODE_CHARS)
    anonymous = discord.ui.TextInput(label="Send anonymously? (yes/no)", style=discord.TextStyle.short, placeholder="yes or no", required=True, default="no", max_length=3)

    def __init__(self, target: discord.User):
        super().__init__()
        self.target = target

    async def on_submit(self, interaction: discord.Interaction):
        anon_raw = self.anonymous.value.strip().lower()
        if anon_raw in ("y", "yes"):
            anonymous = True
        elif anon_raw in ("n", "no"):
            anonymous = False
        else:
            await interaction.response.send_message(content="Please enter yes or no for the anonymous field, then try again.", ephemeral=True)
            return

        code = self.code.value.strip()
        try:
            drawing = decode_drawing(code)
            render_drawing(drawing)  # validate it actually renders before accepting
        except ValueError as e:
            await interaction.response.send_message(content=f"That drawing code couldn't be read ({e}). Make sure you copied the whole code from the drawing page.", ephemeral=True)
            return

        await add_gimmick(interaction.client, self.target.id, "draw", code, interaction.user.id, anonymous)
        await interaction.response.send_message(content=f"Sent your drawing to {formatUsername(self.target)}!", ephemeral=True)

class MessageModal(discord.ui.Modal, title="Send a message"):
    message = discord.ui.TextInput(label="Message", style=discord.TextStyle.paragraph, placeholder="Enter your message here. Max 1800 characters.", required=True, max_length=1800)
    anonymous = discord.ui.TextInput(label="Send anonymously? (yes/no)", style=discord.TextStyle.short, placeholder="yes or no", required=True, default="no", max_length=3)

    def __init__(self, target: discord.User):
        super().__init__()
        self.target = target

    async def on_submit(self, interaction: discord.Interaction):
        anon_raw = self.anonymous.value.strip().lower()
        if anon_raw in ("y", "yes"):
            anonymous = True
        elif anon_raw in ("n", "no"):
            anonymous = False
        else:
            await interaction.response.send_message(content="Please enter yes or no for the anonymous field, then try again.", ephemeral=True)
            return

        await add_gimmick(interaction.client, self.target.id, "message", self.message.value, interaction.user.id, anonymous)
        await interaction.response.send_message(content=f"Sent your message to {formatUsername(self.target)}!", ephemeral=True)


class RenderDrawingModal(discord.ui.Modal, title="Render a drawing"):
    code = discord.ui.TextInput(label="Drawing code", style=discord.TextStyle.paragraph, placeholder="Paste the code exported from the drawing page (etanbot.etangaming.xyz/drawing.html)", required=True, max_length=MAX_CODE_CHARS)

    def __init__(self, viewprivate: bool):
        super().__init__()
        self.viewprivate = viewprivate

    async def on_submit(self, interaction: discord.Interaction):
        try:
            drawing = decode_drawing(self.code.value.strip())
            file = discord.File(render_drawing(drawing), filename="drawing.png")
            await interaction.response.send_message(content="Rendered drawing:", file=file, ephemeral=self.viewprivate)
        except ValueError as e:
            await interaction.response.send_message(content=f"That drawing code couldn't be read ({e}). Make sure you copied the whole code from the drawing page.", ephemeral=True)

class GimmickTypeView(discord.ui.View):
    def __init__(self, author_id: int, target: discord.User, timeout: float = 120):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.target = target

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(content="This isn't for you.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Draw", style=discord.ButtonStyle.primary, emoji="🎨")
    async def draw_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DrawModal(self.target))

    @discord.ui.button(label="Message", style=discord.ButtonStyle.primary, emoji="✉️")
    async def message_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MessageModal(self.target))

class gimmicksCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="etanbot-gimmicks-guide", description="View the guide on the Gimmicks system.")
    async def gimmicks_guide(self, interaction: discord.Interaction):
        if not await handleCommandAccess(interaction, interaction.user.id, "gimmicks-guide"):
            return
        await interaction.response.send_message(content="etan bot Gimmicks are based off strawpage's gimmicks feature, and allow you to send drawings and messages to other users.\nTo get started, run `/etanbot-gimmicks-optin` to enable sending and receiving gimmicks!\nYou can use `/etanbot-gimmicks-send` to send a gimmick to someone (a drawing or message, as of now), and `/etanbot-gimmicks` to view your received gimmicks!\nGimmicks can also be reported, if they contain offensive content. Or, if you don't like someone's gimmicks, you can block them (works for anonymous gimmicks too!)\nWant a DM when you get a new gimmick? Configure that with `/etanbot-settings`.\n\nThis is an optional feature, and you can always opt out (and delete associated gimmicks data, excluding ones you've sent) with `/etanbot-gimmicks-optout`.", ephemeral=True)

    @app_commands.command(name="etanbot-gimmicks-send", description="Send a drawing or message gimmick to someone.")
    @app_commands.describe(target="Who to send the gimmick to.")
    async def gimmicks_send(self, interaction: discord.Interaction, target: discord.User):
        if not await handleCommandAccess(interaction, interaction.user.id, "gimmicks-send"):
            return
        if target.bot:
            await interaction.response.send_message(content="You can't send gimmicks to bots.", ephemeral=True)
            return
        if target.id == interaction.user.id:
            await interaction.response.send_message(content="You can't send a gimmick to yourself.", ephemeral=True)
            return
        if not is_opted_in(interaction.user.id):
            await interaction.response.send_message(content="You need to opt into Gimmicks first — run `/etanbot-gimmicks-optin`.", ephemeral=True)
            return
        if not is_opted_in(target.id):
            await interaction.response.send_message(content=f"{formatUsername(target)} hasn't opted into Gimmicks, so you can't send them one.", ephemeral=True)
            return
        if is_blocked(target.id, interaction.user.id):
            await interaction.response.send_message(content="You can't send a gimmick to that user.", ephemeral=True)
            return

        setCooldown(interaction.user.id, "gimmicks-send", 5)
        view = GimmickTypeView(interaction.user.id, target)
        await interaction.response.send_message(content=f"What kind of gimmick do you want to send to {formatUsername(target)}?\nIf it's a drawing gimmick, [go here](<https://etanbot.etangaming.xyz/drawing.html>) to draw and get a code!", view=view, ephemeral=True)

    @app_commands.command(name="etanbot-gimmicks", description="View gimmicks (drawings/messages) other people have sent you.")
    async def gimmicks(self, interaction: discord.Interaction):
        if not await handleCommandAccess(interaction, interaction.user.id, "gimmicks"):
            return
        if not is_opted_in(interaction.user.id):
            await interaction.response.send_message(content="You haven't opted into Gimmicks yet — run `/etanbot-gimmicks-optin` to start sending and receiving them.", ephemeral=True)
            return

        inbox = get_inbox(interaction.user.id)
        if not inbox:
            await interaction.response.send_message(content="Inbox zero!", ephemeral=True)
            return

        view = GimmickViewerView(interaction.user.id)
        content, file = await render_current_gimmick(interaction.client, interaction.user.id, 0)
        if file is not None:
            await interaction.response.send_message(content=content, file=file, view=view, ephemeral=True)
        else:
            await interaction.response.send_message(content=content, view=view, ephemeral=True)

    @app_commands.command(name="etanbot-gimmicks-post", description="Publicly post one of your received gimmicks in this channel.")
    @app_commands.describe(
        index="Which gimmick to post (matches the number shown in /etanbot-gimmicks, defaults to your oldest one).",
        reveal_author="Whether to reveal the sender's user (does not override sender's anonymity setting).",
    )
    async def gimmicks_post(self, interaction: discord.Interaction, index: app_commands.Range[int, 1, None] = 1, reveal_author: bool = False):
        if not await handleCommandAccess(interaction, interaction.user.id, "gimmicks-post"):
            return
        if not is_opted_in(interaction.user.id):
            await interaction.response.send_message(content="You haven't opted into Gimmicks yet — run `/etanbot-gimmicks-optin` to start sending and receiving them.", ephemeral=True)
            return

        inbox = get_inbox(interaction.user.id)
        if not inbox:
            await interaction.response.send_message(content="You don't have any gimmicks to post.", ephemeral=True)
            return
        if index > len(inbox):
            await interaction.response.send_message(content=f"You only have {len(inbox)} gimmick(s). Check the number shown in `/etanbot-gimmicks`.", ephemeral=True)
            return

        item = inbox[index - 1]
        setCooldown(interaction.user.id, "gimmicks-post", 5)
        effective_reveal = reveal_author and not item["anonymous"]
        content, file = await render_gimmick(interaction.client, item, reveal_sender=effective_reveal)
        view = PostedGimmickView(interaction.user.id, item)
        if file is not None:
            await interaction.response.send_message(content=content, file=file, view=view)
        else:
            await interaction.response.send_message(content=content, view=view)

    @app_commands.command(name="etanbot-gimmicks-optin", description="Opt into Gimmicks so you can send/receive drawings and messages.")
    async def gimmicks_optin(self, interaction: discord.Interaction):
        if not await handleCommandAccess(interaction, interaction.user.id, "gimmicks-optin"):
            return
        if opt_in(interaction.user.id):
            await interaction.response.send_message(content="You're opted into Gimmicks! Others can now send you drawings and messages with `/etanbot-gimmicks-send`, and you can send to other opted-in users too. Opt out at any time with `/etanbot-gimmicks-optout`.\nPsst - Want to get DMs on new gimmicks? Check out your `/etanbot-settings`!", ephemeral=True)
        else:
            await interaction.response.send_message(content="You're already opted into Gimmicks.", ephemeral=True)

    @app_commands.command(name="etanbot-gimmicks-optout", description="Opt out of Gimmicks. Deletes all gimmicks currently in your inbox!")
    async def gimmicks_optout(self, interaction: discord.Interaction):
        if not await handleCommandAccess(interaction, interaction.user.id, "gimmicks-optout"):
            return
        if not is_opted_in(interaction.user.id):
            await interaction.response.send_message(content="You're not opted into Gimmicks.", ephemeral=True)
            return

        pending_count = len(get_inbox(interaction.user.id))
        view = ConfirmView(interaction.user.id)
        await interaction.response.send_message(
            content=(
                f"Are you sure you want to opt out of Gimmicks? **This will permanently delete all {pending_count} gimmick(s) currently in your inbox** "
                "(drawings/messages sent to you), and you won't be able to send or receive gimmicks until you opt back in with `/etanbot-gimmicks-optin`. This cannot be undone."
            ),
            view=view,
            ephemeral=True,
        )
        await view.wait()

        if view.value is not True:
            await interaction.edit_original_response(content="Cancelled." if view.value is False else "Confirmation timed out, cancelled.", view=None)
            return

        if opt_out(interaction.user.id):
            await interaction.edit_original_response(content="You've been opted out of Gimmicks. All your pending gimmicks have been deleted.", view=None)
        else:
            await interaction.edit_original_response(content="You weren't opted in to begin with.", view=None)

    @app_commands.command(name="etanbot-gimmicks-block", description="Block a user from sending you gimmicks.")
    @app_commands.describe(target="The user to block.")
    async def gimmicks_block(self, interaction: discord.Interaction, target: discord.User):
        if not await handleCommandAccess(interaction, interaction.user.id, "gimmicks-block"):
            return
        if target.id == interaction.user.id:
            await interaction.response.send_message(content="You can't block yourself.", ephemeral=True)
            return
        add_block(interaction.user.id, target.id)
        await interaction.response.send_message(content=f"Blocked {formatUsername(target)}. They won't be able to send you any more gimmicks.", ephemeral=True)

    @app_commands.command(name="etanbot-gimmicks-unblock", description="Unblock a user you previously blocked from sending you gimmicks.")
    @app_commands.describe(target="The user to unblock.")
    async def gimmicks_unblock(self, interaction: discord.Interaction, target: discord.User):
        if not await handleCommandAccess(interaction, interaction.user.id, "gimmicks-unblock"):
            return
        if remove_block(interaction.user.id, target.id):
            await interaction.response.send_message(content=f"Unblocked {formatUsername(target)}.", ephemeral=True)
        else:
            await interaction.response.send_message(content=f"{formatUsername(target)} isn't blocked.", ephemeral=True)

    @app_commands.command(name="etanbot-gimmick-drawing-render", description="Render a drawing gimmick code into an image.")
    @app_commands.describe(viewprivate="Whether to send the rendered image privately (ephemeral) or in the channel.")
    async def gimmick_drawing(self, interaction: discord.Interaction, viewprivate: bool = True):
        if not await handleCommandAccess(interaction, interaction.user.id, "gimmick-drawing"):
            return
        await interaction.response.send_modal(RenderDrawingModal(viewprivate))

    @app_commands.command(name="z-admin-gimmick-logs", description="List gimmick log entries with sender/target/dismissed status. (Admin only)")
    @app_commands.describe(user="Only show entries involving this user (as sender or recipient).")
    async def gimmick_logs(self, interaction: discord.Interaction, user: discord.User = None):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        if interaction.user.id != int(config["poweruserid"]):
            await interaction.response.send_message(content="You don't have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        log = loadData("gimmicklog")
        if log == "" or not isinstance(log, list):
            log = []
        pending_ids = get_pending_gimmick_ids()

        entries = []
        for entry in log:
            if user is not None and user.id not in (entry["sender_id"], entry["target_id"]):
                continue
            entries.append({**entry, "dismissed": entry["id"] not in pending_ids})

        if not entries:
            await interaction.edit_original_response(content="No matching gimmick log entries.")
            return

        payload = json.dumps(entries, indent=2).encode("utf-8")
        file = discord.File(BytesIO(payload), filename="gimmicklogs.json")
        dismissed_count = sum(1 for e in entries if e["dismissed"])
        await interaction.edit_original_response(
            content=f"{len(entries)} entr{'y' if len(entries) == 1 else 'ies'} ({dismissed_count} dismissed, {len(entries) - dismissed_count} still pending).",
            attachments=[file],
        )

    @app_commands.command(name="z-admin-gimmick-logs-delete", description="Delete gimmick log entries to reduce stored data. (Admin only)")
    @app_commands.describe(scope="Which entries to delete.", user="Delete entries involving this user. (required if scope is 'A specific user')")
    @app_commands.choices(scope=[
        app_commands.Choice(name="Dismissed/read gimmicks only (keeps records for still-pending ones)", value="dismissed"),
        app_commands.Choice(name="All gimmick logs, including still-pending ones", value="all"),
        app_commands.Choice(name="A specific user", value="user"),
    ])
    async def gimmick_logs_delete(self, interaction: discord.Interaction, scope: app_commands.Choice[str], user: discord.User = None):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        if interaction.user.id != int(config["poweruserid"]):
            await interaction.response.send_message(content="You don't have permission to use this command.", ephemeral=True)
            return
        if scope.value == "user" and user is None:
            await interaction.response.send_message(content="You must specify a user when scope is 'A specific user'.", ephemeral=True)
            return

        log = loadData("gimmicklog")
        if log == "" or not isinstance(log, list):
            log = []
        pending_ids = get_pending_gimmick_ids()

        if scope.value == "dismissed":
            to_delete = [e for e in log if e["id"] not in pending_ids]
        elif scope.value == "all":
            to_delete = list(log)
        else:
            to_delete = [e for e in log if user.id in (e["sender_id"], e["target_id"])]
        delete_ids = {e["id"] for e in to_delete}
        remaining = [e for e in log if e["id"] not in delete_ids]

        if not to_delete:
            await interaction.response.send_message(content="No matching gimmick log entries to delete.", ephemeral=True)
            return

        still_pending = sum(1 for e in to_delete if e["id"] in pending_ids)
        warning = ""
        if still_pending:
            warning = f"\n**Warning:** {still_pending} of these are for gimmicks that haven't been dismissed by their recipient yet. Deleting their log entry removes the ability to trace who sent them if reported later. (you probably shouldn't do this, unless in a test instance)"

        view = ConfirmView(interaction.user.id)
        await interaction.response.send_message(
            content=f"This will permanently delete {len(to_delete)} gimmick log entr{'y' if len(to_delete) == 1 else 'ies'}. This cannot be undone.{warning}",
            view=view,
            ephemeral=True,
        )
        await view.wait()

        if view.value is not True:
            await interaction.edit_original_response(content="Cancelled." if view.value is False else "Confirmation timed out, cancelled.", view=None)
            return

        if saveData("gimmicklog", remaining):
            await interaction.edit_original_response(content=f"Deleted {len(to_delete)} gimmick log entr{'y' if len(to_delete) == 1 else 'ies'}.", view=None)
        else:
            await interaction.edit_original_response(content="An error occurred while deleting log entries.", view=None)

async def setup(bot: commands.Bot):
    await bot.add_cog(gimmicksCog(bot))
