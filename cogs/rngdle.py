import discord
from discord import app_commands
from discord.ext import commands
from common import setCooldown, checkIfCooldown, handleCommandAccess, hybridDefer
import requests
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

    @commands.hybrid_command(name="etanbot-rngdle-latest-roll", description="Get the latest roll of a user on rngdle.com", aliases=["rngdle"])
    @app_commands.describe(username="The username of the user on rngdle.com")
    async def rngdle_latest_roll(self, ctx: commands.Context, username: str):
        if not await handleCommandAccess(ctx, ctx.author.id, "rngdle"):
            return
        handle = await hybridDefer(ctx)
        setCooldown(ctx.author.id, "rngdle", 10)
        data = getRngdleLatestRoll(username)
        if data is None:
            await handle.edit(content=f"No rolls found for user '{username}'.")
        elif "api" in data:
            await handle.edit(content=f"Error fetching data for user '{username}': {data['api']} - {data.get('error', 'No error message')}")
        else:
            poem = data.get("poem", "[No poem]")
            timestampfixed = int(datetime.fromisoformat(data["rolledAt"].replace("Z", "+00:00")).astimezone().timestamp())
            await handle.edit(content=f"**{username}'s latest roll** (rolled at: <t:{timestampfixed}:F>)\nNumber: `{data['number']}`\nTotal Score: `{data['totalScore']}`\nBadge Count: `{data['badgeCount']}`\nHeart Count: `{data['heartCount']}`\nPoem: `{poem}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(rngdle(bot))