import discord  # type: ignore
from discord import app_commands  # type: ignore
from discord.ext import commands  # type: ignore
import traceback

from common import loadData, saveData, formatUsername, checkIfCooldown, setCooldown, poweruserid

class Gifs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="z-admin-gif-add", description="Adds a gif to the collection!")
    @app_commands.describe(name="The name of the gif you want to add.", gif_url="The url of the gif you want to add.")
    async def add_gif(self, interaction: discord.Interaction, name: str, gif_url: str):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.id == int(poweruserid):
            await interaction.edit_original_response(content=f"You don't have permission to use this command.")
            return
        gifs = loadData("gifs")
        if name in gifs.keys():
            await interaction.edit_original_response(content=f"A gif with that name already exists!")
            return
        gifs[name] = gif_url
        if saveData("gifs", gifs):
            await interaction.edit_original_response(content=f"Gif added successfully!")
        else:
            await interaction.edit_original_response(content=f"An error occurred while adding your gif. Please try again later.")

    @app_commands.command(name="z-admin-gif-remove", description="Removes a gif from the collection.")
    @app_commands.describe(name="The name of the gif you want to remove.")
    async def remove_gif(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.id == int(poweruserid):
            await interaction.edit_original_response(content=f"You don't have permission to use this command.")
            return
        gifs = loadData("gifs")
        if name not in gifs.keys():
            await interaction.edit_original_response(content=f"No gif found with that name!")
            return
        del gifs[name]
        if saveData("gifs", gifs):
            await interaction.edit_original_response(content=f"Gif removed successfully!")
        else:
            await interaction.edit_original_response(content=f"An error occurred while removing your gif. Please try again later.")

    @remove_gif.autocomplete("name")
    async def view_gif_autocomplete(self, interaction: discord.Interaction, current: str):
        gifs = loadData("gifs")
        if len(gifs.keys()) == 0:
            return ["No gifs found!"]
        return [app_commands.Choice(name=key, value=key) for key in gifs.keys() if current.lower() in key.lower()][:25]

    @app_commands.command(name="etanbot-gif", description="Send a gif from the shared collection!")
    @app_commands.describe(name="The name of the gif you want to view.")
    async def view_gif(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        cooldown = checkIfCooldown(interaction.user.id, "view_gif")
        if cooldown != -1:
            await interaction.edit_original_response(content=f"You can use this command again <t:{cooldown}:R>.")
            return
        setCooldown(interaction.user.id, "view_gif", 10)
        gifs = loadData("gifs")
        if name not in gifs.keys():
            await interaction.edit_original_response(content=f"No gif found with that name!")
            return
        await interaction.edit_original_response(content=gifs[name])
    
    @view_gif.autocomplete("name")
    async def view_gif_autocomplete(self, interaction: discord.Interaction, current: str):
        gifs = loadData("gifs")
        if len(gifs.keys()) == 0:
            return ["No gifs found!"]
        return [app_commands.Choice(name=key, value=key) for key in gifs.keys() if current.lower() in key.lower()][:25]

async def setup(bot: commands.Bot):
    await bot.add_cog(Gifs(bot))