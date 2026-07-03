import json
import os
import pickle
import discord
import time

kokocreditdefaulturl = "https://estore.kokoamusement.com.au/BalanceMobile/BalanceMobile.aspx?i="
repositoryurl = "https://github.com/etangaming123/etanbot"
developergithub = "https://github.com/etangaming123"
inviteurl = "https://discord.com/oauth2/authorize?client_id=1505906056222605352"
supportserver = "https://etanbot.etangaming.xyz/supportserver.html"
website = "https://etanbot.etangaming.xyz"

datastores = ["linkedkokocards", "profiles", "gifs"]
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
    print(f"Saving [{store}]...")
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
            return json.load(file)
    except Exception as e:
        print(f"Error loading data: {e}")
        return ""

config = loadData("config")
poweruserid = config["poweruserid"] # to bypass cooldowns if you're cool B)

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