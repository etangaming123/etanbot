import discord
from discord import app_commands
from discord.ext import commands

import common
from common import handleCommandAccess

def isToggleable(cmd) -> bool: # excludes bot-owner-only, sconf's own commands (self-lockout protection), always-ephemeral commands, and essential/general commands (server config can't affect any of these)
    if cmd.name.startswith("z-admin-") or cmd.name.startswith("sconf-"):
        return False
    if cmd.extras.get("ephemeral") or cmd.extras.get("essential"):
        return False
    return True

def toggleableCommandNames(bot: commands.Bot):
    return sorted(cmd.name for cmd in bot.tree.get_commands() if isToggleable(cmd))

def matchCommandNames(current: str, names):
    if not current:
        return names[:25]
    lower_current = current.lower()
    return [n for n in names if lower_current in n.lower()][:25]

def canManage(interaction: discord.Interaction) -> bool:
    if common.isPoweruser(interaction.user.id):
        return True
    return interaction.guild is not None and interaction.user.guild_permissions.manage_guild

def categoryForCommand(cmd) -> str:
    if cmd.binding is None:
        return "General"
    name = cmd.binding.qualified_name
    return name[:-3] if name.endswith("Cog") else name

def buildCategories(bot: commands.Bot):
    categories = {}
    for cmd in bot.tree.get_commands():
        if not isToggleable(cmd):
            continue
        categories.setdefault(categoryForCommand(cmd), []).append(cmd.name)
    for names in categories.values():
        names.sort()
    return dict(sorted(categories.items(), key=lambda kv: kv[0].lower()))

def buildCommandListEmbed(categories: dict, disabled: set, selected: str) -> discord.Embed:
    embed = discord.Embed(title="Command configuration for this server", color=0x8649D7)
    if selected == "All":
        for category, names in categories.items():
            lines = "\n".join(f"{'❌' if n in disabled else '✅'} `/{n}`" for n in names)
            embed.add_field(name=category, value=lines[:1024], inline=False)
    else:
        names = categories.get(selected, [])
        lines = "\n".join(f"{'❌' if n in disabled else '✅'} `/{n}`" for n in names) or "No commands in this category."
        embed.description = lines[:4000]
    return embed

class CategorySelect(discord.ui.Select):
    def __init__(self, categories: dict, disabled: set):
        self.categories = categories
        self.disabled_commands = disabled
        options = [discord.SelectOption(label="All", value="All", default=True)]
        options += [discord.SelectOption(label=category, value=category) for category in categories.keys()]
        super().__init__(placeholder="Choose a category...", options=options[:25], min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        for option in self.options:
            option.default = option.value == selected
        embed = buildCommandListEmbed(self.categories, self.disabled_commands, selected)
        await interaction.response.edit_message(embed=embed, view=self.view)

class CommandListView(discord.ui.View):
    def __init__(self, author_id: int, categories: dict, disabled: set, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.add_item(CategorySelect(categories, disabled))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(content="Run the command yourself to use this menu.", ephemeral=True)
            return False
        return True

class sconfCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="sconf-disable-command", description="Disable an etan bot command in this server. Requires Manage Server permission.")
    @app_commands.describe(command="The command to disable.")
    async def disable_command(self, interaction: discord.Interaction, command: str):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        await interaction.response.defer(ephemeral=True)
        if interaction.guild is None:
            await interaction.edit_original_response(content="This command must be used in a server.")
            return
        if not canManage(interaction):
            await interaction.edit_original_response(content="You need the Manage Server permission to use this command.")
            return
        if command not in toggleableCommandNames(self.bot):
            await interaction.edit_original_response(content="Couldn't find that command. Please pick one from the autocomplete suggestions.")
            return
        if common.isCommandDisabled(interaction.guild_id, command):
            await interaction.edit_original_response(content=f"`/{command}` is already disabled in this server.")
            return
        if common.setCommandDisabled(interaction.guild_id, command, True):
            await interaction.edit_original_response(content=f"Disabled `/{command}` in this server.")
        else:
            await interaction.edit_original_response(content="An error occurred while saving. Please try again later.")

    @disable_command.autocomplete("command")
    async def disable_command_autocomplete(self, interaction: discord.Interaction, current: str):
        if interaction.guild is None:
            return []
        names = [n for n in toggleableCommandNames(self.bot) if not common.isCommandDisabled(interaction.guild_id, n)]
        return [app_commands.Choice(name=n, value=n) for n in matchCommandNames(current, names)]

    @app_commands.command(name="sconf-enable-command", description="Re-enable a disabled etan bot command in this server. Requires Manage Server permission.")
    @app_commands.describe(command="The command to re-enable.")
    async def enable_command(self, interaction: discord.Interaction, command: str):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        await interaction.response.defer(ephemeral=True)
        if interaction.guild is None:
            await interaction.edit_original_response(content="This command must be used in a server.")
            return
        if not canManage(interaction):
            await interaction.edit_original_response(content="You need the Manage Server permission to use this command.")
            return
        if not common.isCommandDisabled(interaction.guild_id, command):
            await interaction.edit_original_response(content=f"`/{command}` isn't currently disabled in this server.")
            return
        if common.setCommandDisabled(interaction.guild_id, command, False):
            await interaction.edit_original_response(content=f"Re-enabled `/{command}` in this server.")
        else:
            await interaction.edit_original_response(content="An error occurred while saving. Please try again later.")

    @enable_command.autocomplete("command")
    async def enable_command_autocomplete(self, interaction: discord.Interaction, current: str):
        if interaction.guild is None:
            return []
        names = sorted(common.getDisabledCommandsForGuild(interaction.guild_id))
        return [app_commands.Choice(name=n, value=n) for n in matchCommandNames(current, names)]

    @app_commands.command(name="sconf-list-commands", description="List which etan bot commands are enabled/disabled in this server.")
    async def list_commands(self, interaction: discord.Interaction):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        await interaction.response.defer(ephemeral=True)
        if interaction.guild is None:
            await interaction.edit_original_response(content="This command must be used in a server.")
            return
        categories = buildCategories(self.bot)
        if not categories:
            await interaction.edit_original_response(content="No toggleable commands found.")
            return
        disabled = set(common.getDisabledCommandsForGuild(interaction.guild_id))
        embed = buildCommandListEmbed(categories, disabled, "All")
        view = CommandListView(interaction.user.id, categories, disabled)
        await interaction.edit_original_response(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(sconfCog(bot))
