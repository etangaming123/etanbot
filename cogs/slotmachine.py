import discord
from discord.ext import commands
from discord import app_commands
import random

from common import setCooldown, handleCommandAccess

symbols = {"🍒": 100, "🍋": 90, "🍊": 80, "🍉": 70, "🍇": 60, "⭐": 50, "💎": 25}
fishChance = 1 / 100000  # 1 in 100 thousand. Good luck

def rollSpin():
    if random.random() < fishChance:
        return ["🐟", "🐟", "🐟"]
    return [random.choices(list(symbols.keys()), weights=list(symbols.values()))[0] for _ in range(3)]

class slotMachine(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="etanbot-slotmachine-spin", description="Spin the slot machine, for fun!")
    async def slot(self, interaction: discord.Interaction):
        if not await handleCommandAccess(interaction, interaction.user.id, "slotmachine-spin"):
            return
        await interaction.response.defer()        
        setCooldown(interaction.user.id, "slotmachine-spin", 1)
        result = rollSpin()

        if result[0] == "🐟": # Secret jackpot
            await interaction.edit_original_response(content=f"## \> {result[0]} {result[1]} {result[2]} <\n**🐟 fish 🐟**")
        elif result[0] == result[1] == result[2]: # All symbols are the same
            await interaction.edit_original_response(content=f"## \> {result[0]} {result[1]} {result[2]} <\n**Big winnings!**")
        else:
            await interaction.edit_original_response(content=f"## \> {result[0]} {result[1]} {result[2]} <")

    @app_commands.command(name="etanbot-slotmachine-spin-multi", description="Spin the slot machine multiple times in a row!")
    @app_commands.describe(times="How many times to spin (1-20)")
    async def slot_multi(self, interaction: discord.Interaction, times: app_commands.Range[int, 1, 20]):
        if not await handleCommandAccess(interaction, interaction.user.id, "slotmachine-spin-multi"):
            return
        await interaction.response.defer()
        setCooldown(interaction.user.id, "slotmachine-spin-multi", times)

        lines = []
        for _ in range(times):
            result = rollSpin()
            line = f"[{result[0]}, {result[1]}, {result[2]}]"
            if result[0] == "🐟":
                line += " **🐟 fish 🐟**"
            elif result[0] == result[1] == result[2]:
                line += " **Big winnings!**"
            lines.append(line)

        await interaction.edit_original_response(content="\n".join(lines))

    @app_commands.command(name="etanbot-slotmachine-info", description="Get information about the slot machine.")
    async def slot_info(self, interaction: discord.Interaction):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        await interaction.response.defer()
        total = sum(symbols.values())
        triples = {item: (weight / total) ** 3 for item, weight in symbols.items()}
        triple_total = sum(triples.values())
        string = "**slot machine is free and will always be free. all you win is bragging rights :)**\nsymbols, weights (lower is rarer!), and theoretical odds:\n"
        for item, weight in symbols.items():
            chance = triples[item]
            string += f"{item}: {weight} / {chance:.4%} chance of winning / {chance / triple_total:.3%} of all winnings\n"
        await interaction.edit_original_response(content=string)

async def setup(bot: commands.Bot):
    await bot.add_cog(slotMachine(bot))