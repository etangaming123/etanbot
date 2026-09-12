import asyncio
import re
import traceback

import discord
from deep_translator import GoogleTranslator
from discord.ext import commands

from common import checkIfBanned, checkIfCooldown, setCooldown, dmUser, resolveMentions, truncateMessage

# shorthand/alias -> language string deep-translator understands (full names or ISO codes both work)
LANGUAGE_ALIASES = {
    "auto": "auto",
    "en": "english", "eng": "english", "english": "english",
    "vn": "vietnamese", "vi": "vietnamese", "viet": "vietnamese", "vietnamese": "vietnamese",
    "kr": "korean", "ko": "korean", "korean": "korean",
    "jp": "japanese", "ja": "japanese", "japanese": "japanese",
    "cn": "chinese (simplified)", "zh": "chinese (simplified)", "chinese": "chinese (simplified)",
    "tw": "chinese (traditional)",
    "es": "spanish", "spanish": "spanish",
    "fr": "french", "french": "french",
    "de": "german", "ger": "german", "german": "german",
    "pt": "portuguese", "portuguese": "portuguese",
    "ru": "russian", "russian": "russian",
    "it": "italian", "italian": "italian",
    "nl": "dutch", "dutch": "dutch",
    "pl": "polish", "polish": "polish",
    "tr": "turkish", "turkish": "turkish",
    "ar": "arabic", "arabic": "arabic",
    "hi": "hindi", "hindi": "hindi",
    "th": "thai", "thai": "thai",
    "id": "indonesian", "indonesian": "indonesian",
    "sv": "swedish", "swedish": "swedish",
    "fi": "finnish", "finnish": "finnish",
    "uk": "ukrainian", "ukrainian": "ukrainian",
}

def resolveLanguage(raw: str) -> str:
    return LANGUAGE_ALIASES.get(raw.lower(), raw.lower())

class translateCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def on_translate_mention(self, message: discord.Message):
        if message.author.bot or not message.guild or self.bot.user not in message.mentions:
            return
        if not message.reference:
            return  # bare mention, nothing to translate

        mention_re = re.compile(rf"^<@!?{self.bot.user.id}>\s*")
        remainder = mention_re.sub("", message.content, count=1).strip()
        command_match = re.match(r"translate\b", remainder, re.IGNORECASE)
        if not command_match:
            return
        args = remainder[command_match.end():].split()
        if len(args) >= 2:
            source, target = args[0], args[1]
        elif len(args) == 1:
            source, target = "auto", args[0]
        else:
            source, target = "auto", "english"
        source = resolveLanguage(source)
        target = resolveLanguage(target)

        if checkIfBanned(message.author.id):
            return
        if checkIfCooldown(message.author.id, "translate") != -1:
            return
        setCooldown(message.author.id, "translate", 30)

        try:
            original_message = await message.channel.fetch_message(message.reference.message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            await message.reply("Couldn't find the message you replied to!", mention_author=False)
            return

        original_text = resolveMentions(original_message.content, original_message)
        if not original_text:
            await message.reply("That message has no text content to translate!", mention_author=False)
            return

        if len(original_text) > 500:
            await message.reply("That message is too long to translate (max 500 characters)!", mention_author=False)
            return

        try:
            await message.channel.typing()
            translated = None
            for attempt in range(3):
                try:
                    translated = await asyncio.to_thread(
                        GoogleTranslator(source=source, target=target).translate,
                        original_text,
                    )
                    if "Error 500 (Server Error)!!1500.That’s an error.There was an error. Please try again later.That’s all we know." in translated:
                        raise RuntimeError("Google Translate returned an error")
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    await asyncio.sleep(1)
            reply_text = truncateMessage(f"**Translating from `{source}` to `{target}`...**\noriginal:\n{original_text}\n\ntranslated:\n{translated}", 2000)
            await message.reply(reply_text, mention_author=False)
        except discord.Forbidden:
            await dmUser(
                self.bot,
                message.author.id,
                f"I don't have permission to send messages in {message.channel.mention} (in **{message.guild.name}**), so I couldn't send your translation there. Ask a server admin to grant me the **Send Messages** permission in that channel, or in the server settings.",
            )
        except Exception as e:
            traceback.print_exc()
            try:
                await message.reply(f"Something went wrong translating that message: {e}\n(Check that `{source}` and `{target}` are valid languages.)", mention_author=False)
            except discord.Forbidden:
                await dmUser(self.bot, message.author.id, "Something went wrong translating that message, and I also don't have permission to send messages in that channel. Ask a server admin to grant me the **Send Messages** permission in that channel, or in the server settings.")

async def setup(bot: commands.Bot):
    await bot.add_cog(translateCog(bot))
