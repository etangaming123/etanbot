import discord # type: ignore
from discord.ext import commands # type: ignore
from discord import app_commands # type: ignore
import os # type: shit
import pickle
import json
import traceback
import random
import requests # type: ignore
from bs4 import BeautifulSoup # type: ignore
import re

intents = discord.Intents.default()
kokocreditdefaulturl = "https://estore.kokoamusement.com.au/BalanceMobile/BalanceMobile.aspx?i="

datastores = ["linkedkokocards", "profiles"] # pkls to create
for item in datastores:
    if not os.path.exists(f"{item}.pkl"):
        with open(f"{item}.pkl", "wb") as file:
            pickle.dump({}, file)
        print(f"Created new file [{item}.pkl]")

datastoresbuttheseonesarelists = [] # pkls to create but these are lists
for item in datastoresbuttheseonesarelists:
    if not os.path.exists(f"{item}.pkl"):
        with open(f"{item}.pkl", "wb") as file:
            pickle.dump([], file)
        print(f"Created new file [{item}.pkl]")

def formatUsername(user: discord.User): # Fancy formatting for usernames // displayname (@username)
    if user.display_name == None:
        return f"{user.name}"
    else:
        return f"{user.display_name} (@{user.name})"

def getDisplay(user: discord.User): # incase we only want to get display name and the users display is same as username
    if user.display_name == None:
        return user.name
    else:
        return user.display_name

def saveData(store: str, newdata: dict): # Saves data to a specified .pkl file
    print(f"Saving [{store}]...")
    try:
        backup = loadData(store) 
        with open(f"{store}_backup.pkl", "wb") as file:
            pickle.dump(backup, file)
        with open(f"{store}.pkl", "wb") as file:
            pickle.dump(newdata, file)
        os.remove(f"{store}_backup.pkl")
        return True # Return true if it succeeds
    except Exception:
        traceback.print_exc()
        with open(f"{store}.pkl", "wb") as file:
            pickle.dump(backup, file)
        return False # Otherwise return false

def loadData(store: str): # Gets data from a specified .pkl file
    try:
        with open(f"{store}.pkl", "rb") as file:
            return pickle.load(file) # Return file data if it succeeds
    except Exception:
        traceback.print_exc()
        return "" # Otherwise return an empty string

def truncateMessage(message, length): 
    if len(message) <= length:
        return message
    else:
        return message[:length-20] + f"... [{len(message)-length+20} more characters]"

if not os.path.exists("config.json"):
    with open("config.json", "w") as f:
        json.dump({"token": "your token here", "poweruserid": "your user id here (for certain commands)"}, f, indent=4)
    input("Created config.json with default values. Please edit the file with your bot token and user id, then press enter to continue...")

with open('config.json') as f:
    config = json.load(f)

bot = commands.Bot(command_prefix='!', intents=intents)
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

@bot.tree.command(name="etanbot-clean-link", description="Remove stinky link trackers.")
@app_commands.describe(link="The link you want to clean.", additional="Any additional parameters to remove.")
async def clean_link(interaction: discord.Interaction, link: str, additional: str = None):
    await interaction.response.defer()
    toremove = ["igsh", "si", "fbclid", "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "is"]
    if additional:
        toremove.extend(additional.split(","))
    cleaned_link = link
    for item in toremove:
        cleaned_link = re.sub(r'([&?])' + re.escape(item) + r'=[^&]*', '', cleaned_link)
    cleaned_link = re.sub(r'[?&]+$', '', cleaned_link) # remove trailing ? or &
    await interaction.edit_original_response(content=f"Removed stinky link trackers: {cleaned_link}")

# koko amusement linking
def get_koko_balance(token: str):
    try:
        response = requests.get(f"{kokocreditdefaulturl}{token}")
        if response.status_code != 200:
            print(f"Error fetching koko balance: Received status code {response.status_code}")
            return "ERROR_NET"
        soup = BeautifulSoup(response.text, 'html.parser')

        # Target labels we want to extract
        labels = ["Cash Balance", "Cash Bonus", "Points"]
        thingo = [] # list of the things we find to return at the end
        for label in labels:
            # find text node that matches the label (case-insensitive)
            node = soup.find(string=re.compile(r"^\s*" + re.escape(label) + r"\s*$", re.I))
            value = None
            if node:
                # try common nearby locations for the value
                parent = node.parent
                # look for next sibling text or next table cell
                nxt = parent.find_next_sibling()
                if nxt and nxt.get_text(strip=True):
                    value = nxt.get_text(strip=True)
                else:
                    # fallback: search next td or span
                    nxt_tag = parent.find_next(['td', 'span', 'div'])
                    if nxt_tag:
                        value = nxt_tag.get_text(strip=True)
            # final fallback: search whole document for the label and grab following numbers
            if not value:
                m = re.search(re.escape(label) + r"\s*[:\-]?\s*([\d,\.]+)", soup.get_text(), re.I)
                if m:
                    value = m.group(1)

            thingo.append(f"{label}: {value if value else 'Not found'}")
        return f"Your koko amusement balance:\n" + "\n".join(thingo)
    except Exception as e:
        print(f"Error fetching koko balance: {e}")
        traceback.print_exc()
        return "ERROR"

@bot.tree.command(name="etanbot-koko-help", description="Need help on linking your Koko Amusement card?")
async def koko_help(interaction: discord.Interaction):
    await interaction.response.defer()
    things = [ # I'm organising each new line in an array because I'm cool like that B)
        "To link your Koko Amusement card, you need to get your token from the Koko Amusement website. Here's how you can do it:",
        "1. Scan the QR code on the back of your Koko Amusement card using your phone.",
        "2. Open the link that appears in your browser. It should look something like this: `https://estore.kokoamusement.com.au/BalanceMobile/BalanceMobile.aspx?i=[YourTokenHere]` on your browser's URL address bar.",
        "3. Copy everything that appears after the `?i=` in the URL. This is your token.",
        "4. Use the `/etanbot-koko-link-card` command and paste your token there to link your card to your Discord account!",
        "You're all set! You won't have to do this again, just use /etanbot-koko-balance to check your balance whenever you want.",
        "Rerun the link command if you want to update your card token or if you get an error when checking your balance."
    ]
    await interaction.edit_original_response(content="\n".join(things))

@bot.tree.command(name="etanbot-koko-link-card", description="Link your Koko Amusement card to your discord account to check your balance and transactions!")
@app_commands.describe(token="/BalanceMobile.aspx?i=[this set of characters]")
async def link_card(interaction: discord.Interaction, token: str):
    await interaction.response.defer()
    linkedkokocards = loadData("linkedkokocards")
    if linkedkokocards == "":
        await interaction.edit_original_response(content="An error occurred while accessing the database. Please try again later.")
        return
    linkedkokocards[str(interaction.user.id)] = token
    saveData("linkedkokocards", linkedkokocards)
    thingo = get_koko_balance(token)
    if thingo == "ERROR":
        await interaction.edit_original_response(content="An error occurred while fetching your koko amusement balance. Please make sure your token is correct and try again later. If this error persists, please [report a bug](https://github.com/etangaming123/etanbot/issues/new).")
        return
    elif thingo == "ERROR_NET":
        await interaction.edit_original_response(content="An error occurred while sending request. Please try again later. (if issue persists, check the card balance manually, and if it does work, [report a bug](https://github.com/etangaming123/etanbot/issues/new).)")
        return
    await interaction.edit_original_response(content=f"Successfully linked koko amusement card! {thingo}\nYou can always rerun this command to update your card!")

@bot.tree.command(name="etanbot-koko-balance", description="Check your koko amusement balance if you have linked your card using /etanbot-koko-link-card!")
async def my_koko_balance(interaction: discord.Interaction):
    await interaction.response.defer()
    linkedkokocards = loadData("linkedkokocards")
    if linkedkokocards == "":
        await interaction.edit_original_response(content="An error occurred while accessing the database. Please try again later.")
        return
    token = linkedkokocards.get(str(interaction.user.id))
    if not token:
        await interaction.edit_original_response(content="You have not linked a koko amusement card yet! Use /etanbot-koko-link-card to link your card and check your balance!")
        return
    thingo = get_koko_balance(token)
    if thingo == "ERROR":
        await interaction.edit_original_response(content="An error occurred while fetching your koko amusement balance. Please make sure your token is correct and try again later. If this error persists, please [report a bug](https://github.com/etangaming123/etanbot/issues/new).")
        return
    elif thingo == "ERROR_NET":
        await interaction.edit_original_response(content="An error occurred while sending request. Please try again later. (if issue persists, check the card balance manually, and if it does work, [report a bug](https://github.com/etangaming123/etanbot/issues/new).)")
        return
    await interaction.edit_original_response(content=thingo)

@bot.tree.command(name="etanbot-koko-unlink-card", description="Unlink your koko amusement card from your discord account.")
async def unlink_card(interaction: discord.Interaction):
    await interaction.response.defer()
    linkedkokocards = loadData("linkedkokocards")
    if linkedkokocards == "":
        await interaction.edit_original_response(content="An error occurred while accessing the database. Please try again later.")
        return
    if str(interaction.user.id) in linkedkokocards:
        del linkedkokocards[str(interaction.user.id)]
        saveData("linkedkokocards", linkedkokocards)
        await interaction.edit_original_response(content="Successfully unlinked your koko amusement card.")
    else:
        await interaction.edit_original_response(content="You do not have a koko amusement card linked.")

# profiles
@bot.tree.command(name="etanbot-profile-create", description="Creates a profile for you, viewable using /etanbot-profile!")
async def create_profile(interaction: discord.Interaction):
    await interaction.response.defer()
    await interaction.response.defer(ephemeral=True)
    profiles = loadData("profiles")
    if str(interaction.user.id) in profiles.keys():
        await interaction.edit_original_response(content=f"You already have a profile! Use /etanbot-profile to view it.")
        return
    profiles[str(interaction.user.id)] = {
        "bio": "Nothing yet... use /etanbot-profile-edit to edit this! Max 256 characters.",
        "links": {}
    }
    if saveData("profiles", profiles):
        await interaction.edit_original_response(content=f"Profile created successfully!")
    else:
        await interaction.edit_original_response(content=f"An error occurred while creating your profile. Please try again later.")

@bot.tree.command(name="etanbot-profile", description="View your profile or someone else's!")
@app_commands.describe(user="The user to view the profile of. Defaults to yourself.", viewprivately="Want to make it so only you can see the profile? (defaults to nah)")
async def viewprofile(interaction: discord.Interaction, user: discord.User = None, viewprivately: bool = False):
    await interaction.response.defer()
    containsatsymbol = ["tiktok", "youtube"] # these platforms require an @ symbol in the url
    await interaction.response.defer(ephemeral=viewprivately)
    if user is None:
        user = interaction.user
    profiles = loadData("profiles")
    if str(user.id) not in profiles:
        await interaction.edit_original_response(content=f"This user does not have a profile yet! They can create one using /etanbot-profile-create.")
        return
    profile = profiles[str(user.id)]
    if not "color" in profile:
        profile["color"] = 0x00ff00 # default color is green
    embed = discord.Embed(title=f"{formatUsername(user)}'s Profile", color=profile.get("color", 0x00ff00))
    embed.add_field(name="About Me", value=profile["bio"], inline=False)
    stringystringy = ""
    for platform, username in profile["links"].items():
        link = username
        if platform in containsatsymbol:
            link = f"@{username}"
        stringystringy += f"{platform.capitalize()}: [@{username}](https://{platform}.com/{link})\n"
    if stringystringy == "":
        stringystringy = "No social links set."
    embed.add_field(name="Links", value=stringystringy, inline=False)
    embed.set_thumbnail(url=user.avatar.url if user.avatar else "https://cdn.discordapp.com/embed/avatars/0.png")
    await interaction.edit_original_response(embed=embed)

class ProfileEditModal(discord.ui.Modal, title="Edit Your Profile"):
    def __init__(self, profile):
        super().__init__()
        self.profile = profile
        self.bio = discord.ui.TextInput(label="Bio", style=discord.TextStyle.paragraph, default=profile["bio"], max_length=256)
        self.add_item(self.bio)

    async def on_submit(self, interaction: discord.Interaction):
        profiles = loadData("profiles")
        user_id = str(interaction.user.id)
        if user_id not in profiles:
            await interaction.response.send_message(content=f"Your profile was not found. Please create a new one using /etanbot-profile-create. Here's your bio if you need to copy and paste:\n{self.profile['bio']}", embed=None, view=None, ephemeral=True)
            return
        profiles[user_id]["bio"] = self.bio.value
        if saveData("profiles", profiles):
            await interaction.response.send_message(content=f"Profile updated successfully!", embed=None, view=None, ephemeral=True)
        else:
            await interaction.response.send_message(content=f"An error occurred while updating your profile. Please try again later. Here's your bio if you need to copy and paste:\n{self.profile['bio']}", embed=None, view=None, ephemeral=True)

@bot.tree.command(name="etanbot-profile-edit", description="Edit your profile's bio!")
async def editprofile(interaction: discord.Interaction):
    await interaction.response.defer()
    profiles = loadData("profiles")
    if str(interaction.user.id) not in profiles.keys():
        await interaction.edit_original_response(content=f"You don't have a profile yet! Use /etanbot-profile-create to create one.")
        return
    profile = profiles[str(interaction.user.id)]
    await interaction.response.send_modal(ProfileEditModal(profile))

@bot.tree.command(name="etanbot-profile-delete", description="Delete your profile! This cannot be undone.")
async def deleteprofile(interaction: discord.Interaction):
    await interaction.response.defer()
    await interaction.response.defer(ephemeral=True)
    profiles = loadData("profiles")
    if str(interaction.user.id) not in profiles.keys():
        await interaction.edit_original_response(content=f"You don't have a profile yet! Use /etanbot-profile-create to create one.")
        return
    del profiles[str(interaction.user.id)]
    if saveData("profiles", profiles):
        await interaction.edit_original_response(content=f"Profile deleted successfully!")
    else:
        await interaction.edit_original_response(content=f"An error occurred while deleting your profile. Please try again later.")

@bot.tree.command(name="etanbot-profile-color", description="Change the color of your profile embed! (hex code, no #, default is green)")
@app_commands.describe(color="The hex code of the color you want to set for your profile embed (no #, default is green)")
async def changeprofilecolor(interaction: discord.Interaction, color: str):
    await interaction.response.defer(ephemeral=True)
    profiles = loadData("profiles")
    if str(interaction.user.id) not in profiles.keys():
        await interaction.edit_original_response(content=f"You don't have a profile yet! Use /etanbot-profile-create to create one.")
        return
    try:
        color = int(color, 16)
    except ValueError:
        await interaction.edit_original_response(content=f"Invalid color format. Please use a valid hex code (no #).")
        return
    profiles[str(interaction.user.id)]["color"] = color
    if saveData("profiles", profiles):
        await interaction.edit_original_response(content=f"Profile color updated successfully!")
    else:
        await interaction.edit_original_response(content=f"An error occurred while updating your profile color. Please try again later.")

@bot.tree.command(name="etanbot-profile-link-add", description="Add a link to your profile! (tiktok, instagram, twitter, more later!)")
@app_commands.describe(platform="Only shows supported platforms for now!", username="Your username/handle on the platform (no urls or @, just the username)")
@app_commands.choices(platform=[
    discord.app_commands.Choice(name="TikTok", value="tiktok"),
    discord.app_commands.Choice(name="Instagram", value="instagram"),
    discord.app_commands.Choice(name="Twitter", value="twitter"),
    discord.app_commands.Choice(name="YouTube", value="youtube")
])
async def addprofilelink(interaction: discord.Interaction, platform: discord.app_commands.Choice[str], username: str):
    await interaction.response.defer(ephemeral=True)
    profiles = loadData("profiles")
    if str(interaction.user.id) not in profiles.keys():
        await interaction.edit_original_response(content=f"You don't have a profile yet! Use /etanbot-profile-create to create one.")
        return
    if not "links" in profiles[str(interaction.user.id)]:
        profiles[str(interaction.user.id)]["links"] = {}
    profiles[str(interaction.user.id)]["links"][platform.value] = username

    if not saveData("profiles", profiles):
        await interaction.edit_original_response(content=f"An error occurred while adding the link to your profile. Please try again later.")
        return
    await interaction.edit_original_response(content=f"Link added successfully!")

@bot.tree.command(name="etanbot-profile-link-remove", description="Remove a link from your profile.")
@app_commands.describe(platform="The platform of the link you want to remove.")
@app_commands.choices(platform=[
    discord.app_commands.Choice(name="TikTok", value="tiktok"),
    discord.app_commands.Choice(name="Instagram", value="instagram"),
    discord.app_commands.Choice(name="Twitter", value="twitter"),
    discord.app_commands.Choice(name="YouTube", value="youtube")
])
async def removeprofilelink(interaction: discord.Interaction, platform: discord.app_commands.Choice[str]):
    await interaction.response.defer(ephemeral=True)
    profiles = loadData("profiles")
    if str(interaction.user.id) not in profiles.keys():
        await interaction.edit_original_response(content=f"You don't have a profile yet! Use /etanbot-profile-create to create one.")
        return
    if not "links" in profiles[str(interaction.user.id)] or platform.value not in profiles[str(interaction.user.id)]["links"]:
        await interaction.edit_original_response(content=f"You don't have a link for that platform on your profile!")
        return
    del profiles[str(interaction.user.id)]["links"][platform.value]
    if not saveData("profiles", profiles):
        await interaction.edit_original_response(content=f"An error occurred while removing the link from your profile. Please try again later.")
        return
    await interaction.edit_original_response(content=f"Link removed successfully!")

bot.run(config['token'])