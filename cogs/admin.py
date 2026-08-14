import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone
import re

from common import getBannedUsers, loadData, saveData, config, formatUsername, handleCommandAccess, getUserHash, purgeUserData, ConfirmView, hybridReply, hybridDefer, requireDMOnly, HybridHandle

class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _parse_duration_to_timestamp(self, length: str):
        if not length:
            return None

        if length.lower() == "permanent":
            return None  # Representing permanent ban as None

        if length.lower() == "ncmd":
            return "ncmd" # next command

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

    @commands.hybrid_command(name="z-admin-ban-user", description="Ban a user from using the bot. (Admin only)", aliases=["adminban"])
    @app_commands.describe(user="The user to ban", length="The length of the ban (e.g 2d1h30m2s) (or set to a huge number for 'permanent')", reason="The reason for banning the user (will be shown)")
    async def ban_user(self, ctx: commands.Context, user: discord.User, length: str, reason: str = None):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        if not await requireDMOnly(ctx):
            return
        if ctx.author.id != int(config["poweruserid"]):
            await hybridReply(ctx, content="You don't have permission to use this command.", ephemeral=True)
            return

        handle = await hybridDefer(ctx, ephemeral=True)
        if user == ctx.author:
            await handle.edit(content="You cannot ban yourself.")
            return
        bannedusers = loadData("bannedusers")
        ban_key = getUserHash(user.id)
        if ban_key in bannedusers:
            del bannedusers[ban_key]
        bannedusers[getUserHash(user.id)] = {"length": self._parse_duration_to_timestamp(length), "reason": reason}
        if saveData("bannedusers", bannedusers):
            getBannedUsers(refresh=True)  # Refresh the banned users list after saving
            await handle.edit(content=f"User {formatUsername(user)} has been banned from using etan bot.")
        else:
            await handle.edit(content=f"An error occurred while banning the user.")

    @commands.hybrid_command(name="z-admin-unban-user", description="Unban a user from using the bot. (Admin only)", aliases=["adminunban"])
    @app_commands.describe(user="The user to unban")
    async def unban_user(self, ctx: commands.Context, user: discord.User):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        if not await requireDMOnly(ctx):
            return
        if ctx.author.id != int(config["poweruserid"]):
            await hybridReply(ctx, content="You don't have permission to use this command.", ephemeral=True)
            return

        handle = await hybridDefer(ctx, ephemeral=True)

        bannedusers = loadData("bannedusers")
        if getUserHash(user.id) in bannedusers:
            del bannedusers[getUserHash(user.id)]
        else:
            await handle.edit(content=f"User {formatUsername(user)} is not banned.")
            return

        if saveData("bannedusers", bannedusers):
            getBannedUsers(refresh=True)  # Refresh the banned users list after saving
            await handle.edit(content=f"User {formatUsername(user)} has been unbanned from using etan bot.")
        else:
            await handle.edit(content=f"An error occurred while unbanning the user.")

    @commands.hybrid_command(name="z-admin-purge-user", description="Deletes all data for a specific user. (Admin only)", aliases=["adminpurge"])
    @app_commands.describe(user="The user whose data will be deleted")
    async def purge_user(self, ctx: commands.Context, user: discord.User):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        if not await requireDMOnly(ctx):
            return
        if ctx.author.id != int(config["poweruserid"]):
            await hybridReply(ctx, content="You don't have permission to use this command.", ephemeral=True)
            return

        view = ConfirmView(ctx.author.id)
        handle = HybridHandle(ctx)
        await handle.edit(content=f"Are you sure you want to delete **all** data for {formatUsername(user)}? This cannot be undone.", view=view, ephemeral=True)
        await view.wait()

        if view.value is not True:
            await handle.edit(content="Purge cancelled." if view.value is False else "Confirmation timed out, purge cancelled.", view=None)
            return

        if purgeUserData(user.id):
            await handle.edit(content=f"All data for {formatUsername(user)} has been deleted.", view=None)
        else:
            await handle.edit(content="An error occurred while deleting the user's data.", view=None)

async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))