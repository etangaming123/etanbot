import re

import discord
from better_profanity import profanity
from discord import app_commands
from discord.ext import commands

import common
from common import checkIfBanned, checkIfCooldown, dmUser, handleCommandAccess, setCooldown, truncateMessage
from cogs.sconf import canManage

profanity.load_censor_words()

# "i'm" / "im" / "i am" (any case, straight or curly apostrophe), word-bounded so it
# doesn't fire inside other words (e.g. "impossible").
IM_PATTERN = re.compile(r"\bi\s*(?:'|’)?\s*m\b|\bi\s+am\b", re.IGNORECASE)

def extractLastIm(content: str):
    matches = list(IM_PATTERN.finditer(content))
    if not matches:
        return None
    tail = content[matches[-1].end():].strip()
    return tail or None

# Registry of built-in autoresponders. Add more entries here as needed - each is
# off by default per guild until enabled with /sconf-enable-autoresponder.
# "extract" pulls the relevant captured text out of a message (or returns None if
# it doesn't apply); "respond" builds the reply from that captured text. Anything
# "extract" returns is checked against a profanity/slur filter before it's ever
# echoed back, so responses can't be used to launder flagged text through the bot.
AUTORESPONDERS = {
    "im": {
        "label": "I'm...",
        "description": "Replies \"hi xyz\" to messages containing \"i'm xyz\" / \"im xyz\" / \"i am xyz\" (uses the last occurrence in the message).",
        "extract": extractLastIm,
        "respond": lambda captured: "Hi, that's a long name you got there" if len(captured) > 100 else f"hi {captured}",
    },
}

def matchAutoresponderNames(current: str, names):
    if not current:
        return names[:25]
    lower_current = current.lower()
    return [n for n in names if lower_current in n.lower()][:25]

class autorespondersCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def on_autoresponder_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if checkIfBanned(message.author.id):
            return

        for key, entry in AUTORESPONDERS.items():
            if not common.isAutoresponderEnabled(message.guild.id, key):
                continue
            captured = entry["extract"](message.content)
            if not captured:
                continue
            if profanity.contains_profanity(captured):
                continue

            cooldown_name = f"autoresponder-{key}"
            if checkIfCooldown(message.author.id, cooldown_name) != -1:
                return
            setCooldown(message.author.id, cooldown_name, 10)

            try:
                await message.reply(truncateMessage(entry["respond"](captured), 2000), mention_author=False)
            except discord.Forbidden:
                await dmUser(
                    self.bot,
                    message.author.id,
                    f"I don't have permission to send messages in {message.channel.mention} (in **{message.guild.name}**), so I couldn't send an autoresponse there. Ask a server admin to grant me the **Send Messages** permission in that channel, or in the server settings.",
                )
            return

    @app_commands.command(name="sconf-enable-autoresponder", description="Enable a built-in etan bot autoresponder in this server. Requires Manage Server permission.")
    @app_commands.describe(autoresponder="The autoresponder to enable.")
    async def enable_autoresponder(self, interaction: discord.Interaction, autoresponder: str):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        await interaction.response.defer(ephemeral=True)
        if interaction.guild is None:
            await interaction.edit_original_response(content="This command must be used in a server.")
            return
        if not canManage(interaction):
            await interaction.edit_original_response(content="You need the Manage Server permission to use this command.")
            return
        if autoresponder not in AUTORESPONDERS:
            await interaction.edit_original_response(content="Couldn't find that autoresponder. Please pick one from the autocomplete suggestions.")
            return
        if common.isAutoresponderEnabled(interaction.guild_id, autoresponder):
            await interaction.edit_original_response(content=f"**{AUTORESPONDERS[autoresponder]['label']}** is already enabled in this server.")
            return
        if common.setAutoresponderEnabled(interaction.guild_id, autoresponder, True):
            await interaction.edit_original_response(content=f"Enabled **{AUTORESPONDERS[autoresponder]['label']}** in this server.")
        else:
            await interaction.edit_original_response(content="An error occurred while saving. Please try again later.")

    @enable_autoresponder.autocomplete("autoresponder")
    async def enable_autoresponder_autocomplete(self, interaction: discord.Interaction, current: str):
        if interaction.guild is None:
            return []
        names = [k for k in AUTORESPONDERS if not common.isAutoresponderEnabled(interaction.guild_id, k)]
        return [app_commands.Choice(name=AUTORESPONDERS[n]["label"], value=n) for n in matchAutoresponderNames(current, names)]

    @app_commands.command(name="sconf-disable-autoresponder", description="Disable a built-in etan bot autoresponder in this server. Requires Manage Server permission.")
    @app_commands.describe(autoresponder="The autoresponder to disable.")
    async def disable_autoresponder(self, interaction: discord.Interaction, autoresponder: str):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        await interaction.response.defer(ephemeral=True)
        if interaction.guild is None:
            await interaction.edit_original_response(content="This command must be used in a server.")
            return
        if not canManage(interaction):
            await interaction.edit_original_response(content="You need the Manage Server permission to use this command.")
            return
        if not common.isAutoresponderEnabled(interaction.guild_id, autoresponder):
            await interaction.edit_original_response(content="That autoresponder isn't currently enabled in this server.")
            return
        if common.setAutoresponderEnabled(interaction.guild_id, autoresponder, False):
            label = AUTORESPONDERS.get(autoresponder, {}).get("label", autoresponder)
            await interaction.edit_original_response(content=f"Disabled **{label}** in this server.")
        else:
            await interaction.edit_original_response(content="An error occurred while saving. Please try again later.")

    @disable_autoresponder.autocomplete("autoresponder")
    async def disable_autoresponder_autocomplete(self, interaction: discord.Interaction, current: str):
        if interaction.guild is None:
            return []
        names = common.getEnabledAutorespondersForGuild(interaction.guild_id)
        return [app_commands.Choice(name=AUTORESPONDERS[n]["label"], value=n) for n in matchAutoresponderNames(current, names) if n in AUTORESPONDERS]

    @app_commands.command(name="sconf-list-autoresponders", description="List which built-in etan bot autoresponders are enabled/disabled in this server.")
    async def list_autoresponders(self, interaction: discord.Interaction):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        await interaction.response.defer(ephemeral=True)
        if interaction.guild is None:
            await interaction.edit_original_response(content="This command must be used in a server.")
            return
        enabled = set(common.getEnabledAutorespondersForGuild(interaction.guild_id))
        embed = discord.Embed(title="Autoresponder configuration for this server", color=0x8649D7)
        for key, entry in AUTORESPONDERS.items():
            status = "✅ Enabled" if key in enabled else "❌ Disabled"
            embed.add_field(name=entry["label"], value=f"{status}\n{entry['description']}", inline=False)
        await interaction.edit_original_response(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(autorespondersCog(bot))
