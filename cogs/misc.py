import discord
from discord.ext import commands
from discord import app_commands

from common import handleCommandAccess, readTextFile 

deretypes = readTextFile("deretypes")
tonetags = readTextFile("tonetags")

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

class miscCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="etanbot-deretype", description="Get information for a deretype! Most definitions from https://the-dere-types.fandom.com .")
    @app_commands.describe(deretype="The deretype you wish to view information for.", viewprivate="Whether to view the result privately or not. (defaults to public)")
    async def deretype(self, interaction: discord.Interaction, deretype: str, viewprivate: bool = False):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        await interaction.response.defer(ephemeral=viewprivate)
        if deretype in deretypes:
            await interaction.edit_original_response(content=f"`{deretype}` >> {deretypes[deretype]}")
        else:
            await interaction.edit_original_response(content=f"Couldn't find anything for `{deretype}`.")

    @deretype.autocomplete("deretype")
    async def deretype_autocomplete(self, interaction: discord.Interaction, current: str):
        thingtoreturn = [app_commands.Choice(name=key, value=key)
            for key in deretypes.keys()
            if current.lower() in key.lower()
        ][:25]
        if thingtoreturn:
            return thingtoreturn
        else:
            return [app_commands.Choice(name="No matching deretypes found", value="")]

    @app_commands.command(name="etanbot-10d20", description="Makes a link to use Discord's built in dice roller with 10d20 (10 20-sided dice).")
    async def d20(self, interaction: discord.Interaction):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        await interaction.response.defer()
        if interaction.guild_id is None or interaction.channel_id is None:
            await interaction.edit_original_response(content="This command can only be used in a server channel. (The built in roll-dice feature only works in a channel!)")
            return
        await interaction.edit_original_response(content=f"https://discord.com/channels/{interaction.guild_id}/{interaction.channel_id}/roll-dice/10d20")

    @app_commands.command(name="etanbot-tonetag", description="Get information for a tonetag or toneindicator! Most definitions from https://tonetaglist.carrd.co/.")
    @app_commands.describe(tonetag="The tonetag you wish to view information for. (do not include /)", viewprivate="Whether to view the result privately or not. (defaults to public)")
    async def tonetag(self, interaction: discord.Interaction, tonetag: str, viewprivate: bool = False):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        await interaction.response.defer(ephemeral=viewprivate)
        if tonetag in tonetags:
            await interaction.edit_original_response(content=f"`/{tonetag}` >> {tonetags[tonetag]}")
        else:
            await interaction.edit_original_response(content=f"Couldn't find anything for `{tonetag}`.")

    @tonetag.autocomplete("tonetag")
    async def tonetag_autocomplete(self, interaction: discord.Interaction, current: str):
        thingtoreturn = [app_commands.Choice(name=key, value=key)
            for key in tonetags.keys()
            if current.lower() in key.lower()
        ][:25]
        if thingtoreturn:
            return thingtoreturn
        else:
            return [app_commands.Choice(name="No matching tonetags found", value="")]

    @app_commands.command(name="etanbot-mbti", description="Lookup an mbti type/acronym! (ENTP, INTP, INTJ-T, ISFJ-A, etc.)")
    @app_commands.describe(mbti="The mbti type you want to look up (ENTP, INTP, INTJ-T, ISFJ-A, etc.)", viewprivate="Whether to view the result privately or not. (defaults to public)")
    async def mbti(self, interaction: discord.Interaction, mbti: str, viewprivate: bool = False):
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

async def setup(bot: commands.Bot):
    await bot.add_cog(miscCog(bot))