import io
import re
import traceback

import aiohttp
import discord
from discord.ext import commands

import quoteimage
from common import website, getDisplay, checkIfBanned, checkIfCooldown, setCooldown, dmUser

FONT_PATH = quoteimage.resolveFontPath()  # first body font installed on this host, so the bot renders the same on Windows/macOS/Linux
MENTION_RE = re.compile(r"<@!?(\d+)>|<@&(\d+)>|<#(\d+)>")

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

class quoteCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def on_quote_mention(self, message: discord.Message):
        if message.author.bot or not message.guild or self.bot.user not in message.mentions:
            return
        if not message.reference:
            return  # bare mention, nothing to quote

        if checkIfBanned(message.author.id):
            return
        if checkIfCooldown(message.author.id, "quote") != -1:
            return
        setCooldown(message.author.id, "quote", 15)

        try:
            original_message = await message.channel.fetch_message(message.reference.message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            await message.reply("Couldn't find the message you replied to!", mention_author=False)
            return

        if original_message.author.id == self.bot.user.id:
            return  # don't quote the bot's own messages

        author = original_message.author
        if not isinstance(author, discord.Member):
            author = message.guild.get_member(author.id) or author

        try:
            await message.channel.typing()
            async with aiohttp.ClientSession() as session:
                async with session.get(author.display_avatar.url) as resp:
                    avatar_bytes = await resp.read()

            # the spotlight is tinted with the avatar's own main color; this is
            # only the fallback for avatars too close to greyscale to pick one
            role_color = (255, 255, 255)
            available_colors = [role.color.to_rgb() for role in getattr(author, "roles", []) if role.color.value != 0]
            available_colors.reverse()  # reverse so higher roles take precedence
            if available_colors:
                role_color = available_colors[0]

            resolved_text = resolveMentions(original_message.content, original_message) or "*[no text content]*"

            png_bytes, had_spoiler = await quoteimage.renderQuoteImage(
                content_text=resolved_text,
                author_display_name=getDisplay(author),
                author_username=author.name,
                avatar_bytes=avatar_bytes,
                font_path=FONT_PATH,
                role_color=role_color,
                watermark_text=f"etanbot // coded by etangaming123 // {website}",
            )

            # the card shows spoilered text dimmed rather than hidden, so spoiler
            # the attachment too and let the reader opt in
            await message.reply(file=discord.File(io.BytesIO(png_bytes), filename="quote.png", spoiler=had_spoiler), mention_author=False)
        except discord.Forbidden:
            await dmUser(
                self.bot,
                message.author.id,
                f"I don't have permission to send images in {message.channel.mention} (in **{message.guild.name}**), so I couldn't send your quote there. Ask a server admin to grant me the **Attach Files** and **Send Messages** permission in that channel, or in the server settings.",
            )
        except Exception as e:
            traceback.print_exc()
            try:
                await message.reply(f"Something went wrong creating the quote image: {e}", mention_author=False)
            except discord.Forbidden:
                await dmUser(self.bot, message.author.id, "Something went wrong creating your quote image, and I also don't have permission to send messages in that channel. Ask a server admin to grant me the **Attach Files** and **Send Messages** permission in that channel, or in the server settings.")

async def setup(bot: commands.Bot):
    await bot.add_cog(quoteCog(bot))
