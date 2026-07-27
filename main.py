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

from common import developergithub, ensure_datastores, repositoryurl, formatUsername, truncateMessage, inviteurl, supportserver, website, setCooldown, getDisplay, config, handleCommandAccess

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

def readTextFile(textfile: str):
    with open(f"{textfile}.txt", "r") as f:
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

@bot.tree.command(name="etanbot-8ball", description="Ask the magic 8ball a question!") # use with caution. its completely random yet can be scarily accurate at times
@app_commands.describe(question="The question to ask the 8ball. (a yes or no question, and keep it short!)", flavour="The flavour of the 8ball. (optional, defaults to classic)")
@app_commands.choices(flavour=[
    discord.app_commands.Choice(name="classic", value="classic"),
    discord.app_commands.Choice(name="casual", value="casual"),
    discord.app_commands.Choice(name="tsundere", value="tsundere"),
])
async def eight_ball(interaction: discord.Interaction, question: str, flavour: discord.app_commands.Choice[str] = None):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    await interaction.response.defer()
    responses_classic = [
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
    responses_tsundere = [
        "Ask again... but not b-because I told y-you to, baka!",
        "Y-yes... Don't get any w-weird ideas, baka!",
        "Whaaat?! N-no!",
        "I can't p-predict that... not like I-I wanted to!",
        "I'm gonna say y-yes... but not b-because of y-you or anything!",
        "N-no! But it's not like I w-wanted to say yes!",
        "I don't know! D-don't get any weird ideas, b-baka!",
        "No! Hmph!",
        "Yes! Hmph!",
        "Maybe! Hmph!"
    ]
    responses_casual = [
        "yea",
        "nah",
        "prolly not",
        "prolly should",
        "why not",
        "hell nah",
        "idk",
        "didn't catch that, ask again",
        "can't tell ya",
    ]

    # this is probably the worst way to do this but i cba finding a better one
    if flavour == None: # attempt 4 of fixing this stupid ass bug holy shit
        responses = responses_classic
    elif flavour.value == "classic":
        responses = responses_classic
    elif flavour.value == "tsundere":
        responses = responses_tsundere
    elif flavour.value == "casual":
        responses = responses_casual

    if flavour == None:
        await interaction.edit_original_response(content=f"You asked the classic 8ball \"{question}\"...\nThe 8ball says... {random.choice(responses)}")
        return  
    await interaction.edit_original_response(content=f"You asked the {flavour.value} 8ball \"{question}\"...\nThe 8ball says... {random.choice(responses)}")

@bot.tree.command(name="etanbot-braincells", description="Check how many braincells you (or someone else) has left. (highest is 1000)")
@app_commands.describe(user="The user to check braincells for (defaults to yourself).")
async def braincells(interaction: discord.Interaction, user: discord.User = None):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    await interaction.response.defer()
    if user is None:
        user = interaction.user
    braincellcount = random.randint(0, 1000)
    await interaction.edit_original_response(content=f"{formatUsername(user)} has {braincellcount} braincells.")

@bot.tree.command(name="etanbot-pizoelectric", description="[Thing] is turning [something else] into electricity!") # based off the infamous copypasta "Japan is turning footsteps into electricity! ⚡Using piezoelectric tiles, every step you take generates a small amount of energy. Millions of steps together can power LED lights and displays in busy places like Shibuya Station. A brilliant way to create a sustainable and smart city -- turning movement into clean, renewable energy 🌱💡"
@app_commands.describe(thing="Who is turning something into electricity?", somethingelse="What is being turned into electricity?")
async def pizoelectric(interaction: discord.Interaction, thing: str = None, somethingelse: str = None):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    await interaction.response.defer()
    if thing is None:
        thing = "Japan"
    if somethingelse is None:
        somethingelse = "footsteps"

    await interaction.edit_original_response(content=f"{thing} is turning {somethingelse} into electricity! ⚡Using piezoelectric tiles, every step you take generates a small amount of energy. Millions of steps together can power LED lights and displays in busy places like Shibuya Station. A brilliant way to create a sustainable and smart city -- turning movement into clean, renewable energy 🌱💡")

@bot.tree.command(name="etanbot-puppet", description="Make the bot say something (as a response to the command, not in the channel).")
@app_commands.describe(say="The thing to say.")
async def puppet(interaction: discord.Interaction, say: str):
    if not await handleCommandAccess(interaction, interaction.user.id, "puppet"):
        return
    await interaction.response.defer()
    setCooldown(interaction.user.id, "puppet", 5)
    if interaction.user.id != int(config["poweruserid"]):
        say = f"-# triggered by {interaction.user.mention}\n{say}"
    realthing = truncateMessage(say, 2000)
    await interaction.edit_original_response(content=realthing)
    setCooldown(interaction.user.id, "puppet", 10)

@bot.tree.command(name="etanbot-puppet-v2", description="Make the bot say something, but better (kinda)")
@app_commands.describe(say="<nl> gets replaced with a new line")
async def puppetv2(interaction: discord.Interaction, say: str):
    if not await handleCommandAccess(interaction, interaction.user.id, "puppet"):
        return
    await interaction.response.defer()
    setCooldown(interaction.user.id, "puppet", 5)
    if interaction.user.id != int(config["poweruserid"]):
        say = f"-# triggered by {interaction.user.mention}\n{say}"
    say = say.replace("<nl>", "\n")
    realthing = truncateMessage(say, 2000)
    await interaction.edit_original_response(content=realthing)
    setCooldown(interaction.user.id, "puppet", 10)

@bot.tree.command(name="etanbot-puppet-v3", description="Make the bot say something, but even better!")
async def puppetv3(interaction: discord.Interaction):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    class puppetForm(discord.ui.Modal, title="Make the bot say something!"):
        say = discord.ui.TextInput(label="What should the bot say?", style=discord.TextStyle.paragraph, placeholder="Enter your message here. Max 2000 characters.", required=True, max_length=2000)

        async def on_submit(self, interaction: discord.Interaction):
            if interaction.user.id != int(config["poweruserid"]):
                say = f"-# triggered by {interaction.user.mention}\n{say}"
            say = truncateMessage(self.say.value, 2000)
            await interaction.response.send_message(f"{self.say.value}", ephemeral=False)
        
    await interaction.response.send_modal(puppetForm())

@bot.tree.command(name="etanbot-coinflip", description="Flip a coin!")
@app_commands.describe(choice="The option you're looking for (cosmetic)")
@app_commands.choices(choice=[
    discord.app_commands.Choice(name="Heads", value="heads"),
    discord.app_commands.Choice(name="Tails", value="tails")
])
async def coinflip(interaction: discord.Interaction, choice: discord.app_commands.Choice[str] = None):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    await interaction.response.defer()
    result = random.choice(["Heads", "Tails"])
    if choice == None:
        await interaction.edit_original_response(content=f"The coin landed on **{result}**!")
    else:
        if choice.value == result:
            await interaction.edit_original_response(content=f"You hoped for *{choice.value}*, and the coin landed on **{result}**!")
        else:
            await interaction.edit_original_response(content=f"You hoped for *{choice.value}*, but the coin landed on **{result}**!")

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
@app_commands.describe(link="The link you want to clean [Valid url with http:// or https://]", additional="Any additional parameters to remove, separated by commas (optional).")
async def clean_link(interaction: discord.Interaction, link: str, additional: str = None):
    if not await handleCommandAccess(interaction, interaction.user.id, "cleanlink"):
        return
    await interaction.response.defer()
    if not (link.startswith("http://") or link.startswith("https://")):
        await interaction.edit_original_response(content="Please enter a valid URL that starts with http:// or https://")
        return
    if len(link) > 2000:
        await interaction.edit_original_response(content="There's no way that's a real link. [Please enter a valid URL under 2000 characters.]")
        return
    toremove = ["igsh", "si", "fbclid", "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "is", "mibextid", "gclid", "dclid", "is_from_webapp", "sender_device", "_t", "_r", "t"] # common link trackers to remove
    if additional:
        toremove.extend(additional.split(","))
    cleaned_link = cleanLink(link, toremove)

    if "tiktok.com" in cleaned_link and "vt.tiktok.com" not in cleaned_link: # Fuck you tiktok, we're removing ALL your parameters
        cleaned_link = cleanLink(link, "*")
    
    if "https://vt.tiktok" in cleaned_link[:17]: # wow tiktok that's slack
        await interaction.edit_original_response(content=f"vt.tiktok links redirect you to a URL with trackers! Please wait as we get the real URL and clean that...")
        try:
            response = requests.get(cleaned_link) # make a request to the link to get the final URL after tiktok's trackers redirect it
            if response.status_code != 200:
                await interaction.edit_original_response(content=f"Couldn't get real video link - status code {response.status_code}.")
            actuallink = response.url
            cleaned_link = cleanLink(actuallink, "*")
            await interaction.edit_original_response(content=f"We are using a different method to remove trackers from this link, as this tiktok link has embedded trackers: {cleaned_link}")
            return
        except Exception as e:
            print(f"Error cleaning link: {e}")
            await interaction.edit_original_response(content="Something went wrong whilst trying to remove trackers. (Check your URL!)")
            return
    await interaction.edit_original_response(content=f"Removed stinky link trackers: {cleaned_link}")

def cleanLinkV2(url, whitelist):
    if whitelist is None or len(whitelist) == 0:
        if "?" not in url:
            return url.split("&")[0]  # If no parameters, just return the base URL (Tiktok is known to use & instead of ? for their parameters sometimes, so we check for both and split by the one that exists)
        return url.split("?")[0]  # If no whitelist is provided, remove all parameters
    if "?" not in url:
        return url
    base_url, query_string = url.split("?", 1)
    params = query_string.split("&")
    cleaned_params = []
    for param in params:
        key = param.split("=")[0]
        if key in whitelist:
            cleaned_params.append(param)
    if cleaned_params:
        return f"{base_url}?{'&'.join(cleaned_params)}"
    else:
        return base_url

@bot.tree.command(name="etanbot-clean-link-v2", description="Remove even more link trackers. May break some links.")
@app_commands.describe(link="The link you want to clean [Valid url with http:// or https://]", whitelist="Any parameters you want to keep, separated by commas (optional). (overrides default whitelist)")
async def clean_link_v2(interaction: discord.Interaction, link: str, whitelist: str = None):
    if not await handleCommandAccess(interaction, interaction.user.id, "cleanlink"):
        return
    await interaction.response.defer()
    setCooldown(interaction.user.id, "cleanlink", 5)
    if not (link.startswith("http://") or link.startswith("https://")):
        await interaction.edit_original_response(content="Please enter a valid URL that starts with http:// or https://")
        return
    if len(link) > 2000:
        await interaction.edit_original_response(content="There's no way that's a real link. [Please enter a valid URL under 2000 characters.]")
        return
    defaultwhitelist = []
    whitelist_list = whitelist.split(",") if whitelist else defaultwhitelist
    if "steamcommunity.com" in link:
        whitelist_list.append("id") # id for sharedfiles
    if "youtube.com" in link or "youtu.be" in link:
        whitelist_list.append("v") # video id
        whitelist_list.append("t") # timestamp
        whitelist_list.append("list") # playlist

    cleaned_link = cleanLinkV2(link, whitelist_list)

    if "https://vt.tiktok" in cleaned_link[:17]: # wow tiktok that's slack
        await interaction.edit_original_response(content=f"vt.tiktok links redirect you to a URL with trackers! Please wait as we get the real URL and clean that...")
        try:
            response = requests.get(cleaned_link) # make a request to the link to get the final URL after tiktok's trackers redirect it
            if response.status_code != 200:
                await interaction.edit_original_response(content=f"Couldn't get real video link - status code {response.status_code}.")
            actuallink = response.url
            cleaned_link = cleanLink(actuallink, "*")
            await interaction.edit_original_response(content=f"We are using a different method to remove trackers from this link, as this tiktok link has embedded trackers: {cleaned_link}")
            return
        except Exception as e:
            print(f"Error cleaning link: {e}")
            await interaction.edit_original_response(content="Something went wrong whilst trying to remove trackers. (Check your URL!)")
            return

    await interaction.edit_original_response(content=f"Removed a BUNCH of query parameters: {cleaned_link}")

@bot.tree.command(name="etanbot-randomnumber", description="Generate a random number between a specified range.")
@app_commands.describe(minimum="The minimum number (inclusive).", maximum="The maximum number (inclusive).")
async def random_number(interaction: discord.Interaction, minimum: int, maximum: int):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    await interaction.response.defer()
    if minimum > maximum:
        minimum, maximum = maximum, minimum
    number = random.randint(minimum, maximum)
    await interaction.edit_original_response(content=f"Your random number between {minimum} and {maximum} is: {number}")

@bot.tree.command(name="etanbot-birthday", description="Whose birthday is it?")
@app_commands.describe(user="The user whose birthday it is (defaults to yourself).")
async def birthday(interaction: discord.Interaction, user: discord.User = None):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
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
@app_commands.describe(x="she does what [100 chars]", y="on your what [100 chars]", z="until you what [100 chars]")
async def shexonmyytilliz(interaction: discord.Interaction, x: str, y: str, z: str):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    if len(x) > 100 or len(y) > 100 or len(z) > 100:
        await interaction.response.defer()
        await interaction.edit_original_response(content="Please keep each input under 100 characters.")
        return
    await interaction.response.defer()
    await interaction.edit_original_response(content=f"she {x} on my {y} till i {z}")

@bot.tree.command(name="etanbot-predict", description="[event] will happen [unspecified date/time]")
@app_commands.describe(event="The event you want to predict.")
async def predict(interaction: discord.Interaction, event: str):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
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
    event = truncateMessage(event, 750)
    await interaction.edit_original_response(content=f"Predicting when \"{event}\" will happen...\n\"{event}\" will happen {random.choice(times)}!")

@bot.tree.command(name="etanbot-10d20", description="Makes a link to use Discord's built in dice roller with 10d20 (10 20-sided dice).")
async def d20(interaction: discord.Interaction):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
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
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    await interaction.response.defer()
    liestrings = [
        "USER is LYING!!!",
        "Nah, USER isn't telling the truth.",
        "❌ Nope, USER!",
        "I wouldn't trust USER if I were you...",
        "That's straight lies, USER..."
    ]
    truthstrings = [        
        "✅ True, USER!",
        "Confirmed, USER is telling the truth.",
        "Yeah, I'd say USER is being truthful here.",
        "Trust USER!",
        "USER sounds about right"
    ]

    if random.randint(0, 1) == 0 and str(bot.user.id) != user.id: # the bot never lies.
        await interaction.edit_original_response(content=random.choice(liestrings).replace("USER", formatUsername(user)))
    else:
        await interaction.edit_original_response(content=random.choice(truthstrings).replace("USER", formatUsername(user)))

@bot.tree.command(name="etanbot-tonetag", description="Get information for a tonetag or toneindicator! Most definitions from https://tonetaglist.carrd.co/.")
@app_commands.describe(tonetag="The tonetag you wish to view information for. (do not include /)", viewprivate="Whether to view the result privately or not. (defaults to public)")
async def tonetag(interaction: discord.Interaction, tonetag: str, viewprivate: bool = False):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    await interaction.response.defer(ephemeral=viewprivate)
    if tonetag in tonetags:
        await interaction.edit_original_response(content=f"`/{tonetag}` >> {tonetags[tonetag]}")
    else:
        await interaction.edit_original_response(content=f"Couldn't find anything for `{tonetag}`.")

@tonetag.autocomplete("tonetag")
async def tonetag_autocomplete(interaction: discord.Interaction, current: str):
    thingtoreturn = [app_commands.Choice(name=key, value=key)
        for key in tonetags.keys()
        if current.lower() in key.lower()
    ][:25]
    if thingtoreturn:
        return thingtoreturn
    else:
        return [app_commands.Choice(name="No matching tonetags found", value="")]

def checkValidMBTI(mbti):
    if len(mbti) != 4 and len(mbti) != 6:
        return False
    if mbti[0] not in "EI":
        return False
    if mbti[1] not in "NS":
        return False
    if mbti[2] not in "FT":
        return False
    if mbti[3] not in "JP":
        return False
    if len(mbti) != 4:
        if mbti[5] not in "AT":
            return False
    return True

@bot.tree.command(name="etanbot-mbti", description="Lookup an mbti type/acronym! (ENTP, INTP, INTJ-T, ISFJ-A, etc.)")
@app_commands.describe(mbti="The mbti type you want to look up (ENTP, INTP, INTJ-T, ISFJ-A, etc.)", viewprivate="Whether to view the result privately or not. (defaults to public)")
async def mbti(interaction: discord.Interaction, mbti: str, viewprivate: bool = False):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    await interaction.response.defer(ephemeral=viewprivate)
    mbti = mbti.upper()
    if not checkValidMBTI(mbti):
        await interaction.edit_original_response(content="That doesn't look like a valid MBTI type. Please enter a valid type like ENTP, INTP, INTJ-T, ISFJ-A, etc.\nThe format is `E/I`, `N/S`, `F/T`, `J/P`, and optionally `-A` or `-T` for assertive or turbulent. Do not include spaces, but include the - if adding `-A` or `-T`.")
        return
    stringo = f"{mbti} means:\n"
    if mbti[0] == "I":
        stringo = stringo + "`I` >> **I**ntrovert (prefers to fly solo)\n"
    else:
        stringo = stringo + "`E` >> **E**xtrovert (enjoys company)\n"
    
    if mbti[1] == "S":
        stringo = stringo + "`S` >> **S**ensing (relies on raw senses)\n"
    else:
        stringo = stringo + "`N` >> I**n**tuition (relies on patterns and insights)\n"

    if mbti[2] == "F":
        stringo = stringo + "`F` >> **F**eeling (makes decisions based on personal values)\n"
    else:
        stringo = stringo + "`T` >> **T**hinking (makes decisions based on logic and objective criteria)\n"

    if mbti[3] == "P":
        stringo = stringo + "`P` >> **P**erception (takes in information through the senses)\n"
    else:
        stringo = stringo + "`J` >> **J**udgement (makes decisions and organizes their environment)\n"

    if len(mbti) == 6:
        if mbti[5] == "A":
            stringo = stringo + "`-A` >> **A**ssertive (self-assured, even under stress)\n"
        else:
            stringo = stringo + "`-T` >> **T**urbulent (sensitive to stress, success-driven, perfectionistic, and eager to improve)\n"

    await interaction.edit_original_response(content=stringo)

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

@bot.tree.command(name="etanbot-reference", description="IS THAT A [something] REFERENCE?!")
@app_commands.describe(reference="The thing being referenced [200 character limit]")
async def isthatareference(interaction: discord.Interaction, reference: str):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    await interaction.response.defer()
    if len(reference) > 200:
        await interaction.edit_original_response(content="Please keep the reference under 200 characters.")
        return
    await interaction.edit_original_response(content=f"IS THAT A {reference} REFERENCE?!")

@bot.tree.command(name="etanbot-headpat", description="Give someone a headpat, or headpats!") # dedicated to ruigoonr
@app_commands.describe(user="The user to give headpats to", amount="The amount of headpats to give.")
async def headpat(interaction: discord.Interaction, user: discord.User, amount: int):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    await interaction.response.defer()
    if interaction.user == user:
        await interaction.edit_original_response(content=f"You gave yourself {str(amount)} headpats!")
        return
    await interaction.edit_original_response(content=f"You gave {user.mention} {str(amount)} headpats!")

@bot.tree.command(name="etanbot-sleep", description="Use this for when someone doesn't want to sleep but should!")
@app_commands.describe(user="The user that should head to sleep", customstring="A custom message, add USER to replace with a mention (required)")
async def etanbotsleep(interaction: discord.Interaction, user: discord.User, customstring: str = None):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    await interaction.response.defer()
    if customstring != None:
        if "USER" in customstring:
            await interaction.edit_original_response(content=customstring.replace("USER", user.mention))
            return
        else:
            await interaction.edit_original_response(content="You must include the word USER if using a custom string!")
            return
    sleepstrings = [
        "USER, you should head off to sleep now!",
        "It's quite late, USER...",
        "GO TO SLEEP USER!!!",
        "Staying up late isn't good for you USER..."
    ]
    await interaction.edit_original_response(content=random.choice(sleepstrings).replace("USER", user.mention))

@bot.tree.command(name="etanbot-lock-in", description="Tell someone to lock in!")
@app_commands.describe(user="The user that should lock in", customstring="A custom message, add USER to replace with a mention (required)")
async def etanbotlockin(interaction: discord.Interaction, user: discord.User, customstring: str = None):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    await interaction.response.defer()
    if customstring != None:
        if "USER" in customstring:
            await interaction.edit_original_response(content=customstring.replace("USER", user.mention))
            return
        else:
            await interaction.edit_original_response(content="You must include the word USER if using a custom string!")
            return
    lockinstrings = [
        "Lock in USER!!!",
        "Stop getting distracted, USER!!!",
        "You know, you should really do that thing right now USER...",
        "Stop geeking out and lock in USER!!!"
    ]
    await interaction.edit_original_response(content=random.choice(lockinstrings).replace("USER", user.mention))

@bot.tree.command(name="etanbot-preview", description="Preview a message before sending it.")
async def preview(interaction: discord.Interaction):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    class previewForm(discord.ui.Modal, title="Preview a message"):
        message = discord.ui.TextInput(label="Message", style=discord.TextStyle.paragraph, placeholder="Enter your message here. Max 1800 characters.", required=True, max_length=1800)

        async def on_submit(self, interaction: discord.Interaction):
            await interaction.response.send_message(f"This is a preview of your message:\n\n{self.message.value}", ephemeral=True)
        
    await interaction.response.send_modal(previewForm())

@bot.tree.command(name="etanbot-random-list", description="Picks a random choice in a list!")
@app_commands.describe(list="The list of names or otherwise, separated by commas [,] (max 50 characters for each, up to 15 entries)", reroll="The amount of times to reroll", replacement="If rerolling multiple times, whether to make rolling the same item allowed")
async def randomList(interaction: discord.Interaction, list: str, reroll: int = None, replacement: bool = False):
    if not await handleCommandAccess(interaction, interaction.user.id, "randomlist"):
        return
    await interaction.response.defer()
    setCooldown(interaction.user.id, "randomlist", 10)
    try:
        actuallist = list.split(",")
    except Exception:
        await interaction.edit_original_response(content="That doesn't seem to be a valid list! Please separate your valies with commas. --> `,`")
        return
    if len(actuallist) < 2:
        await interaction.edit_original_response(content="Your list must have 2 or more entries!")
        return

    if len(actuallist) > 15:
        await interaction.edit_original_response(content="Your list must have less than 15 entries!")

    for item in actuallist:
        if len(item) > 50:
            await interaction.edit_original_response(content="One or more items in your list is over 50 characters!")
            return

    if reroll == None or reroll < 1:
        reroll = 1

    if reroll > len(actuallist) and reroll == False:
        reroll = len(actuallist) - 1

    rolleditems = []

    for _ in range(reroll):
        selecteditemindex = random.randint(0, len(actuallist) - 1)
        rolleditems.append(actuallist[selecteditemindex])
        if replacement == False:
            actuallist.pop(selecteditemindex)
    
    string = ""

    for item in sorted(rolleditems):
        if item[0] == " ":
            item = item[1:]
        string = string + f"{item}, "
    indeexo = len(string) - 2
    string = string[:indeexo]
    await interaction.edit_original_response(content=f"Rolling from `{list}`\nChoices picked: \n`{string}`")

@bot.tree.command(name="etanbot-scan", description="Scan a user for a percentage of how much of something they are!")
@app_commands.describe(user="The user to scan", scanfor="What to scan for (preferrably in one word, i.e goat, unemployed etc.)")
async def scanuser(interaction: discord.Interaction, user: discord.User, scanfor: str):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    await interaction.response.defer()
    if len(scanfor) > 100:
        await interaction.edit_original_response(content="Please keep your `scanfor` field short! Less than 100 characters, please.")
    percentage = random.randint(0, 100)
    await interaction.edit_original_response(content=f"{formatUsername(user)} is **{str(percentage)}%** `{scanfor}`!")

@bot.tree.command(name="etanbot-ship", description="Ship 2 users with each other!")
@app_commands.describe(user1="The first user", user2="The second user (defaults to yourself)", method="The RNG method used to ship (defaults to set)")
@app_commands.choices(method=[
    discord.app_commands.Choice(name="set", value="set"),
    discord.app_commands.Choice(name="setInverse", value="setInverse"),
    discord.app_commands.Choice(name="random", value="random"),
])
async def ship(interaction: discord.Interaction, user1: discord.User, user2: discord.User = None, method: discord.app_commands.Choice[str] = None):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    await interaction.response.defer()

    textvalues = {
        0: "Enemies",
        10: "Terrible",
        20: "Awful",
        30: "Not Too Great",
        40: "Worse than average",
        50: "Barely",
        60: "Not Bad",
        70: "Pretty Good",
        80: "Great",
        90: "Amazing",
        100: "ALL PERFECT!",
    }

    if user2 == None:
        user2 = interaction.user

    if interaction.user.id == user1.id and interaction.user.id == user2.id:
        await interaction.edit_original_response(content="You can't ship yourself with yourself!")
        return
    if user1.id == user2.id:
        await interaction.edit_original_response(content="You can't ship a user with themselves!")
        return
    
    if method == None or method == "set":
        if user1.id > user2.id:
            random.seed(str(user1.id) + str(user2.id)) # make the result consistent for the same pair of users
        else:
            random.seed(str(user2.id) + str(user1.id)) # same as above but we swap the values so it's still consistent

    elif method == "setInverse":
        if user1.id < user2.id: # legit the same as set, but we use the inverse as the seed
            random.seed(str(user1.id) + str(user2.id)) # make the result consistent for the same pair of users
        else:
            random.seed(str(user2.id) + str(user1.id)) # same as above but we swap the values so it's still consistent
    else:
        random.seed() # completely random for "random"

    percentage = random.randint(0, 100)
    extratext = ""
    for index, value in textvalues.items():
        if percentage == index or percentage > index:
            extratext = value
    embed = discord.Embed(title=f"{percentage}% // {extratext}")
    embed.add_field(name=f"{getDisplay(user1)}", value=f"@{user1.name}", inline=True)
    embed.add_field(name=f"{getDisplay(user2)}", value=f"@{user2.name}", inline=True)

    # cba finding a better way to do this
    if percentage < 30:
        embed.color = discord.Colour.red()
    elif percentage < 50:
        embed.color = discord.Colour.orange()
    elif percentage < 70:
        embed.color = discord.Colour.yellow()
    elif percentage < 100:
        embed.color = discord.Colour.green()
    else:
        embed.color = discord.Colour.pink()

    random.seed() # reset the seed so other random commands aren't affected by this one
    await interaction.edit_original_response(content=f"Shipping `{formatUsername(user1)}` and `{formatUsername(user2)}`...", embed=embed)

@bot.tree.command(name="etanbot-deretype", description="Get information for a deretype! Most definitions from https://the-dere-types.fandom.com .")
@app_commands.describe(deretype="The deretype you wish to view information for.", viewprivate="Whether to view the result privately or not. (defaults to public)")
async def deretype(interaction: discord.Interaction, deretype: str, viewprivate: bool = False):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    await interaction.response.defer(ephemeral=viewprivate)
    if deretype in deretypes:
        await interaction.edit_original_response(content=f"`{deretype}` >> {deretypes[deretype]}")
    else:
        await interaction.edit_original_response(content=f"Couldn't find anything for `{deretype}`.")

@deretype.autocomplete("deretype")
async def deretype_autocomplete(interaction: discord.Interaction, current: str):
    thingtoreturn = [app_commands.Choice(name=key, value=key)
        for key in deretypes.keys()
        if current.lower() in key.lower()
    ][:25]
    if thingtoreturn:
        return thingtoreturn
    else:
        return [app_commands.Choice(name="No matching deretypes found", value="")]

@bot.tree.command(name="etanbot-random-dere", description="Get a random deretype based on a user!")
@app_commands.describe(user="The user to get the random deretype of (defaults to yourself)", method="The method to use for finding deretype (defaults to set)")
@app_commands.choices(method=[
    discord.app_commands.Choice(name="set", value="set"),
    discord.app_commands.Choice(name="random", value="random"),
])
async def randomDere(interaction: discord.Interaction, user: discord.User = None, method: discord.app_commands.Choice[str] = None):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    await interaction.response.defer()
    if user == None:
        user = interaction.user

    methodreal = ""
    if method == None:
        methodreal = "set"
    else:
        methodreal = method.value

    if methodreal == "set":
        random.seed(str(user.id)) # make the result consistent for the same user
    else:
        random.seed() # completely random for "random"

    deretype = random.choice(list(deretypes.keys()))
    random.seed() # reset the seed so other random commands aren't affected by this one
    await interaction.edit_original_response(content=f"{formatUsername(user)}'s a `{deretype}` >> {deretypes[deretype]}\n\n*This result is based on the `{methodreal}` method.*")

@bot.tree.command(name="etanbot-regional-indicator", description="Turn a sentence into regional indicator emojis!")
@app_commands.describe(text="The text to turn into emojis, only letters or numbers. Max 90 chars.", copyable="(click to copy on mobile) Whether to make the result copyable (defaults to false).")
async def regionalIndicators(interaction: discord.Interaction, text: str, copyable: bool = False):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    await interaction.response.defer()
    numbers = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"}
    if len(text) > 90:
        await interaction.edit_original_response(content="Please keep your text under 90 characters.")
        return
    text = text.lower()
    result = ""
    for char in text:
        if char.isalpha():
            result += f":regional_indicator_{char}: "
        elif char in numbers.keys():
            result += f":{numbers[char]}:"
        elif char == " ":
            result += "   "
        else:
            await interaction.edit_original_response(content="Please only use letters, numbers, and spaces.")
            return
    if copyable:
        await interaction.edit_original_response(content=f"`{result}`")
    else:
        await interaction.edit_original_response(content=result)

@bot.tree.command(name="etanbot-read-indicator", description="Show a (barebones) indicator/message that you've read the message(s) in chat!")
async def readIndicator(interaction: discord.Interaction, fakeread: bool = None):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    await interaction.response.defer()
    if fakeread is None:
        fakeread = False
    if fakeread:
        await interaction.edit_original_response(content=f"⨯ Not read by {formatUsername(interaction.user)}")
    else:
        await interaction.edit_original_response(content=f"✓ Read by {formatUsername(interaction.user)}")

@bot.tree.command(name="etanbot-slop-or-gem", description="Check if something is slop or gem!")
@app_commands.describe(scan="Let's see if this thing is slop or gem!")
async def slopOrGem(interaction: discord.Interaction, scan: str):
    if not await handleCommandAccess(interaction, interaction.user.id):
        return
    await interaction.response.defer()
    if len(scan) > 500:
        await interaction.edit_original_response(content="Your \"scan\" object is WAY too long!")
        return
    randomnumber = random.randint(-100, 100)
    if randomnumber < 0:
        await interaction.edit_original_response(content=f"`{scan}` is {abs(randomnumber)}% **slop**!")
    else:
        await interaction.edit_original_response(content=f"`{scan}` is {abs(randomnumber)}% **gem**!")

@bot.tree.command(name="paro", description="paro") # paro
@app_commands.describe(detailed="Whether to return detailed RNG results (defaults to false).")
async def paro(paro: discord.Interaction, detailed: bool = False): # paro
    if not await handleCommandAccess(paro, paro.user.id, "paro"):
        return
    await paro.response.defer() # paro
    setCooldown(paro.user.id, "paro", 1)
    randomnumber = random.randint(1, 1000)
    extrarandomnum = random.randint(1, 20)
    extrastring = ""

    if extrarandomnum == 1: # 1 (1 in 20)
        extrastring = "# TEXT"
    elif extrarandomnum < 4: # 2-3 (roughly 1 in 10)
        extrastring = "**TEXT**"
    elif extrarandomnum < 9: # 4-8 (roughly 1 in 4)
        extrastring = "*TEXT*"
    else:
        extrastring = "TEXT"
    
    if detailed:
        extrastring = extrastring + f"\n-# rng `{randomnumber}` (1-1000) // extra rng `{extrarandomnum}` (1-20)"

    if randomnumber == 1: # 1 (1 in 1000)
        await paro.edit_original_response(content=f"{extrastring.replace('TEXT', 'Paranoia')}") # Paranoia
    elif randomnumber < 12: # 2-11 (roughly 1 in 100)
        await paro.edit_original_response(content=f"{extrastring.replace('TEXT', 'Parousia')}") # Parousia
    elif randomnumber < 113: # 12-112 (roughly 1 in 10)
        await paro.edit_original_response(content=f"{extrastring.replace('TEXT', 'Paro')}") # Paro
    else: # the default
        await paro.edit_original_response(content=f"{extrastring.replace('TEXT', 'paro')}") # paro

bot.run(config['token'])