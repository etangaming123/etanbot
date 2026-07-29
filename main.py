import discord
from discord.ext import commands 
from discord import app_commands
import os 
import json
import random
import requests
import re
from git import Repo
repo = Repo(os.curdir)

from common import developergithub, ensure_datastores, repositoryurl, inviteurl, supportserver, website, setCooldown, config, handleCommandAccess, readTextFile

intents = discord.Intents.default()
ensure_datastores()

def getLatestCommitHash():
    try:
        response = requests.get("https://api.github.com/repos/etangaming123/etanbot/commits/main")
        if response.status_code == 200:
            data = response.json()
            return data['sha'][:7] # Return the first 7 characters of the commit hash
        else:
            print(f"Error fetching latest commit: Received status code {response.status_code}")
            return "unknown"
    except Exception as e:
        print(f"Error fetching latest commit: {e}")
        return "unknown"

tonetags = readTextFile("tonetags")
deretypes = readTextFile("deretypes")
currentcommithash = repo.head.object.hexsha[:7]

if not os.path.exists("config.json"):
    with open("config.json", "w") as f:
        json.dump({"token": "your token here", "poweruserid": "your user id here (for certain commands)"}, f, indent=4)
    input("Created config.json with default values. Please edit the file with your bot token and user id, then press enter to continue...")

with open('config.json') as f:
    config = json.load(f)

class etanBot(commands.Bot):
    async def setup_hook(self):
        await self.load_extension("cogs.kokolinking")
        await self.load_extension("cogs.profiles")
        await self.load_extension("cogs.nsotaskmanager")
        await self.load_extension("cogs.gifs")
        await self.load_extension("cogs.math")
        await self.load_extension("cogs.slotmachine")
        await self.load_extension("cogs.rngdle")
        await self.load_extension("cogs.admin")
        await self.load_extension("cogs.color")
        await self.load_extension("cogs.linkcleaner")
        await self.load_extension("cogs.rng")
        await self.load_extension("cogs.message")
        await self.load_extension("cogs.misc")
        await self.load_extension("cogs.timezones")

bot = etanBot(command_prefix='!', intents=intents)
bot.tree.allowed_installs = app_commands.AppInstallationType(guild=True, user=True)
bot.tree.allowed_contexts = app_commands.AppCommandContext(guild=True, dm_channel=True, private_channel=True)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="etanbot.etangaming.xyz | /etanbot-who-am-i"))
        print("Changed presence")
    except Exception as e:
        print(f'Error syncing commands: {e}')

# general
@bot.tree.command(name="etanbot-ping", description="Ping the bot")
async def ping(interaction: discord.Interaction):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    await interaction.response.defer()
    await interaction.edit_original_response(content=f"Pong! [{round(bot.latency * 1000)}ms]")

@bot.tree.command(name="etanbot-who-am-i", description="Information about the bot!")
async def whoami(interaction: discord.Interaction):
    if not await handleCommandAccess(interaction, interaction.user.id, "whoami"):
        return
    await interaction.response.defer()
    setCooldown(interaction.user.id, "whoami", 10)
    embed = discord.Embed(title="etanbot info", description="funny discord bot", color=0x8649D7)
    embed.add_field(name="Description", value=f"Funny Discord bot that can be added to your account and used anywhere within Discord.", inline=False)
    embed.add_field(name="Features", value="Various commands - link cleaner, MBTI personality type lookup, tonetag lookup, NEEDY STREAMER OVERLOAD Task Manager Generator, with more to come.", inline=False)
    embed.add_field(name="Links", value=f"[webpage]({website}) • [terms of service]({website}/termsofservice.html) • [privacy policy]({website}/privacypolicy.html) • [add to discord]({inviteurl}) • [support server]({supportserver})", inline=False)
    embed.add_field(name="Commit", value=currentcommithash, inline=True)
    embed.add_field(name="Developer", value=f"[etangaming123]({developergithub})", inline=True)
    embed.add_field(name="Repository", value=repositoryurl, inline=False)
    embed.set_footer(text=f"etan • etangaming123 • etangamingxyz")
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else "https://cdn.discordapp.com/embed/avatars/0.png")
    if bot.user.banner:
        embed.set_image(url=bot.user.banner.url)
    await interaction.edit_original_response(embed=embed)

@bot.tree.command(name="etanbot-invite", description="Get the invite link for the bot!")
async def invite(interaction: discord.Interaction):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    await interaction.response.defer()
    await interaction.edit_original_response(content=f"[Let's get started!]({inviteurl}) • [Support server]({supportserver})")

@bot.tree.command(name="etanbot-status", description="Are we running the latest commit?")
async def status(interaction: discord.Interaction):
    if not await handleCommandAccess(interaction, interaction.user.id, "status"):
        return
    await interaction.response.defer()
    setCooldown(interaction.user.id, "status", 10)
    if repo.is_dirty():
        await interaction.edit_original_response(content="etanbot is running on a modified commit!")
        return
    latesthash = getLatestCommitHash()
    if latesthash == currentcommithash:
        await interaction.edit_original_response(content=f"etanbot is up to date! Running commit: {currentcommithash}")
    elif latesthash == "unknown":
        await interaction.edit_original_response(content=f"etanbot is running commit: {currentcommithash}, we couldn't get the latest commit")
    else:
        await interaction.edit_original_response(content=f"etanbot is not up to date. Running commit: {currentcommithash}, latest commit: {latesthash}. Please contact the developer to update the bot!")

bot.run(config['token'])