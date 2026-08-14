import discord
from discord import app_commands
from discord.ext import commands
import difflib

from common import loadData, saveData, setCooldown, poweruserid, handleCommandAccess, hybridReply, hybridDefer, requireDMOnly

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

    @commands.hybrid_command(name="z-admin-gif-add", description="Adds a gif to the collection!", aliases=["admingifadd"])
    @app_commands.describe(name="The name of the gif you want to add.", gif_url="The url of the gif you want to add.")
    async def add_gif(self, ctx: commands.Context, name: str, gif_url: str):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        if not await requireDMOnly(ctx):
            return
        handle = await hybridDefer(ctx, ephemeral=True)
        if not ctx.author.id == int(poweruserid):
            await handle.edit(content=f"You don't have permission to use this command.")
            return
        gifs = loadData("gifs")
        if name in gifs.keys():
            await handle.edit(content=f"A gif with that name already exists!")
            return
        gifs[name] = gif_url
        if saveData("gifs", gifs):
            await handle.edit(content=f"Gif added successfully!")
        else:
            await handle.edit(content=f"An error occurred while adding your gif. Please try again later.")

    @commands.hybrid_command(name="z-admin-gif-remove", description="Removes a gif from the collection.", aliases=["admingifremove"])
    @app_commands.describe(name="The name of the gif you want to remove.")
    async def remove_gif(self, ctx: commands.Context, name: str):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        if not await requireDMOnly(ctx):
            return
        handle = await hybridDefer(ctx, ephemeral=True)
        if not ctx.author.id == int(poweruserid):
            await handle.edit(content=f"You don't have permission to use this command.")
            return
        gifs = loadData("gifs")
        if name not in gifs.keys():
            await handle.edit(content=f"No gif found with that name!")
            return
        del gifs[name]
        if saveData("gifs", gifs):
            await handle.edit(content=f"Gif removed successfully!")
        else:
            await handle.edit(content=f"An error occurred while removing your gif. Please try again later.")

    @remove_gif.autocomplete("name")
    async def view_gif_autocomplete(self, interaction: discord.Interaction, current: str):
        gifs = loadData("gifs")
        if len(gifs.keys()) == 0:
            return ["No gifs found!"]
        return [app_commands.Choice(name=key, value=key) for key in matchGifNames(current, gifs.keys())]

    @commands.hybrid_command(name="z-admin-gif-refresh", description="Refreshes the gif collection from the data file.", aliases=["admingifrefresh"])
    async def refresh_gifs(self, ctx: commands.Context):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        if not await requireDMOnly(ctx):
            return
        global gifs
        gifs = loadData("gifs")
        await hybridReply(ctx, content="Gif collection refreshed!", ephemeral=True)

    @commands.hybrid_command(name="etanbot-gif", description="Send a gif from the shared collection!", aliases=["gif"])
    @app_commands.describe(name="The name of the gif you want to view.")
    async def view_gif(self, ctx: commands.Context, name: str):
        if not await handleCommandAccess(ctx, ctx.author.id, "view_gif"):
            return
        handle = await hybridDefer(ctx)
        setCooldown(ctx.author.id, "view_gif", 10)
        if name not in gifs.keys():
            await handle.edit(content=f"No gif found with that name!")
            return
        await handle.edit(content=gifs[name])

    @view_gif.autocomplete("name")
    async def view_gif_autocomplete(self, interaction: discord.Interaction, current: str):
        if len(gifs.keys()) == 0:
            return ["No gifs found!"]
        return [app_commands.Choice(name=key, value=key) for key in matchGifNames(current, gifs.keys())]

async def setup(bot: commands.Bot):
    await bot.add_cog(Gifs(bot))