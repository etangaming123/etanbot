import json
import os
import hashlib
import pickle
import discord
import time

repositoryurl = "https://github.com/etangaming123/etanbot"
developergithub = "https://github.com/etangaming123"
inviteurl = "https://discord.com/oauth2/authorize?client_id=1505906056222605352"
supportserver = "https://etanbot.etangaming.xyz/supportserver.html"
website = "https://etanbot.etangaming.xyz"

datastores = ["linkedkokocards", "profiles", "gifs", "bannedusers"]
datastoresbuttheseonesarelists = []

cooldowns = {}

def ensure_datastores():
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

def saveData(store: str, newdata: dict):
    try:
        backup = loadData(store)
        with open(f"{store}_backup.json", "w") as file:
            json.dump(backup, file)
        with open(f"{store}.json", "w") as file:
            json.dump(newdata, file)
        os.remove(f"{store}_backup.json")
        return True
    except Exception as e:
        print(f"Error saving data, restoring backup: {e}")
        with open(f"{store}.json", "w") as file:
            json.dump(backup, file)
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
        return [] if store in datastoresbuttheseonesarelists else {}

config = loadData("config")
poweruserid = config["poweruserid"] # to bypass cooldowns if you're cool B)
bannedusers = loadData("bannedusers") # load once

def getBanKey(userid: int):
    return hashlib.sha1(str(int(userid)).encode("utf-8")).hexdigest()

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

def checkIfCooldown(userid: int, commandname: str): # Don't like cooldowns? If running a selfhosted instance, just make this return -1! Simple as that!
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
    ban_keys = [getBanKey(userid), str(hash(userid)), str(hash(str(userid)))]
    for ban_key in ban_keys:
        if ban_key in bannedusers:
        
            if bannedusers[ban_key]["length"] != None and time.time() > bannedusers[ban_key]["length"]:
                del bannedusers[ban_key]
                saveData("bannedusers", bannedusers)
                return False
            if ban_key != getBanKey(userid):
                bannedusers[getBanKey(userid)] = bannedusers[ban_key]
                del bannedusers[ban_key]
                saveData("bannedusers", bannedusers)
                return bannedusers[getBanKey(userid)]
            return bannedusers[ban_key]
    return False

async def handleCommandAccess(interaction: discord.Interaction, userid: int, commandname: str = None):
    banned = checkIfBanned(userid)
    if banned:
        ban_length = banned.get("length")
        reason = banned.get("reason") or "No reason provided."
        if ban_length != None:
            ban_until = f"<t:{round(ban_length)}:F>"
        else:
            ban_until = "permanently"
        await interaction.response.send_message(content=f"You are banned from using etan bot until {ban_until}. Reason: {reason}", ephemeral=True)
        return False

    if commandname != None:
        cooldown = checkIfCooldown(userid, commandname)
        if cooldown != -1:
            await interaction.response.send_message(content=f"You can use this command again <t:{cooldown}:R>", ephemeral=True)
            return False

    return True

def getBannedUsers(refresh: bool = False):
    global bannedusers
    if refresh:
        bannedusers = loadData("bannedusers")
    return bannedusers