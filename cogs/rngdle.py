import discord
from discord import app_commands
from discord.ext import commands
from common import setCooldown, checkIfCooldown
import requests
import time
from datetime import datetime

rngdleapiurl = "https://www.rngdle.com/api/users/"

def getRngdleLatestRoll(username: str):
    try:
        response = requests.get(f"{rngdleapiurl}{username}/rolls?limit=1")
        if response.status_code != 200:
            print(f"Error fetching data for user '{username}': {response.status_code}")
            return {"api": response.status_code, "error": response.text}
        data = response.json()
        if not data:
            return None
        rolls = data.get("rolls", [])
        if not rolls:
            return None
        latest_roll = rolls[0]
        return latest_roll
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for user '{username}': {e}")
        return {"api": "another error", "error": str(e)}

class rngdle(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="etanbot-rngdle-latest-roll", description="Get the latest roll of a user on rngdle.com")
    @app_commands.describe(username="The username of the user on rngdle.com")
    async def rngdle_latest_roll(self, interaction: discord.Interaction, username: str):
        await interaction.response.defer()
        cooldown = checkIfCooldown(interaction.user.id, "rngdle")
        if cooldown != -1:
            await interaction.edit_original_response(content=f"You can use this command again <t:{cooldown}:R>")
            return
        setCooldown(interaction.user.id, "rngdle", 10)
        data = getRngdleLatestRoll(username)
        if data is None:
            await interaction.edit_original_response(content=f"No rolls found for user '{username}'.")
        elif "api" in data:
            await interaction.edit_original_response(content=f"Error fetching data for user '{username}': {data['api']} - {data.get('error', 'No error message')}")
        else:
            poem = data.get("poem", "[No poem]")
            timestampfixed = int(datetime.fromisoformat(data["rolledAt"].replace("Z", "+00:00")).astimezone().timestamp())
            await interaction.edit_original_response(content=f"**{username}'s latest roll** (rolled at: <t:{timestampfixed}:F>)\nNumber: `{data['number']}`\nTotal Score: `{data['totalScore']}`\nBadge Count: `{data['badgeCount']}`\nHeart Count: `{data['heartCount']}`\nPoem: `{poem}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(rngdle(bot))