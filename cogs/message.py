import discord
from discord.ext import commands
from discord import app_commands
import random

from common import handleCommandAccess, formatUsername, truncateMessage, setCooldown, config, hybridDefer

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

        
    @commands.hybrid_command(name="etanbot-regional-indicator", description="Turn a sentence into regional indicator emojis!", aliases=["regional"])
    @app_commands.describe(text="The text to turn into emojis, only letters or numbers. Max 90 chars.", copyable="(click to copy on mobile) Whether to make the result copyable (defaults to false).")
    async def regionalIndicators(self, ctx: commands.Context, text: str, copyable: bool = False):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx)
        numbers = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"}
        if len(text) > 90:
            await handle.edit(content="Please keep your text under 90 characters.")
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
                await handle.edit(content="Please only use letters, numbers, and spaces.")
                return
        if copyable:
            await handle.edit(content=f"`{result}`")
        else:
            await handle.edit(content=result)

    @commands.hybrid_command(name="etanbot-read-indicator", description="Show a (barebones) indicator/message that you've read the message(s) in chat!", aliases=["read"])
    async def readIndicator(self, ctx: commands.Context, fakeread: bool = None):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx)
        if fakeread is None:
            fakeread = False
        if fakeread:
            await handle.edit(content=f"⨯ Not read by {formatUsername(ctx.author)}")
        else:
            await handle.edit(content=f"✓ Read by {formatUsername(ctx.author)}")

    @commands.hybrid_command(name="etanbot-birthday", description="Whose birthday is it?", aliases=["birthday"])
    @app_commands.describe(user="The user whose birthday it is (defaults to yourself).")
    async def birthday(self, ctx: commands.Context, user: discord.User = None):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx)
        bdaystrings = [
            "Happy birthday, USER!",
            "Birthday happy, USER!",
            "Happy birthday to USER!",
            "Birthday wishes to USER!",
            "Cake and candles to USER!",
            "Let's celebrate USER's birthday!"
        ]

        if user is None:
            user = ctx.author
        if user == ctx.author:
            await handle.edit(content="Happy birthday to you!!!")
            return
        if user == self.bot.user:
            await handle.edit(content="thanks but i don't think it's my birthday...")
            return
        await handle.edit(content=random.choice(bdaystrings).replace("USER", user.mention))

    @commands.hybrid_command(name="etanbot-shexonmyytilliz", description="she [x] on my [y] till i [z]", aliases=["shex"])
    @app_commands.describe(x="she does what [100 chars]", y="on your what [100 chars]", z="until you what [100 chars]")
    async def shexonmyytilliz(self, ctx: commands.Context, x: str, y: str, z: str):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        if len(x) > 100 or len(y) > 100 or len(z) > 100:
            handle = await hybridDefer(ctx)
            await handle.edit(content="Please keep each input under 100 characters.")
            return
        handle = await hybridDefer(ctx)
        await handle.edit(content=f"she {x} on my {y} till i {z}")


    @commands.hybrid_command(name="etanbot-reference", description="IS THAT A [something] REFERENCE?!", aliases=["reference"])
    @app_commands.describe(reference="The thing being referenced [200 character limit]")
    async def isthatareference(self, ctx: commands.Context, reference: str):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx)
        if len(reference) > 200:
            await handle.edit(content="Please keep the reference under 200 characters.")
            return
        await handle.edit(content=f"IS THAT A {reference} REFERENCE?!")

    @commands.hybrid_command(name="etanbot-headpat", description="Give someone a headpat, or headpats!", aliases=["headpat"]) # dedicated to ruigoonr
    @app_commands.describe(user="The user to give headpats to", amount="The amount of headpats to give.")
    async def headpat(self, ctx: commands.Context, user: discord.User, amount: int):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx)
        amount = abs(amount) # stay positive!
        if ctx.author == user:
            await handle.edit(content=f"You gave yourself {str(amount)} headpats!")
            return
        await handle.edit(content=f"You gave {user.mention} {str(amount)} headpats!")

    @commands.hybrid_command(name="etanbot-sleep", description="Use this for when someone doesn't want to sleep but should!", aliases=["sleep"])
    @app_commands.describe(user="The user that should head to sleep", customstring="A custom message, add USER to replace with a mention (required)")
    async def etanbotsleep(self, ctx: commands.Context, user: discord.User, customstring: str = None):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx)
        if customstring != None:
            if "USER" in customstring:
                await handle.edit(content=customstring.replace("USER", user.mention))
                return
            else:
                await handle.edit(content="You must include the word USER if using a custom string!")
                return
        sleepstrings = [
            "USER, you should head off to sleep now!",
            "It's quite late, USER...",
            "GO TO SLEEP USER!!!",
            "Staying up late isn't good for you USER..."
        ]
        await handle.edit(content=random.choice(sleepstrings).replace("USER", user.mention))

    @commands.hybrid_command(name="etanbot-lock-in", description="Tell someone to lock in!", aliases=["lockin"])
    @app_commands.describe(user="The user that should lock in", customstring="A custom message, add USER to replace with a mention (required)")
    async def etanbotlockin(self, ctx: commands.Context, user: discord.User, customstring: str = None):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx)
        if customstring != None:
            if "USER" in customstring:
                await handle.edit(content=customstring.replace("USER", user.mention))
                return
            else:
                await handle.edit(content="You must include the word USER if using a custom string!")
                return
        lockinstrings = [
            "Lock in USER!!!",
            "Stop getting distracted, USER!!!",
            "You know, you should really do that thing right now USER...",
            "Stop geeking out and lock in USER!!!"
        ]
        await handle.edit(content=random.choice(lockinstrings).replace("USER", user.mention))

    @commands.hybrid_command(name="etanbot-preview", description="Preview a message before sending it.", aliases=["preview"])
    async def preview(self, ctx: commands.Context):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        class previewForm(discord.ui.Modal, title="Preview a message"):
            message = discord.ui.TextInput(label="Message", style=discord.TextStyle.paragraph, placeholder="Enter your message here. Max 1800 characters.", required=True, max_length=1800)

            async def on_submit(self, interaction: discord.Interaction):
                await interaction.response.send_message(f"This is a preview of your message:\n\n{self.message.value}", ephemeral=True)

        if ctx.interaction is None:
            await ctx.reply("This command needs to be used as a slash command (`/etanbot-preview`) because it opens a form.", mention_author=False)
            return
        await ctx.interaction.response.send_modal(previewForm())

    @commands.hybrid_command(name="etanbot-pizoelectric", description="[Thing] is turning [something else] into electricity!", aliases=["pizo"]) # based off the infamous copypasta "Japan is turning footsteps into electricity! ⚡Using piezoelectric tiles, every step you take generates a small amount of energy. Millions of steps together can power LED lights and displays in busy places like Shibuya Station. A brilliant way to create a sustainable and smart city -- turning movement into clean, renewable energy 🌱💡"
    @app_commands.describe(thing="Who is turning something into electricity?", somethingelse="What is being turned into electricity?")
    async def pizoelectric(self, ctx: commands.Context, thing: str = None, somethingelse: str = None):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx)
        if thing is None:
            thing = "Japan"
        if somethingelse is None:
            somethingelse = "footsteps"

        await handle.edit(content=f"{thing} is turning {somethingelse} into electricity! ⚡Using piezoelectric tiles, every step you take generates a small amount of energy. Millions of steps together can power LED lights and displays in busy places like Shibuya Station. A brilliant way to create a sustainable and smart city -- turning movement into clean, renewable energy 🌱💡")

async def setup(bot: commands.Bot):
    await bot.add_cog(messageCog(bot))