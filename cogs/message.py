import discord
from discord.ext import commands
from discord import app_commands
import random

from common import handleCommandAccess, formatUsername, truncateMessage, setCooldown, config

class messageCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="etanbot-puppet", description="Make the bot say something (as a response to the command, not in the channel).")
    @app_commands.describe(say="The thing to say.")
    async def puppet(self, interaction: discord.Interaction, say: str):
        if not await handleCommandAccess(interaction, interaction.user.id, "puppet"):
            return
        await interaction.response.defer()
        setCooldown(interaction.user.id, "puppet", 5)
        if interaction.user.id != int(config["poweruserid"]):
            say = f"-# triggered by {interaction.user.mention}\n{say}"
        realthing = truncateMessage(say, 2000)
        await interaction.edit_original_response(content=realthing)
        setCooldown(interaction.user.id, "puppet", 10)

    @app_commands.command(name="etanbot-puppet-v2", description="Make the bot say something, but better (kinda)")
    @app_commands.describe(say="<nl> gets replaced with a new line")
    async def puppetv2(self, interaction: discord.Interaction, say: str):
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

    @app_commands.command(name="etanbot-puppet-v3", description="Make the bot say something, but even better!")
    async def puppetv3(self, interaction: discord.Interaction):
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

        
    @app_commands.command(name="etanbot-regional-indicator", description="Turn a sentence into regional indicator emojis!")
    @app_commands.describe(text="The text to turn into emojis, only letters or numbers. Max 90 chars.", copyable="(click to copy on mobile) Whether to make the result copyable (defaults to false).")
    async def regionalIndicators(self, interaction: discord.Interaction, text: str, copyable: bool = False):
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

    @app_commands.command(name="etanbot-read-indicator", description="Show a (barebones) indicator/message that you've read the message(s) in chat!")
    async def readIndicator(self, interaction: discord.Interaction, fakeread: bool = None):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        await interaction.response.defer()
        if fakeread is None:
            fakeread = False
        if fakeread:
            await interaction.edit_original_response(content=f"⨯ Not read by {formatUsername(interaction.user)}")
        else:
            await interaction.edit_original_response(content=f"✓ Read by {formatUsername(interaction.user)}")

    @app_commands.command(name="etanbot-birthday", description="Whose birthday is it?")
    @app_commands.describe(user="The user whose birthday it is (defaults to yourself).")
    async def birthday(self, interaction: discord.Interaction, user: discord.User = None):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        setCooldown(interaction.user, "message-ping", 10)
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
        if user == self.bot.user:
            await interaction.edit_original_response(content="thanks but i don't think it's my birthday...")
            return
        await interaction.edit_original_response(content=random.choice(bdaystrings).replace("USER", user.mention))

    @app_commands.command(name="etanbot-shexonmyytilliz", description="she [x] on my [y] till i [z]")
    @app_commands.describe(x="she does what [100 chars]", y="on your what [100 chars]", z="until you what [100 chars]")
    async def shexonmyytilliz(self, interaction: discord.Interaction, x: str, y: str, z: str):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        if len(x) > 100 or len(y) > 100 or len(z) > 100:
            await interaction.response.defer()
            await interaction.edit_original_response(content="Please keep each input under 100 characters.")
            return
        await interaction.response.defer()
        await interaction.edit_original_response(content=f"she {x} on my {y} till i {z}")


    @app_commands.command(name="etanbot-reference", description="IS THAT A [something] REFERENCE?!")
    @app_commands.describe(reference="The thing being referenced [200 character limit]")
    async def isthatareference(self, interaction: discord.Interaction, reference: str):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        await interaction.response.defer()
        if len(reference) > 200:
            await interaction.edit_original_response(content="Please keep the reference under 200 characters.")
            return
        await interaction.edit_original_response(content=f"IS THAT A {reference} REFERENCE?!")

    @app_commands.command(name="etanbot-headpat", description="Give someone a headpat, or headpats!") # dedicated to ruigoonr
    @app_commands.describe(user="The user to give headpats to", amount="The amount of headpats to give.")
    async def headpat(self, interaction: discord.Interaction, user: discord.User, amount: int):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        setCooldown(interaction.user, "message-ping", 10)
        await interaction.response.defer()
        amount = abs(amount) # stay positive!
        if interaction.user == user:
            await interaction.edit_original_response(content=f"You gave yourself {str(amount)} headpats!")
            return
        await interaction.edit_original_response(content=f"You gave {user.mention} {str(amount)} headpats!")

    @app_commands.command(name="etanbot-sleep", description="Use this for when someone doesn't want to sleep but should!")
    @app_commands.describe(user="The user that should head to sleep", customstring="A custom message, add USER to replace with a mention (required)")
    async def etanbotsleep(self, interaction: discord.Interaction, user: discord.User, customstring: str = None):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        setCooldown(interaction.user, "message-ping", 10)
        await interaction.response.defer()
        if customstring != None:
            if "USER" in customstring:
                await interaction.edit_original_response(content=f"{customstring.replace('USER', user.mention)}\n-# A custom string from {interaction.user.mention} was provided.")
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

    @app_commands.command(name="etanbot-lock-in", description="Tell someone to lock in!")
    @app_commands.describe(user="The user that should lock in", customstring="A custom message, add USER to replace with a mention (required)")
    async def etanbotlockin(self, interaction: discord.Interaction, user: discord.User, customstring: str = None):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        setCooldown(interaction.user, "message-ping", 10)
        await interaction.response.defer()
        if customstring != None:
            if "USER" in customstring:
                await interaction.edit_original_response(content=f"{customstring.replace('USER', user.mention)}\n-# A custom string from {interaction.user.mention} was provided.")
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

    @app_commands.command(name="etanbot-preview", description="Preview a message before sending it.")
    async def preview(self, interaction: discord.Interaction):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        class previewForm(discord.ui.Modal, title="Preview a message"):
            message = discord.ui.TextInput(label="Message", style=discord.TextStyle.paragraph, placeholder="Enter your message here. Max 1800 characters.", required=True, max_length=1800)

            async def on_submit(self, interaction: discord.Interaction):
                await interaction.response.send_message(f"This is a preview of your message:\n\n{self.message.value}", ephemeral=True)
            
        await interaction.response.send_modal(previewForm())

    @app_commands.command(name="etanbot-pizoelectric", description="[Thing] is turning [something else] into electricity!") # based off the infamous copypasta "Japan is turning footsteps into electricity! ⚡Using piezoelectric tiles, every step you take generates a small amount of energy. Millions of steps together can power LED lights and displays in busy places like Shibuya Station. A brilliant way to create a sustainable and smart city -- turning movement into clean, renewable energy 🌱💡"
    @app_commands.describe(thing="Who is turning something into electricity?", somethingelse="What is being turned into electricity?")
    async def pizoelectric(self, interaction: discord.Interaction, thing: str = None, somethingelse: str = None):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        await interaction.response.defer()
        if thing is None:
            thing = "Japan"
        if somethingelse is None:
            somethingelse = "footsteps"

        await interaction.edit_original_response(content=f"{thing} is turning {somethingelse} into electricity! ⚡Using piezoelectric tiles, every step you take generates a small amount of energy. Millions of steps together can power LED lights and displays in busy places like Shibuya Station. A brilliant way to create a sustainable and smart city -- turning movement into clean, renewable energy 🌱💡")

    @app_commands.command(name="etanbot-tsunderefy", description="Turns a given phrase into a tsundere-style one!")
    @app_commands.describe(text="The text you wish to tsunderefy. Keep it short! (about a sentence)", showoriginal="Whether to show the original in the bot's response (defaults to false)")
    async def tsunderefy(self, interaction: discord.Interaction, text: str, showoriginal: bool = False):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        await interaction.response.defer()

        prefixes = ["Hmph.", "H-hey.", "W-well.", "Ugh."]
        suffixes = [
            "Hmph!", "Baka!", "N-not that I care!", "It's not like I did this for you or anything!",
            "D-don't get the wrong idea!", "S-stupid!", "...b-baka.", "Whatever!"
        ]
        pronoun_stutters = {"i": "I-I", "you": "y-you", "you're": "y-you're", "youre": "y-youre"}
        repeattimes = 3
        punctuation = ".,!?;:"

        words = text.split()

        for i, word in enumerate(words):
            stripped = word.strip(punctuation)
            replacement = pronoun_stutters.get(stripped.lower())
            if replacement:
                words[i] = word.replace(stripped, replacement, 1)

        for _ in range(repeattimes):
            eligible_words = [
                word for word in words
                if (len(word) > 1 and word[0].isalpha() and word[1].isalpha())
                or (len(word) == 1 and word[0].isalpha())
            ]

            if not eligible_words:
                continue

            selectedword = random.choice(eligible_words)
            selectedrandom = words.index(selectedword)
            words[selectedrandom] = f"{selectedword[0]}-{selectedword}"

        finalstring = " ".join(words)

        if finalstring and finalstring[-1] not in punctuation:
            finalstring += "!"
        elif finalstring.endswith("!"):
            finalstring += "!"

        if random.random() < 0.4:
            finalstring = f"{random.choice(prefixes)} {finalstring}"

        finalstring += f" {random.choice(suffixes)}"
        await interaction.edit_original_response(content=f"{finalstring}\n{'-# Original: ' + text if showoriginal else ''}")

    @app_commands.command(name="yumeship", description="Dedicated to Paro")
    async def yumeship(self, yumeship: discord.Interaction):
        if not await handleCommandAccess(yumeship, yumeship.user.id):
            return
        await yumeship.response.defer()
        await yumeship.edit_original_response(content="I hop on the internet as usual I get a notification I am curious so I obviously click on it")

async def setup(bot: commands.Bot):
    await bot.add_cog(messageCog(bot))