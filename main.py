print("Loading modules...")
import discord
from discord.ext import commands, tasks
from discord import app_commands
import os 
import json
import requests
import random
from git import Repo
repo = Repo(os.curdir)
import secure_token

from common import developergithub, ensure_datastores, repositoryurl, inviteurl, supportserver, website, setCooldown, config, handleCommandAccess, readTextFile, statuses, checkforupdates

intents = discord.Intents.default()
ensure_datastores()

def getCurrentBranch():
    try:
        return repo.active_branch.name
    except TypeError:
        return "detached HEAD"

def getLatestCommitHash(branch=None):
    branch = branch or getCurrentBranch()
    try:
        response = requests.get(f"https://api.github.com/repos/etangaming123/etanbot/commits/{branch}")
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
currentbranch = getCurrentBranch()

if not os.path.exists("config.json"):
    with open("config.json", "w") as f:
        json.dump({"token": "your token here", "poweruserid": "your user id here (for certain commands)"}, f, indent=4)
    input("Created config.json with default values. Please edit the file with your bot token and user id, then press enter to continue...")

cogs = ["kokolinking", "profiles", "nsotaskmanager", "gifs", "math", "slotmachine", "rngdle", "admin", "color", "linkcleaner", "rng", "message", "misc", "timezones", "datamanagement", "gimmicks", "usersettings"]

print("Loading additional commands...")
class etanBot(commands.Bot):
    async def setup_hook(self):
        for item in cogs:
            try:
                await self.load_extension(f"cogs.{item}")
                print(f"Loaded cog {item}")
            except Exception as e:
                print(f"Failed to load cog {item}: {e}")

bot = etanBot(command_prefix='!', intents=intents)
bot.tree.allowed_installs = app_commands.AppInstallationType(guild=True, user=True)
bot.tree.allowed_contexts = app_commands.AppCommandContext(guild=True, dm_channel=True, private_channel=True)

async def updateStatus(newstatus):
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=newstatus))

pickedstatus = None
OhNoesWereOutOfDateButItsOkayBecauseWePrintedTheWarningAlready = False # i love weird variable names <3

@tasks.loop(minutes=10)
async def DoThisEveryTenMinutes():
    global pickedstatus
    global OhNoesWereOutOfDateButItsOkayBecauseWePrintedTheWarningAlready

    if checkforupdates:
        latesthash = getLatestCommitHash()
        if latesthash != currentcommithash and not OhNoesWereOutOfDateButItsOkayBecauseWePrintedTheWarningAlready:
            branchnote = f" [tracking branch: {currentbranch}, not main]" if currentbranch != "main" else ""
            print(f"etan bot has updated!{branchnote} Current commit: {currentcommithash}, latest commit: {latesthash}. You should git pull and restart the bot if not running a modded instance!")
            OhNoesWereOutOfDateButItsOkayBecauseWePrintedTheWarningAlready = True

    pickedstatus = random.choice(statuses)
    if pickedstatus == "special1":
        await updateStatus(f"Currently running {currentcommithash}")
    elif pickedstatus == "special2":
        await updateStatus(f"Installed in {len(bot.guilds)} servers!")
    else:
        await updateStatus(pickedstatus)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    try:
        print("Syncing commands...")
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Error syncing commands: {e}')
    DoThisEveryTenMinutes.start()
    print("Bot is up and running!")

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
    embed.add_field(name="Commit", value=f"{currentcommithash} ({currentbranch})" if currentbranch != "main" else currentcommithash, inline=True)
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
    await interaction.edit_original_response(content=f"[Add etan bot to your account]({inviteurl}), or [join the support server for updates and help]({supportserver})")

@bot.tree.command(name="etanbot-status", description="Are we running the latest commit?")
async def status(interaction: discord.Interaction):
    if not await handleCommandAccess(interaction, interaction.user.id, "status"):
        return
    await interaction.response.defer()
    setCooldown(interaction.user.id, "status", 10)

    branchnote = ""
    if currentbranch != "main":
        branchnote = f" (running on branch **{currentbranch}**, not main)"

    if repo.is_dirty():
        dirtyfiles = [item.a_path for item in repo.index.diff(None)] + repo.untracked_files
        filelist = ", ".join(dirtyfiles[:10]) + ("..." if len(dirtyfiles) > 10 else "")
        await interaction.edit_original_response(content=f"etanbot is running on a modified commit!{branchnote} Running commit: {currentcommithash}. Uncommitted changes: {filelist}")
        return

    latesthash = getLatestCommitHash(currentbranch)
    if latesthash == currentcommithash:
        await interaction.edit_original_response(content=f"etanbot is up to date!{branchnote} Running commit: {currentcommithash}")
    elif latesthash == "unknown":
        await interaction.edit_original_response(content=f"etanbot is running commit: {currentcommithash}{branchnote}, we couldn't get the latest commit")
    else:
        await interaction.edit_original_response(content=f"etanbot is not up to date.{branchnote} Running commit: {currentcommithash}, latest commit: {latesthash}. Please contact the developer to update the bot!")

bot.run(secure_token.secure_token())