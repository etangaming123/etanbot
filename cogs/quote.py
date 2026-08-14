import io
import re
import traceback

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

import quoteimage
from common import website, getDisplay, checkIfBanned, checkIfCooldown, setCooldown, dmUser, handleCommandAccess, hybridDefer, hybridReply

FONT_PATH = r"C:\Windows\Fonts\arial.ttf"
MENTION_RE = re.compile(r"<@!?(\d+)>|<@&(\d+)>|<#(\d+)>")
MESSAGE_LINK_RE = re.compile(
    r"(?:https?://(?:ptb\.|canary\.)?discord(?:app)?\.com/channels/(?:\d+|@me)/(?P<channel_id>\d+)/(?P<message_id>\d+))"
    r"|^(?P<bare_id>\d{15,20})$"
)

def resolveMentions(text, message):
    def repl(m):
        if m.group(1):
            uid = int(m.group(1))
            user = discord.utils.get(message.mentions, id=uid) or (message.guild.get_member(uid) if message.guild else None)
            return f"@{getDisplay(user)}" if user else "@unknown-user"
        if m.group(2):
            rid = int(m.group(2))
            role = discord.utils.get(message.role_mentions, id=rid) or (message.guild.get_role(rid) if message.guild else None)
            return f"@{role.name}" if role else "@unknown-role"
        if m.group(3):
            cid = int(m.group(3))
            chan = discord.utils.get(message.channel_mentions, id=cid) or (message.guild.get_channel(cid) if message.guild else None)
            return f"#{chan.name}" if chan else "#unknown-channel"
    return MENTION_RE.sub(repl, text)

async def resolveTargetMessage(ctx: commands.Context, message_link: str = None):
    """Returns (message, error). Slash invocations identify the target via a message link/ID
    (there's no "this was a reply to X" concept for a slash command); prefix invocations
    (e>quote) reuse the invoking message's own reply reference, same as the old mention-trigger did."""
    if message_link:
        m = MESSAGE_LINK_RE.match(message_link.strip())
        if not m:
            return None, "That doesn't look like a valid message link or ID."
        if m.group("bare_id"):
            channel, message_id = ctx.channel, int(m.group("bare_id"))
        else:
            channel_id = int(m.group("channel_id"))
            channel = (ctx.guild.get_channel(channel_id) if ctx.guild else None) or ctx.channel
            message_id = int(m.group("message_id"))
        try:
            return await channel.fetch_message(message_id), None
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None, "Couldn't find that message (bad link, or I can't see that channel)."

    if ctx.message.reference is None:
        if ctx.interaction is not None:
            return None, "Pass a message link to quote (right-click a message > Copy Message Link) — reply-based quoting only works with `e>quote`."
        return None, "Reply to the message you want to quote!"
    try:
        return await ctx.channel.fetch_message(ctx.message.reference.message_id), None
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return None, "Couldn't find the message you replied to!"

class quoteCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="etanbot-quote", description="Quote a message as an image. Reply to a message with e>quote, or (slash) pass a message link.", aliases=["quote"])
    @app_commands.describe(message="Link to the message to quote (not needed with e>quote as a reply).")
    async def quote(self, ctx: commands.Context, message: str = None):
        if not ctx.guild:
            await hybridReply(ctx, content="This only works in a server.")
            return
        if not await handleCommandAccess(ctx, ctx.author.id, "quote"):
            return

        original_message, error = await resolveTargetMessage(ctx, message)
        if error:
            await hybridReply(ctx, content=error)
            return

        setCooldown(ctx.author.id, "quote", 15)
        handle = await hybridDefer(ctx)

        author = original_message.author
        if not isinstance(author, discord.Member):
            author = ctx.guild.get_member(author.id) or author

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(author.display_avatar.url) as resp:
                    avatar_bytes = await resp.read()

            role_color = (255, 255, 255)
            available_colors = [role.color.to_rgb() for role in getattr(author, "roles", []) if role.color.value != 0]
            available_colors.reverse()  # reverse so higher roles take precedence
            if available_colors:
                role_color = available_colors[0]

            resolved_text = resolveMentions(original_message.content, original_message) or "*[no text content]*"

            png_bytes = await quoteimage.renderQuoteImage(
                content_text=resolved_text,
                author_display_name=getDisplay(author),
                author_username=author.name,
                avatar_bytes=avatar_bytes,
                font_path=FONT_PATH,
                role_color=role_color,
                watermark_text=f"etanbot // coded by etangaming123 // {website}",
            )

            await handle.edit(content=None, attachments=[discord.File(io.BytesIO(png_bytes), filename="quote.png")])
        except discord.Forbidden:
            await dmUser(
                self.bot,
                ctx.author.id,
                f"I don't have permission to send images in {ctx.channel.mention} (in **{ctx.guild.name}**), so I couldn't send your quote there. Ask a server admin to grant me the **Attach Files** and **Send Messages** permission in that channel, or in the server settings.",
            )
        except Exception as e:
            traceback.print_exc()
            try:
                await handle.edit(content=f"Something went wrong creating the quote image: {e}")
            except discord.Forbidden:
                await dmUser(self.bot, ctx.author.id, "Something went wrong creating your quote image, and I also don't have permission to send messages in that channel. Ask a server admin to grant me the **Attach Files** and **Send Messages** permission in that channel, or in the server settings.")

async def setup(bot: commands.Bot):
    await bot.add_cog(quoteCog(bot))
