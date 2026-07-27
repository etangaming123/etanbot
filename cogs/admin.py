import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone
import re

from common import loadData, saveData, checkIfCooldown, setCooldown, checkIfBanned, config, formatUsername, handleCommandAccess, getBanKey

class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _parse_duration_to_timestamp(self, length: str):
        if not length:
            return None

        matches = re.findall(r"(\d+)([dhms])", length.lower())
        if not matches:
            return None

        total = timedelta()
        for value, unit in matches:
            value = int(value)
            if unit == "d":
                total += timedelta(days=value)
            elif unit == "h":
                total += timedelta(hours=value)
            elif unit == "m":
                total += timedelta(minutes=value)
            elif unit == "s":
                total += timedelta(seconds=value)

        return int((datetime.now(timezone.utc) + total).timestamp())

    @app_commands.command(name="z-admin-ban-user", description="Ban a user from using the bot. (Admin only)")
    @app_commands.describe(user="The user to ban", length="The length of the ban (e.g 2d1h30m2s) (or set to a huge number for 'permanent')", reason="The reason for banning the user (will be shown)")
    async def ban_user(self, interaction: discord.Interaction, user: discord.User, length: str, reason: str = None):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        if interaction.user.id != int(config["poweruserid"]):
            await interaction.response.send_message(content="You don't have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        if user == interaction.user:
            await interaction.edit_original_response(content="You cannot ban yourself.")
            return
        bannedusers = loadData("bannedusers")
        for ban_key in [getBanKey(user.id), str(hash(user.id)), str(hash(str(user.id)))]:
            if ban_key in bannedusers:
                del bannedusers[ban_key]
        bannedusers[getBanKey(user.id)] = {"length": self._parse_duration_to_timestamp(length), "reason": reason}
        if saveData("bannedusers", bannedusers):
            await interaction.edit_original_response(content=f"User {formatUsername(user)} has been banned from using etan bot.")
        else:
            await interaction.edit_original_response(content=f"An error occurred while banning the user.")

    @app_commands.command(name="z-admin-unban-user", description="Unban a user from using the bot. (Admin only)")
    @app_commands.describe(user="The user to unban")
    async def unban_user(self, interaction: discord.Interaction, user: discord.User):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        if interaction.user.id != int(config["poweruserid"]):
            await interaction.response.send_message(content="You don't have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        bannedusers = loadData("bannedusers")
        if getBanKey(user.id) in bannedusers:
            del bannedusers[getBanKey(user.id)]
        elif str(hash(user.id)) in bannedusers:
            del bannedusers[str(hash(user.id))]
        elif str(hash(str(user.id))) in bannedusers:
            del bannedusers[str(hash(str(user.id)))]
        else:
            await interaction.edit_original_response(content=f"User {formatUsername(user)} is not banned.")
            return

        if saveData("bannedusers", bannedusers):
            await interaction.edit_original_response(content=f"User {formatUsername(user)} has been unbanned from using etan bot.")
        else:
            await interaction.edit_original_response(content=f"An error occurred while unbanning the user.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))