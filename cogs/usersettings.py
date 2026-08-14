import discord
from discord.ext import commands

from common import get_user_setting, handleCommandAccess, hybridReply, set_user_setting

# Registry of per-user settings shown in /etanbot-settings. Other cogs' settings
# can be added here later as this grows beyond gimmicks-only.
SETTINGS = {
    "gimmick_dm_notifications": {
        "label": "Gimmick DM Notifications",
        "description": "Get a Direct Message whenever someone sends you a gimmick. (add etan bot to account first!)",
        "default": False,
    },
}


class OptionsView(discord.ui.View):
    def __init__(self, user_id: int, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.selected = next(iter(SETTINGS))
        self._update_state()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(content="These aren't your settings.", ephemeral=True)
            return False
        return True

    def _current_value(self) -> bool:
        meta = SETTINGS[self.selected]
        return get_user_setting(self.user_id, self.selected, meta["default"])

    def _update_state(self):
        current = self._current_value()
        self.on_button.style = discord.ButtonStyle.success if current else discord.ButtonStyle.secondary
        self.off_button.style = discord.ButtonStyle.danger if not current else discord.ButtonStyle.secondary
        for option in self.setting_select.options:
            option.default = option.value == self.selected

    def render_content(self) -> str:
        meta = SETTINGS[self.selected]
        state = "**On**" if self._current_value() else "**Off**"
        return f"**{meta['label']}**\n{meta['description']}\n\nCurrently: {state}"

    @discord.ui.select(placeholder="Choose a setting...", options=[
        discord.SelectOption(label=meta["label"], value=key, description=meta["description"])
        for key, meta in SETTINGS.items()
    ])
    async def setting_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.selected = select.values[0]
        self._update_state()
        await interaction.response.edit_message(content=self.render_content(), view=self)

    @discord.ui.button(label="On", style=discord.ButtonStyle.secondary, row=1)
    async def on_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        set_user_setting(self.user_id, self.selected, True)
        self._update_state()
        await interaction.response.edit_message(content=self.render_content(), view=self)

    @discord.ui.button(label="Off", style=discord.ButtonStyle.secondary, row=1)
    async def off_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        set_user_setting(self.user_id, self.selected, False)
        self._update_state()
        await interaction.response.edit_message(content=self.render_content(), view=self)


class usersettingsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="etanbot-settings", description="Configure your etan bot settings.", aliases=["settings"])
    async def settings(self, ctx: commands.Context):
        if not await handleCommandAccess(ctx, ctx.author.id, "settings"):
            return
        view = OptionsView(ctx.author.id)
        await hybridReply(ctx, content=view.render_content(), view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(usersettingsCog(bot))
