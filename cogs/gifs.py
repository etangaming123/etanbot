import discord
from discord import app_commands
from discord.ext import commands
import difflib

from common import loadData, saveData, setCooldown, poweruserid, handleCommandAccess

gifs = loadData("gifs")

def matchGifNames(current: str, keys):
    if not current:
        return sorted(keys)[:25]
    lower_current = current.lower()
    substring_matches = sorted(k for k in keys if lower_current in k.lower())
    close_matches = difflib.get_close_matches(lower_current, [k.lower() for k in keys], n=25, cutoff=0.6)
    lower_to_key = {k.lower(): k for k in keys}
    seen = set(substring_matches)
    for lower_key in close_matches:
        key = lower_to_key[lower_key]
        if key not in seen:
            seen.add(key)
            substring_matches.append(key)
    return substring_matches[:25]

class Gifs(commands.Cog):
    global gifs
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="z-admin-gif-add", description="Adds a gif to the collection!")
    @app_commands.describe(name="The name of the gif you want to add.", gif_url="The url of the gif you want to add.")
    async def add_gif(self, interaction: discord.Interaction, name: str, gif_url: str):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
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
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
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
        return [app_commands.Choice(name=key, value=key) for key in matchGifNames(current, gifs.keys())]

    @app_commands.command(name="z-admin-gif-refresh", description="Refreshes the gif collection from the data file.")
    async def refresh_gifs(self, interaction: discord.Interaction):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        global gifs
        gifs = loadData("gifs")
        await interaction.response.send_message("Gif collection refreshed!", ephemeral=True)

    @app_commands.command(name="etanbot-gif", description="Send a gif from the shared collection!")
    @app_commands.describe(name="The name of the gif you want to view.")
    async def view_gif(self, interaction: discord.Interaction, name: str):
        if not await handleCommandAccess(interaction, interaction.user.id, "view_gif"):
            return
        await interaction.response.defer()
        setCooldown(interaction.user.id, "view_gif", 10)
        if name not in gifs.keys():
            await interaction.edit_original_response(content=f"No gif found with that name!")
            return
        await interaction.edit_original_response(content=gifs[name])
    
    @view_gif.autocomplete("name")
    async def view_gif_autocomplete(self, interaction: discord.Interaction, current: str):
        if len(gifs.keys()) == 0:
            return ["No gifs found!"]
        return [app_commands.Choice(name=key, value=key) for key in matchGifNames(current, gifs.keys())]

async def setup(bot: commands.Bot):
    await bot.add_cog(Gifs(bot))