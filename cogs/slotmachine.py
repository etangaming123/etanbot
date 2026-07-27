import discord
from discord.ext import commands
from discord import app_commands
import random

from common import setCooldown, checkIfCooldown, handleCommandAccess

symbols = {"🍒": 5, "🍋": 4, "🍊": 3, "🍉": 2, "🍇": 2, "⭐": 1, "💎": 0.1}

class slotMachine(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="etanbot-slotmachine-spin", description="Spin the slot machine, for fun!")
    async def slot(self, interaction: discord.Interaction):
        if not await handleCommandAccess(interaction, interaction.user.id, "slotmachine-spin"):
            return
        await interaction.response.defer()        
        setCooldown(interaction.user.id, "slotmachine-spin", 1)
        result = [random.choices(list(symbols.keys()), weights=list(symbols.values()))[0] for _ in range(3)]

        if result[0] == result[1] == result[2]: # All symbols are the same
            await interaction.edit_original_response(content=f"## \> {result[0]} {result[1]} {result[2]} <\n**Big winnings!**")
        else:
            await interaction.edit_original_response(content=f"## \> {result[0]} {result[1]} {result[2]} <")

    @app_commands.command(name="etanbot-slotmachine-info", description="Get information about the slot machine.")
    async def slot_info(self, interaction: discord.Interaction):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        await interaction.response.defer()
        string = "slot machine is free and will always be free. all you win is bragging rights :)\nsymbols and weights (lower is rarer!):\n"
        for item in symbols:
            string += f"{item}: {symbols[item]}\n"
        await interaction.edit_original_response(content=string)

async def setup(bot: commands.Bot):
    await bot.add_cog(slotMachine(bot))