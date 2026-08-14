import typing
import discord
from discord import app_commands
from discord.ext import commands
from common import loadData, saveData, setCooldown, formatUsername, config, handleCommandAccess, hybridReply, hybridDefer, requireDMOnly
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

class Profiles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="etanbot-profile-create", description="Creates a profile for you, viewable using /etanbot-profile!", aliases=["profilecreate"])
    async def create_profile(self, ctx: commands.Context):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx, ephemeral=True)
        profiles = loadData("profiles")
        if str(ctx.author.id) in profiles.keys():
            await handle.edit(content=f"You already have a profile! Use /etanbot-profile to view it.")
            return
        profiles[str(ctx.author.id)] = {
            "bio": "Nothing yet... use /etanbot-profile-edit to edit this! Max 256 characters.",
            "links": {}
        }
        if saveData("profiles", profiles):
            await handle.edit(content=f"Profile created successfully!")
        else:
            await handle.edit(content=f"An error occurred while creating your profile. Please try again later.")

    @commands.hybrid_command(name="etanbot-profile", description="View your profile or someone else's!", aliases=["profile"])
    @app_commands.describe(user="The user to view the profile of. Defaults to yourself.", viewprivately="Want to make it so only you can see the profile? (defaults to nah)")
    async def viewprofile(self, ctx: commands.Context, user: discord.User = None, viewprivately: bool = False):
        containsatsymbol = ["tiktok", "youtube"] # these platforms require an @ symbol in the url
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx, ephemeral=viewprivately)
        if user is None:
            user = ctx.author
        profiles = loadData("profiles")
        if str(user.id) not in profiles:
            await handle.edit(content=f"This user does not have a profile yet! They can create one using /etanbot-profile-create.")
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
        if user.banner:
            embed.set_image(url=user.banner.url)
        await handle.edit(embed=embed)

    @commands.hybrid_command(name="etanbot-profile-edit", description="Edit your profile's bio!", aliases=["profileedit"])
    async def editprofile(self, ctx: commands.Context):
        if not await handleCommandAccess(ctx, ctx.author.id, "editprofile"):
            return
        profiles = loadData("profiles")
        if str(ctx.author.id) not in profiles.keys():
            await hybridReply(ctx, content=f"You don't have a profile yet! Use /etanbot-profile-create to create one.", ephemeral=True)
            return
        setCooldown(ctx.author.id, "editprofile", 10)
        profile = profiles[str(ctx.author.id)]
        if ctx.interaction is None:
            await ctx.reply("This command needs to be used as a slash command (`/etanbot-profile-edit`) because it opens a form.", mention_author=False)
            return
        await ctx.interaction.response.send_modal(ProfileEditModal(profile))

    @commands.hybrid_command(name="etanbot-profile-delete", description="Delete your profile! This cannot be undone.", aliases=["profiledelete"])
    async def deleteprofile(self, ctx: commands.Context):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        handle = await hybridDefer(ctx, ephemeral=True)
        profiles = loadData("profiles")
        if str(ctx.author.id) not in profiles.keys():
            await handle.edit(content=f"You don't have a profile yet! Use /etanbot-profile-create to create one.")
            return
        del profiles[str(ctx.author.id)]
        if saveData("profiles", profiles):
            await handle.edit(content=f"Profile deleted successfully!")
        else:
            await handle.edit(content=f"An error occurred while deleting your profile. Please try again later.")

    @commands.hybrid_command(name="etanbot-profile-color", description="Change the color of your profile embed! (hex code, no #, default is green)", aliases=["profilecolor"])
    @app_commands.describe(color="The hex code of the color you want to set for your profile embed (no #, default is green)")
    async def changeprofilecolor(self, ctx: commands.Context, color: str):
        if not await handleCommandAccess(ctx, ctx.author.id, "changeprofilecolor"):
            return
        handle = await hybridDefer(ctx, ephemeral=True)
        setCooldown(ctx.author.id, "changeprofilecolor", 10)
        profiles = loadData("profiles")
        if str(ctx.author.id) not in profiles.keys():
            await handle.edit(content=f"You don't have a profile yet! Use /etanbot-profile-create to create one.")
            return
        try:
            color = int(color, 16)
        except ValueError:
            await handle.edit(content=f"Invalid color format. Please use a valid hex code (no #).")
            return
        profiles[str(ctx.author.id)]["color"] = color
        if saveData("profiles", profiles):
            await handle.edit(content=f"Profile color updated successfully!")
        else:
            await handle.edit(content=f"An error occurred while updating your profile color. Please try again later.")

    @commands.hybrid_command(name="etanbot-profile-link-add", description="Add a link to your profile! (tiktok, instagram, twitter, more later!)", aliases=["profilelinkadd"])
    @app_commands.describe(platform="Only shows supported platforms for now!", username="Your username/handle on the platform (no urls or @, just the username)")
    async def addprofilelink(self, ctx: commands.Context, platform: typing.Literal["tiktok", "instagram", "twitter", "youtube"], username: str):
        if not await handleCommandAccess(ctx, ctx.author.id, "addprofilelink"):
            return
        handle = await hybridDefer(ctx, ephemeral=True)
        setCooldown(ctx.author.id, "addprofilelink", 10)
        profiles = loadData("profiles")
        if str(ctx.author.id) not in profiles.keys():
            await handle.edit(content=f"You don't have a profile yet! Use /etanbot-profile-create to create one.")
            return
        if not "links" in profiles[str(ctx.author.id)]:
            profiles[str(ctx.author.id)]["links"] = {}
        profiles[str(ctx.author.id)]["links"][platform] = username

        if not saveData("profiles", profiles):
            await handle.edit(content=f"An error occurred while adding the link to your profile. Please try again later.")
            return
        await handle.edit(content=f"Link added successfully!")

    @commands.hybrid_command(name="etanbot-profile-link-remove", description="Remove a link from your profile.", aliases=["profilelinkremove"])
    @app_commands.describe(platform="The platform of the link you want to remove.")
    async def removeprofilelink(self, ctx: commands.Context, platform: typing.Literal["tiktok", "instagram", "twitter", "youtube"]):
        if not await handleCommandAccess(ctx, ctx.author.id, "removeprofilelink"):
            return
        handle = await hybridDefer(ctx, ephemeral=True)
        setCooldown(ctx.author.id, "removeprofilelink", 10)
        profiles = loadData("profiles")
        if str(ctx.author.id) not in profiles.keys():
            await handle.edit(content=f"You don't have a profile yet! Use /etanbot-profile-create to create one.")
            return
        if not "links" in profiles[str(ctx.author.id)] or platform not in profiles[str(ctx.author.id)]["links"]:
            await handle.edit(content=f"You don't have a link for that platform on your profile!")
            return
        del profiles[str(ctx.author.id)]["links"][platform]
        if not saveData("profiles", profiles):
            await handle.edit(content=f"An error occurred while removing the link from your profile. Please try again later.")
            return
        await handle.edit(content=f"Link removed successfully!")

    @commands.hybrid_command(name="z-admin-profile-delete", description="Delete a user's profile.", aliases=["adminprofiledelete"])
    @app_commands.describe(user="The user whose profile you want to delete.", userid="The user ID of the user whose profile you want to delete if you can't specify the user.")
    async def admin_delete_profile(self, ctx: commands.Context, user: discord.User = None, userid: str = None):
        if not await handleCommandAccess(ctx, ctx.author.id):
            return
        if not await requireDMOnly(ctx):
            return
        handle = await hybridDefer(ctx, ephemeral=True)
        if ctx.author.id != int(config["poweruserid"]):
            await handle.edit(content=f"You do not have permission to use this command.")
            return
        if user is None and userid is None:
            await handle.edit(content=f"You must specify either a user or a user ID.")
            return
        if user is not None:
            userid = str(user.id)
        profiles = loadData("profiles")
        if userid not in profiles.keys():
            await handle.edit(content=f"This user does not have a profile!")
            return
        del profiles[userid]
        if saveData("profiles", profiles):
            await handle.edit(content=f"Profile deleted successfully!")
        else:
            await handle.edit(content=f"An error occurred while deleting the profile. Please try again later.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Profiles(bot))
