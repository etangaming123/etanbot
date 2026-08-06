import discord
from discord import app_commands
from discord.ext import commands

from common import handleCommandAccess, saveData, loadData, userdatastores, setCooldown, purgeUserData, ConfirmView

class datamanagement(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="etanbot-list-data", description="Gets everything that etan bot has stored on your user!")
    async def listData(self, interaction: discord.Interaction):
        if not handleCommandAccess(interaction, interaction.user.id, "listdata"):
            return
        
        await interaction.response.defer(ephemeral=True)
        setCooldown(interaction.user.id, "listdata", 15)
        data = {}

        for item in userdatastores:
            read = loadData(item) # read everything that stores user data
            if read == "":
                data[item] = "[Failed to load]"
            else:
                try:
                    data[item] = str(read[str(interaction.user.id)])
                except ValueError:
                    data[item] = "[No data stored]"

        string = "**etan bot has the following data associated with you:**\n"

        for datastore, value in data.items():
            string += f"{datastore}: `{value}`\n"

        await interaction.edit_original_response(content=string)

    @app_commands.command(name="etanbot-delete-data", description="Deletes all your data from etan bot.")
    async def deleteData(self, interaction: discord.Interaction):
        if not await handleCommandAccess(interaction, interaction.user.id, "deletedata"):
            return

        view = ConfirmView(interaction.user.id)
        await interaction.response.send_message(content="Are you sure you want to delete **all** your data from etan bot? This cannot be undone.", view=view, ephemeral=True)
        await view.wait()

        if view.value is not True:
            await interaction.edit_original_response(content="Cancelled." if view.value is False else "Confirmation timed out, cancelled.", view=None)
            return

        setCooldown(interaction.user.id, "deletedata", 15)
        if purgeUserData(interaction.user.id):
            await interaction.edit_original_response(content="All your data has been deleted from etan bot.", view=None)
        else:
            await interaction.edit_original_response(content="An error occurred while deleting your data.", view=None)

async def setup(bot: commands.Bot):
    await bot.add_cog(datamanagement(bot))
