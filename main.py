import discord # type: ignore
from discord.ext import commands # type: ignore
from discord import app_commands # type: ignore
import os # type: shit
import json
import traceback
import random
import requests # type: ignore
import re

from common import developergithub, ensure_datastores, loadData, repositoryurl, saveData, formatUsername, getDisplay, truncateMessage, inviteurl, supportserver

intents = discord.Intents.default()
ensure_datastores()

def getLatestCommitHash():
    try:
        response = requests.get("https://api.github.com/repos/etangaming123/etanbot/commits/main")
        if response.status_code == 200:
            data = response.json()
            cachedcommithash = data['sha'][:7] # Cache the commit hash for future use
            return data['sha'][:7] # Return the first 7 characters of the commit hash
        else:
            print(f"Error fetching latest commit: Received status code {response.status_code}")
            return "unknown"
    except Exception as e:
        print(f"Error fetching latest commit: {e}")
        traceback.print_exc()
        return "unknown"

currentcommithash = getLatestCommitHash()

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

bot = etanBot(command_prefix='!', intents=intents)
bot.tree.allowed_installs = app_commands.AppInstallationType(guild=True, user=True)
bot.tree.allowed_contexts = app_commands.AppCommandContext(guild=True, dm_channel=True, private_channel=True)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Error syncing commands: {e}')

# general
@bot.tree.command(name="etanbot-ping", description="Ping the bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.defer()
    await interaction.edit_original_response(content=f"Pong! [{round(bot.latency * 1000)}ms]")

@bot.tree.command(name="etanbot-who-am-i", description="Information about the bot!")
async def whoami(interaction: discord.Interaction):
    await interaction.response.defer()
    embed = discord.Embed(title="etanbot info", description="funny discord bot", color=0x8649D7)
    embed.add_field(name="Description", value="Funny Discord bot that can be added to your account and used anywhere within Discord.\n [webpage](https://etanbot.etangaming.xyz/) • [terms of service](https://etanbot.etangaming.xyz/termsofservice.html) • [privacy policy](https://etanbot.etangaming.xyz/privacypolicy.html)", inline=False)
    embed.add_field(name="Features", value="Various commands - link cleaner, 8ball, coinflip, random number generator, built-in profiles, (unofficial) KOKO Amusement card linking, with more to come.")
    embed.add_field(name="Commit", value=currentcommithash, inline=False)
    embed.add_field(name="Developer", value=f"[etangaming123]({developergithub})", inline=False)
    embed.add_field(name="Repository", value=repositoryurl, inline=False)
    embed.set_footer(text=f"etan • etangaming123 • etangamingxyz")
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else "https://cdn.discordapp.com/embed/avatars/0.png")
    if bot.user.banner:
        embed.set_image(url=bot.user.banner.url)
    await interaction.edit_original_response(embed=embed)

@bot.tree.command(name="etanbot-invite", description="Get the invite link for the bot!")
async def invite(interaction: discord.Interaction):
    await interaction.response.defer()
    await interaction.edit_original_response(content=f"[Let's get started!]({inviteurl}) • [Support server]({supportserver})")

@bot.tree.command(name="etanbot-8ball", description="Ask the magic 8ball a question!") # use with caution. its completely random yet can be scarily accurate at times
@app_commands.describe(question="The question to ask the 8ball. (a yes or no question, and keep it short!)")
async def eight_ball(interaction: discord.Interaction, question: str):
    await interaction.response.defer()
    responses = [
        "It is certain.",
        "It is decidedly so.",
        "Without a doubt.",
        "Yes - definitely.",
        "You may rely on it.",
        "As I see it, yes.",
        "Most likely.",
        "Outlook good.",
        "Yes.",
        "Signs point to yes.",
        "Reply hazy, try again.",
        "Ask again later.",
        "Better not tell you now.",
        "Cannot predict now.",
        "Concentrate and ask again.",
        "Don't count on it.",
        "My reply is no.",
        "My sources say no.",
        "Outlook not so good.",
        "Very doubtful."
    ]
    await interaction.edit_original_response(content=f"You asked the 8ball \"{question}\"...\nThe 8ball says... {random.choice(responses)}")

@bot.tree.command(name="etanbot-braincells", description="Check how many braincells you (or someone else) has left. (highest is 1000)")
@app_commands.describe(user="The user to check braincells for (defaults to yourself).")
async def braincells(interaction: discord.Interaction, user: discord.User = None):
    await interaction.response.defer()
    if user is None:
        user = interaction.user
    braincellcount = random.randint(0, 1000)
    await interaction.edit_original_response(content=f"{formatUsername(user)} has {braincellcount} braincells.")

@bot.tree.command(name="etanbot-pizoelectric", description="[Thing] is turning [something else] into electricity!") # based off the infamous copypasta "Japan is turning footsteps into electricity! ⚡Using piezoelectric tiles, every step you take generates a small amount of energy. Millions of steps together can power LED lights and displays in busy places like Shibuya Station. A brilliant way to create a sustainable and smart city -- turning movement into clean, renewable energy 🌱💡"
@app_commands.describe(thing="Who is turning something into electricity?", somethingelse="What is being turned into electricity?")
async def pizoelectric(interaction: discord.Interaction, thing: str = None, somethingelse: str = None):
    await interaction.response.defer()
    if thing is None:
        thing = "Japan"
    if somethingelse is None:
        somethingelse = "footsteps"

    await interaction.edit_original_response(content=f"{thing} is turning {somethingelse} into electricity! ⚡Using piezoelectric tiles, every step you take generates a small amount of energy. Millions of steps together can power LED lights and displays in busy places like Shibuya Station. A brilliant way to create a sustainable and smart city -- turning movement into clean, renewable energy 🌱💡")

@bot.tree.command(name="etanbot-pp-size", description="*wink*")
@app_commands.describe(user="Whose pp size do you want to check? (defaults to yourself)")
async def pp_size(interaction: discord.Interaction, user: discord.User = None):
    await interaction.response.defer()
    if user is None:
        user = interaction.user
    if str(user.id) == config["poweruserid"]:
        size = random.randint(20, 30) # wink
    else:
        size = random.randint(0, 30)
    string = "8" + "=" * size + "D"
    await interaction.edit_original_response(content=f"{formatUsername(user)}: {string}")

@bot.tree.command(name="etanbot-puppet", description="Make the bot say something (as a response to the command, not in the channel).")
@app_commands.describe(say="The thing to say.")
async def puppet(interaction: discord.Interaction, say: str):
    await interaction.response.defer()
    await interaction.edit_original_response(content=say)

@bot.tree.command(name="etanbot-coinflip", description="Flip a coin!")
async def coinflip(interaction: discord.Interaction):
    await interaction.response.defer()
    result = random.choice(["Heads", "Tails"])
    await interaction.edit_original_response(content=f"{result}!")

def cleanLink(url, toremove):
    if toremove == "*": # if toremove is *, remove all parameters from the link
        if "?" not in url:
            return url.split("&")[0] # Tiktok is known to use & instead of ? for their parameters sometimes, so we check for both and split by the one that exists
        return url.split("?")[0]
    cleaned_link = url
    for item in toremove:
        cleaned_link = re.sub(r'([&?])' + re.escape(item) + r'=[^&]*', '', cleaned_link)
    cleaned_link = re.sub(r'[?&]+$', '', cleaned_link) # remove trailing ? or &
    for item in toremove:
        cleaned_link = re.sub(r'([&])' + re.escape(item) + r'=[^&]*', '', cleaned_link) # run again, this time removing & params
    return cleaned_link

@bot.tree.command(name="etanbot-clean-link", description="Remove stinky link trackers.")
@app_commands.describe(link="The link you want to clean.", additional="Any additional parameters to remove, separated by commas (optional).")
async def clean_link(interaction: discord.Interaction, link: str, additional: str = None):
    await interaction.response.defer()
    toremove = ["igsh", "si", "fbclid", "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "is", "mibextid", "gclid", "dclid", "is_from_webapp", "sender_device", "_t", "_r"] # common link trackers to remove
    if additional:
        toremove.extend(additional.split(","))
    cleaned_link = cleanLink(link, toremove)
    if "tiktok.com" in cleaned_link and "vt.tiktok.com" not in cleaned_link: # Fuck you tiktok, we're removing ALL your parameters
        cleaned_link = cleanLink(link, "*")
    if "vt.tiktok" in cleaned_link: # wow tiktok that's slack
        await interaction.edit_original_response(content=f"URL seems to have embedded trackers, just a sec...")
        try:
            response = requests.get(cleaned_link) # make a request to the link to get the final URL after tiktok's trackers redirect it
            if response.status_code != 200:
                await interaction.edit_original_response(content=f"Couldn't get real video link - status code {response.status_code}.")
            actuallink = response.url
            cleaned_link = cleanLink(actuallink, toremove)
            await interaction.edit_original_response(content=f"We are using a different method to remove trackers from this link, as this tiktok link has embedded trackers: {cleaned_link}")
            return
        except Exception:
            traceback.print_exc()
            await interaction.edit_original_response(content="Something went wrong whilst trying to remove trackers. (Check your URL!)")
            return
    await interaction.edit_original_response(content=f"Removed stinky link trackers: {cleaned_link}")

@bot.tree.command(name="etanbot-randomnumber", description="Generate a random number between a specified range.")
@app_commands.describe(minimum="The minimum number (inclusive).", maximum="The maximum number (inclusive).")
async def random_number(interaction: discord.Interaction, minimum: int, maximum: int):
    await interaction.response.defer()
    if minimum > maximum:
        minimum, maximum = maximum, minimum
    number = random.randint(minimum, maximum)
    await interaction.edit_original_response(content=f"Your random number between {minimum} and {maximum} is: {number}")

@bot.tree.command(name="etanbot-birthday", description="Whose birthday is it?")
async def birthday(interaction: discord.Interaction, user: discord.User = None):
    await interaction.response.defer()
    bdaystrings = [
        "Happy birthday, USER!",
        "Birthday happy, USER!",
        "Happy birthday to USER!",
        "Birthday wishes to USER!",
        "Cake and candles to USER!",
        "Let's celebrate USER's birthday!"
    ]

    if user is None:
        user = interaction.user
    if user == interaction.user:
        await interaction.edit_original_response(content="Happy birthday to you!!!")
        return
    if user == bot.user:
        await interaction.edit_original_response(content="thanks but i don't think it's my birthday...")
        return
    await interaction.edit_original_response(content=random.choice(bdaystrings).replace("USER", user.mention))

@bot.tree.command(name="etanbot-shexonmyytilliz", description="she [x] on my [y] till i [z]")
@app_commands.describe(x="she does what", y="on your what", z="until you what")
async def shexonmyytilliz(interaction: discord.Interaction, x: str, y: str, z: str):
    await interaction.response.defer()
    await interaction.edit_original_response(content=f"she {x} on my {y} till i {z}")

@bot.tree.command(name="etanbot-predict", description="[event] will happen [unspecified date/time]")
@app_commands.describe(event="The event you want to predict.")
async def predict(interaction: discord.Interaction, event: str):
    await interaction.response.defer()
    times = [
        "right now",
        "in a few seconds",
        "in a few minutes",
        "in a few hours",
        "tomorrow",
        "in a few days",
        "next week",
        "in a few weeks",
        "next month",
        "in a few months",
        "next year",
        "in a few years",
        "never"
    ]
    await interaction.edit_original_response(content=f"{event} will happen {random.choice(times)}!")

@bot.tree.command(name="etanbot-10d20", description="Makes a link to use Discord's built in dice roller with 10d20 (10 20-sided dice).")
async def d20(interaction: discord.Interaction):
    await interaction.response.defer()
    if interaction.guild_id is None or interaction.channel_id is None:
        await interaction.edit_original_response(content="This command can only be used in a server channel. (The built in roll-dice feature only works in a channel!)")
        return
    await interaction.edit_original_response(content=f"https://discord.com/channels/{interaction.guild_id}/{interaction.channel_id}/roll-dice/10d20")

@bot.tree.command(name="etanbot-lie-detector", description="Check if someone is lying!")
@app_commands.describe(user="The user who you think is lying. (Leave blank for yourself!)")
async def liedetector(interaction: discord.Interaction, user: discord.User = None):
    if user == None:
        user = interaction.user
    await interaction.response.defer()
    liestrings = [
        "USER is LYING!!!",
        "Nah, USER isn't telling the truth.",
        "❌ Nope, USER!",
        "I wouldn't trust USER if I were you..."
    ]
    truthstrings = [
        "✅ True, USER!",
        "Confirmed, USER is telling the truth.",
        "Yeah, I'd say USER is being truthful here.",
        "Trust USER!"
    ]

    if random.randint(0, 1) == 0:
        await interaction.edit_original_response(content=random.choice(liestrings).replace("USER", formatUsername(user)))
    else:
        await interaction.edit_original_response(content=random.choice(truthstrings).replace("USER", formatUsername(user)))

def readTonetags():
    with open("tonetags.txt", "r") as f:
        tonetags = {}
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "\t" in line:
                key, value = line.split("\t", 1)
            elif " " in line:
                key, value = line.split(None, 1)
            else:
                continue
            tonetags[key.strip().lstrip("/")] = value.strip()
        return tonetags

@bot.tree.command(name="etanbot-tonetag", description="Get information for a tonetag! Most definitions from https://tonetaglist.carrd.co/.")
@app_commands.describe(tonetag="The tonetag you wish to view information for. (remove /)")
async def tonetag(interaction: discord.Interaction, tonetag: str):
    await interaction.response.defer()
    tonetags = readTonetags()
    if tonetag in tonetags:
        await interaction.edit_original_response(content=f"`{tonetag}` >> {tonetags[tonetag]}")
    else:
        await interaction.edit_original_response(content=f"Couldn't find anything for `{tonetag}`.")

@tonetag.autocomplete("tonetag")
async def tonetag_autocomplete(interaction: discord.Interaction, current: str):
    tonetags = readTonetags()
    thingtoreturn = [app_commands.Choice(name=key, value=key)
        for key in tonetags.keys()
        if current.lower() in key.lower()
    ][:25]
    if thingtoreturn:
        return thingtoreturn
    else:
        return [app_commands.Choice(name="No matching tonetags found", value="")]

@bot.tree.command(name="etanbot-mbti", description="Lookup an mbti type/acronym! (ENTP, INTP, INTJ, ISFJ, etc.)")
@app_commands.describe(mbti="The mbti type you want to look up (ENTP, INTP, INTJ, ISFJ, etc.)")
async def mbti(interaction: discord.Interaction, mbti: str):
    await interaction.response.defer()
    mbti = mbti.upper()
    if len(mbti) != 4 or any(letter not in "EI" for letter in mbti[0]) or any(letter not in "NS" for letter in mbti[1]) or any(letter not in "FT" for letter in mbti[2]) or any(letter not in "JP" for letter in mbti[3]):
        await interaction.edit_original_response(content="That doesn't look like a valid MBTI type. Please enter a valid type like ENTP, INTP, INTJ, ISFJ, etc.")
        return
    stringo = f"{mbti} means:\n"
    if mbti[0] == "I":
        stringo = stringo + "`I` >> **I**ntrovert\n"
    else:
        stringo = stringo + "`E` >> **E**xtrovert\n"
    
    if mbti[1] == "S":
        stringo = stringo + "`S` >> **S**ensing\n"
    else:
        stringo = stringo + "`N` >> I**n**tuition\n"

    if mbti[2] == "F":
        stringo = stringo + "`F` >> **F**eeling\n"
    else:
        stringo = stringo + "`T` >> **T**hinking\n"

    if mbti[3] == "P":
        stringo = stringo + "`P` >> **P**erception\n"
    else:
        stringo = stringo + "`J` >> **J**udgement\n"
    await interaction.edit_original_response(content=stringo)

@bot.tree.command(name="etanbot-status", description="Are we running the latest commit?")
async def status(interaction: discord.Interaction):
    await interaction.response.defer()
    latesthash = getLatestCommitHash()
    if latesthash == currentcommithash:
        await interaction.edit_original_response(content=f"etanbot is up to date! Running commit: {currentcommithash}")
    else:
        await interaction.edit_original_response(content=f"etanbot is not up to date. Running commit: {currentcommithash}, latest commit: {latesthash}. Please contact the developer to update the bot!")

bot.run(config['token'])