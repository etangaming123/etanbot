import discord
from discord.ext import commands
from discord import app_commands
import random

from common import setCooldown, checkIfCooldown, handleCommandAccess, hybridDefer

symbols = {"🍒": 5, "🍋": 4, "🍊": 3, "🍉": 2, "🍇": 2, "⭐": 1, "💎": 0.1}

class slotMachine(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="etanbot-slotmachine-spin", description="Spin the slot machine, for fun!", aliases=["slots"])
    async def slot(self, ctx: commands.Context):
        if not await handleCommandAccess(ctx, ctx.author.id, "slotmachine-spin"):
            return
        handle = await hybridDefer(ctx)
        setCooldown(ctx.author.id, "slotmachine-spin", 1)
        result = [random.choices(list(symbols.keys()), weights=list(symbols.values()))[0] for _ in range(3)]

        if result[0] == result[1] == result[2]: # All symbols are the same
            await handle.edit(content=f"## \> {result[0]} {result[1]} {result[2]} <\n**Big winnings!**")
        else:
            await handle.edit(content=f"## \> {result[0]} {result[1]} {result[2]} <")

    @commands.hybrid_command(name="etanbot-slotmachine-info", description="Get information about the slot machine.", aliases=["slotsinfo"])
    async def slot_info(self, ctx: commands.Context):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx)
        string = "slot machine is free and will always be free. all you win is bragging rights :)\nsymbols and weights (lower is rarer!):\n"
        for item in symbols:
            string += f"{item}: {symbols[item]}\n"
        await handle.edit(content=string)

async def setup(bot: commands.Bot):
    await bot.add_cog(slotMachine(bot))