import json
import os
import hashlib
import pickle
import discord
import time

from crypto_utils import encrypt_value, decrypt_value

# change these if you need
repositoryurl = "https://github.com/etangaming123/etanbot"
developergithub = "https://github.com/etangaming123"
inviteurl = "https://discord.com/oauth2/authorize?client_id=1505906056222605352"
supportserver = "https://etanbot.etangaming.xyz/supportserver.html"
website = "https://etanbot.etangaming.xyz"

statuses = ["special1", "special2", "etanbot.etangaming.xyz", "open source and free to use <3", "by etangaming123", "kairiki bear bug", "pa pa para paranoia", "Not a teapot!", "/etanbot-who-am-i", "Cleaning links since May 18, i think", "I think thoughts, and thoughts always make me think"]

# more options
checkforupdates = True
enablecooldowns = True

# no touchy! unless you want more datastores
userdatastores = ["linkedkokocards", "profiles"]
otherdatastores = ["bannedusers", "gifs"]
datastoresbuttheseonesarelists = []

sensitivestores = ["linkedkokocards"] # datastores whose values should never be shown raw (e.g. in /etanbot-list-data)

datastores = []

# idk if theres a better way lmfao
for item in userdatastores:
    datastores.append(item)

for item in otherdatastores:
    datastores.append(item)

cooldowns = {}

def ensure_datastores(): # converting from pkl to json if needed, and creating new files if they don't exist
    for item in datastores:

        if os.path.exists(f"{item}.pkl"):
            data = pickle.load(open(f"{item}.pkl", "rb"))
            with open(f"{item}.json", "w") as file:
                json.dump(data, file, indent=4)
                print(f"Converted [{item}.pkl] to [{item}.json]")

        if not os.path.exists(f"{item}.json"):
            with open(f"{item}.json", "w") as file:
                json.dump({}, file)
            print(f"Created new file [{item}.json]")

    for item in datastoresbuttheseonesarelists:

        if os.path.exists(f"{item}.pkl"):
            data = pickle.load(open(f"{item}.pkl", "rb"))
            with open(f"{item}.json", "w") as file:
                json.dump(data, file, indent=4)
                print(f"Converted [{item}.pkl] to [{item}.json]")

        if not os.path.exists(f"{item}.json"):
            with open(f"{item}.json", "w") as file:
                json.dump([], file)
            print(f"Created new file [{item}.json]")

    migrate_koko_tokens()

def migrate_koko_tokens(): # idempotent: encrypts any plaintext koko tokens still on disk, leaves already-encrypted ones alone
    data = loadData("linkedkokocards")
    if data == "" or not data:
        return
    changed = False
    for userid, token in data.items():
        try:
            decrypt_value(token) # already valid ciphertext, nothing to do
        except Exception:
            data[userid] = encrypt_value(token) # legacy/plaintext value, encrypt it
            changed = True
    if changed:
        saveData("linkedkokocards", data)
        print("Migrated legacy plaintext koko tokens to encrypted storage.")

def saveData(store: str, newdata: dict):
    try:
        backup = loadData(store)
        with open(f"{store}_backup.json", "w") as file: # write a back up just in case. (learnt this the hard way when a datastore went blank)
            json.dump(backup, file, indent=4)
        with open(f"{store}.json", "w") as file:
            json.dump(newdata, file, indent=4)
        os.remove(f"{store}_backup.json")
        return True
    
    except Exception as e:
        print(f"Error saving data, restoring backup: {e}")
        with open(f"{store}.json", "w") as file:
            json.dump(backup, file, indent=4)
        return False

def loadData(store: str):
    try:
        with open(f"{store}.json", "r") as file:
            data = json.load(file)
            if store in datastoresbuttheseonesarelists:
                return data if isinstance(data, list) else []
            return data if isinstance(data, dict) else {}
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return "" # commands are written to handle empty string as error, so we return that instead of None or {}

config = loadData("config")
poweruserid = config["poweruserid"] # to bypass cooldowns if you're cool B)
bannedusers = loadData("bannedusers") # load once

def getUserHash(userid: int):
    return hashlib.sha1(str(userid).encode("utf-8")).hexdigest()

def removeFormatting(string: str): # Remove Discord formatting from a string (using backslashes to escape formatting characters)
    formatting_chars = ['*', '_', '~', '`', '>', '|']
    for char in formatting_chars:
        string = string.replace(char, f'\{char}')
    return string

def formatUsername(user: discord.User): # Fancy formatting for usernames // displayname (@username)
    if user.display_name == None:
        return f"{removeFormatting(user.name)}"
    else:
        return f"{user.display_name} (@{removeFormatting(user.name)})"

def getDisplay(user: discord.User): # incase we only want to get display name and the users display is same as username
    if user.display_name == None:
        return removeFormatting(user.name)
    else:
        return removeFormatting(user.display_name)

def truncateMessage(message, length): 
    if len(message) <= length:
        return message
    else:
        return message[:length-30] + f"... [{len(message)-length+30} more characters]"

def checkIfCooldown(userid: int, commandname: str):
    if not enablecooldowns: # always return -1 (no cooldown) if cooldowns are disabled
        return -1
    if poweruserid != None and userid == int(poweruserid):
        return -1 # no cooldown for power user
    if not userid in cooldowns:
        cooldowns[userid] = {}
    if not commandname in cooldowns[userid]:
        return -1
    if time.time() < cooldowns[userid][commandname]:
        return round(cooldowns[userid][commandname]) # return timestamp of when they can use command again
    else:
        del cooldowns[userid][commandname] # remove cooldown since it's expired
        return -1

def setCooldown(userid: int, commandname: str, cooldowntime: int):
    if poweruserid != None and userid == int(poweruserid):
        return # no cooldown for power user
    if not userid in cooldowns:
        cooldowns[userid] = {}
    cooldowns[userid][commandname] = round(time.time() + cooldowntime)

def checkIfBanned(userid: int):
    global bannedusers
    ban_key = getUserHash(userid)
    if ban_key in bannedusers:
        if bannedusers[ban_key]["length"] == "ncmd":
            return bannedusers[ban_key]
        if bannedusers[ban_key]["length"] != None and time.time() > bannedusers[ban_key]["length"]:
            del bannedusers[ban_key]
            saveData("bannedusers", bannedusers)
            return False
        if ban_key != getUserHash(userid):
            bannedusers[getUserHash(userid)] = bannedusers[ban_key]
            del bannedusers[ban_key]
            saveData("bannedusers", bannedusers)
            return bannedusers[getUserHash(userid)]
        return bannedusers[ban_key]
    return False

async def handleCommandAccess(interaction: discord.Interaction, userid: int, commandname: str = None):
    banned = checkIfBanned(userid)
    if banned:
        ban_length = banned.get("length")
        reason = banned.get("reason") or "No reason provided."
        if ban_length == "ncmd":
            ban_until = "the next command you try to use."
            currentbanned = getBannedUsers(refresh=True)
            del currentbanned[getUserHash(userid)]
            saveData("bannedusers", currentbanned)
            getBannedUsers(refresh=True)  # Refresh the banned users list after saving

        elif ban_length != None:
            ban_until = f"<t:{round(ban_length)}:F>"

        else:
            ban_until = "the bot gets shut down, apparently."
        await interaction.response.send_message(content=f"You are banned from using etan bot until {ban_until}.\n\n{reason}", ephemeral=True)
        return False

    if commandname != None:
        cooldown = checkIfCooldown(userid, commandname)
        if cooldown != -1:
            await interaction.response.send_message(content=f"Slow down, dude! You can use this command again <t:{cooldown}:R>", ephemeral=True)
            return False

    return True

def purgeUserData(userid: int):
    userid = str(userid)
    for store in userdatastores:
        data = loadData(store)
        if data == "":
            return False
        if userid in data:
            del data[userid]
            if not saveData(store, data):
                return False
    return True

class ConfirmView(discord.ui.View):
    def __init__(self, author_id: int, timeout: float = 30):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.value = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(content="This confirmation isn't for you.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
        await interaction.response.defer()

def getBannedUsers(refresh: bool = False):
    global bannedusers
    if refresh:
        bannedusers = loadData("bannedusers")
    return bannedusers

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
