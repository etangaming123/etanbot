import discord
from discord.ext import commands
from discord import app_commands
import random
import typing
from typing import Optional

from common import handleCommandAccess, formatUsername, setCooldown, getDisplay, readTextFile, truncateMessage, hybridDefer

deretypes = readTextFile("deretypes")

class rngCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="etanbot-coinflip", description="Flip a coin!", aliases=["coinflip"])
    @app_commands.describe(choice="The option you're looking for (cosmetic)")
    async def coinflip(self, ctx: commands.Context, choice: Optional[typing.Literal["heads", "tails"]] = None):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx)
        result = random.choice(["Heads", "Tails"])
        if choice == None:
            await handle.edit(content=f"The coin landed on **{result}**!")
        else:
            if choice == result.lower():
                await handle.edit(content=f"You hoped for *{choice}*, and the coin landed on **{result}**!")
            else:
                await handle.edit(content=f"You hoped for *{choice}*, but the coin landed on **{result}**!")


    @commands.hybrid_command(name="etanbot-8ball", description="Ask the magic 8ball a question!", aliases=["8ball"]) # use with caution. its completely random yet can be scarily accurate at times
    @app_commands.describe(question="The question to ask the 8ball. (a yes or no question, and keep it short!)", flavour="The flavour of the 8ball. (optional, defaults to classic)")
    async def eight_ball(self, ctx: commands.Context, question: str, flavour: Optional[typing.Literal["classic", "casual", "tsundere"]] = None):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx)
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
        elif flavour == "classic":
            responses = responses_classic
        elif flavour == "tsundere":
            responses = responses_tsundere
        elif flavour == "casual":
            responses = responses_casual

        if flavour == None:
            await handle.edit(content=f"You asked the classic 8ball \"{question}\"...\nThe 8ball says... {random.choice(responses)}")
            return
        await handle.edit(content=f"You asked the {flavour} 8ball \"{question}\"...\nThe 8ball says... {random.choice(responses)}")

    @commands.hybrid_command(name="etanbot-braincells", description="Check how many braincells you (or someone else) has left. (highest is 1000)", aliases=["braincells"])
    @app_commands.describe(user="The user to check braincells for (defaults to yourself).")
    async def braincells(self, ctx: commands.Context, user: discord.User = None):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx)
        if user is None:
            user = ctx.author
        braincellcount = random.randint(0, 1000)
        await handle.edit(content=f"{formatUsername(user)} has {braincellcount} braincells.")

    @commands.hybrid_command(name="etanbot-randomnumber", description="Generate a random number between a specified range.", aliases=["rand"])
    @app_commands.describe(minimum="The minimum number (inclusive).", maximum="The maximum number (inclusive).")
    async def random_number(self, ctx: commands.Context, minimum: int, maximum: int):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx)
        if minimum > maximum:
            minimum, maximum = maximum, minimum
        number = random.randint(minimum, maximum)
        await handle.edit(content=f"Your random number between {minimum} and {maximum} is: {number}")

    @commands.hybrid_command(name="etanbot-lie-detector", description="Check if someone is lying!", aliases=["lie"])
    @app_commands.describe(user="The user who you think is lying. (Leave blank for yourself!)")
    async def liedetector(self, ctx: commands.Context, user: discord.User = None):
        if user == None:
            user = ctx.author
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx)
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

        if random.randint(0, 1) == 0 and str(self.bot.user.id) != user.id: # the bot never lies.
            await handle.edit(content=random.choice(liestrings).replace("USER", formatUsername(user)))
        else:
            await handle.edit(content=random.choice(truthstrings).replace("USER", formatUsername(user)))

    @commands.hybrid_command(name="etanbot-random-list", description="Picks a random choice in a list!", aliases=["randlist"])
    @app_commands.describe(list="The list of names or otherwise, separated by commas [,] (max 50 characters for each, up to 15 entries)", reroll="The amount of times to reroll", replacement="If rerolling multiple times, whether to make rolling the same item allowed")
    async def randomList(self, ctx: commands.Context, list: str, reroll: int = None, replacement: bool = False):
        if not await handleCommandAccess(ctx, ctx.author.id, "randomlist"):
            return
        handle = await hybridDefer(ctx)
        setCooldown(ctx.author.id, "randomlist", 10)
        try:
            actuallist = list.split(",")
        except Exception:
            await handle.edit(content="That doesn't seem to be a valid list! Please separate your valies with commas. --> `,`")
            return
        if len(actuallist) < 2:
            await handle.edit(content="Your list must have 2 or more entries!")
            return

        if len(actuallist) > 15:
            await handle.edit(content="Your list must have less than 15 entries!")

        for item in actuallist:
            if len(item) > 50:
                await handle.edit(content="One or more items in your list is over 50 characters!")
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
        await handle.edit(content=f"Rolling from `{list}`\nChoices picked: \n`{string}`")

    @commands.hybrid_command(name="etanbot-scan", description="Scan a user for a percentage of how much of something they are!", aliases=["scan"])
    @app_commands.describe(user="The user to scan", scanfor="What to scan for (preferrably in one word, i.e goat, unemployed etc.)")
    async def scanuser(self, ctx: commands.Context, user: discord.User, scanfor: str):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx)
        if len(scanfor) > 100:
            await handle.edit(content="Please keep your `scanfor` field short! Less than 100 characters, please.")
        percentage = random.randint(0, 100)
        await handle.edit(content=f"{formatUsername(user)} is **{str(percentage)}%** `{scanfor}`!")

    @commands.hybrid_command(name="etanbot-ship", description="Ship 2 users with each other!", aliases=["ship"])
    @app_commands.describe(user1="The first user", user2="The second user (defaults to yourself)", method="The RNG method used to ship (defaults to set)")
    async def ship(self, ctx: commands.Context, user1: discord.User, user2: discord.User = None, method: Optional[typing.Literal["set", "setInverse", "random"]] = None):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx)

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
            user2 = ctx.author

        if ctx.author.id == user1.id and ctx.author.id == user2.id:
            await handle.edit(content="You can't ship yourself with yourself!")
            return
        if user1.id == user2.id:
            await handle.edit(content="You can't ship a user with themselves!")
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
        await handle.edit(content=f"Shipping `{formatUsername(user1)}` and `{formatUsername(user2)}`...", embed=embed)

    @commands.hybrid_command(name="etanbot-slop-or-gem", description="Check if something is slop or gem!", aliases=["slopgem"])
    @app_commands.describe(scan="Let's see if this thing is slop or gem!")
    async def slopOrGem(self, ctx: commands.Context, scan: str):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx)
        if len(scan) > 500:
            await handle.edit(content="Your \"scan\" object is WAY too long!")
            return
        randomnumber = random.randint(-100, 100)
        if randomnumber < 0:
            await handle.edit(content=f"`{scan}` is {abs(randomnumber)}% **slop**!")
        else:
            await handle.edit(content=f"`{scan}` is {abs(randomnumber)}% **gem**!")

    @commands.hybrid_command(name="paro", description="paro") # paro
    @app_commands.describe(detailed="Whether to return detailed RNG results (defaults to false).")
    async def paro(self, ctx: commands.Context, detailed: bool = False): # paro
        if not await handleCommandAccess(ctx, ctx.author.id, "paro"):
            return
        handle = await hybridDefer(ctx) # paro
        setCooldown(ctx.author.id, "paro", 1)
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
            await handle.edit(content=f"{extrastring.replace('TEXT', 'Paranoia')}") # Paranoia
        elif randomnumber < 12: # 2-11 (roughly 1 in 100)
            await handle.edit(content=f"{extrastring.replace('TEXT', 'Parousia')}") # Parousia
        elif randomnumber < 113: # 12-112 (roughly 1 in 10)
            await handle.edit(content=f"{extrastring.replace('TEXT', 'Paro')}") # Paro
        else: # the default
            await handle.edit(content=f"{extrastring.replace('TEXT', 'paro')}") # paro

    @commands.hybrid_command(name="testify", description="[ Proceeding will make a decision that you can not reverse. ]") # testify
    @app_commands.describe(detailed="Whether to return detailed RNG results (defaults to false).")
    async def testify(self, ctx: commands.Context, detailed: bool = False): # testify
        if not await handleCommandAccess(ctx, ctx.author.id, "testify"):
            return
        handle = await hybridDefer(ctx) # testify
        setCooldown(ctx.author.id, "testify", 1)
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
            await handle.edit(content=f"{extrastring.replace('TEXT', 'And Testify.')}")
        elif randomnumber < 12: # 2-11 (roughly 1 in 100)
            await handle.edit(content=f"{extrastring.replace('TEXT', 'I’ll end it all...')}")
        elif randomnumber < 113: # 12-112 (roughly 1 in 10)
            await handle.edit(content=f"{extrastring.replace('TEXT', 'Testify')}")
        else: # the default
            await handle.edit(content=f"{extrastring.replace('TEXT', 'testify')}")

    @commands.hybrid_command(name="etanbot-predict", description="[event] will happen [unspecified date/time]", aliases=["predict"])
    @app_commands.describe(event="The event you want to predict.")
    async def predict(self, ctx: commands.Context, event: str):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx)
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
        await handle.edit(content=f"Predicting when \"{event}\" will happen...\n\"{event}\" will happen {random.choice(times)}!")


    @commands.hybrid_command(name="etanbot-random-dere", description="Get a random deretype based on a user!", aliases=["randdere"])
    @app_commands.describe(user="The user to get the random deretype of (defaults to yourself)", method="The method to use for finding deretype (defaults to set)")
    async def randomDere(self, ctx: commands.Context, user: discord.User = None, method: Optional[typing.Literal["set", "random"]] = None):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx)
        if user == None:
            user = ctx.author

        methodreal = ""
        if method == None:
            methodreal = "set"
        else:
            methodreal = method

        if methodreal == "set":
            random.seed(str(user.id)) # make the result consistent for the same user
        else:
            random.seed() # completely random for "random"

        deretype = random.choice(list(deretypes.keys()))
        random.seed() # reset the seed so other random commands aren't affected by this one
        await handle.edit(content=f"{formatUsername(user)}'s a `{deretype}` >> {deretypes[deretype]}\n\n*This result is based on the `{methodreal}` method.*")

async def setup(bot: commands.Bot):
    await bot.add_cog(rngCog(bot))