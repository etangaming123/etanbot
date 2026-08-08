import io
import json

import discord
from discord import app_commands
from discord.ext import commands

from common import handleCommandAccess, saveData, loadData, userdatastores, sensitivestores, setCooldown, purgeUserData, ConfirmView

ALLOWED_LINK_PLATFORMS = ("tiktok", "instagram", "twitter", "youtube")
# 2MB — a self-exported file can now include the user's (redacted) gimmick inbox, which counts toward
# upload size even though it's always skipped on import (see NON_IMPORTABLE_STORES below), so a user
# with a lot of pending drawings shouldn't get blocked from re-importing the rest of their data.
MAX_IMPORT_FILE_SIZE = 2097152

# datastores that get exported via /etanbot-list-data but can never be brought back in via /etanbot-import-data
NON_IMPORTABLE_STORES = {
    "gimmickinbox": "gimmicks can't be imported — they're included in your export for reference only",
}

def validate_profiles(value):
    if not isinstance(value, dict):
        return False, "`profiles` entry must be an object."
    if "bio" not in value:
        return False, "`profiles.bio` is required."
    if not isinstance(value["bio"], str):
        return False, "`profiles.bio` must be a string."
    if len(value["bio"]) > 256:
        return False, "`profiles.bio` must be 256 characters or fewer."
    if "links" in value:
        links = value["links"]
        if not isinstance(links, dict):
            return False, "`profiles.links` must be an object."
        for platform, username in links.items():
            if platform not in ALLOWED_LINK_PLATFORMS:
                return False, f"`profiles.links` has unsupported platform `{platform}`."
            if not isinstance(username, str):
                return False, f"`profiles.links.{platform}` must be a string."
    if "color" in value:
        color = value["color"]
        if not isinstance(color, int) or isinstance(color, bool):
            return False, "`profiles.color` must be an integer."
        if not (0 <= color <= 0xFFFFFF):
            return False, "`profiles.color` must be between 0 and 0xFFFFFF."
    return True, None

IMPORT_VALIDATORS = {
    "profiles": validate_profiles,
}

class datamanagement(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="etanbot-list-data", description="Exports everything that etan bot has stored on your user as a .json file!")
    async def listData(self, interaction: discord.Interaction):
        if not await handleCommandAccess(interaction, interaction.user.id, "listdata"):
            return

        await interaction.response.defer(ephemeral=True)
        setCooldown(interaction.user.id, "listdata", 15)
        data = {}

        for item in userdatastores:
            read = loadData(item) # read everything that stores user data
            if read == "":
                data[item] = "[Failed to load]"
            elif item in sensitivestores:
                data[item] = "[Linked - token hidden for security]" if str(interaction.user.id) in read else "[No data stored]"
            else:
                try:
                    data[item] = read[str(interaction.user.id)]
                except Exception:
                    data[item] = "[No data stored]"

        # gimmicks aren't a userdatastore (see common.py) since they can't be re-imported, but we still
        # show the user what's in their inbox — with sender_id always stripped, even for non-anonymous
        # gimmicks, so this export can never be used to unmask who sent something.
        gimmickinbox = loadData("gimmickinbox")
        if not isinstance(gimmickinbox, dict):
            gimmickinbox = {}
        data["gimmickinbox"] = [
            {key: value for key, value in gimmick.items() if key != "sender_id"}
            for gimmick in gimmickinbox.get(str(interaction.user.id), [])
        ]

        payload = json.dumps(data, indent=4).encode("utf-8")
        file = discord.File(io.BytesIO(payload), filename=f"etanbot-data-{interaction.user.id}.json")
        await interaction.edit_original_response(content="Here's everything etan bot has stored on you. You can import the importable sections of this into a new instance of etan bot.\n-# Gimmicks are included for reference and transparency only and can't be re-imported.", attachments=[file])

    @app_commands.command(name="etanbot-import-data", description="Import your data from a previously exported .json file.")
    @app_commands.describe(file="The .json file exported using /etanbot-list-data.")
    async def importData(self, interaction: discord.Interaction, file: discord.Attachment):
        if not await handleCommandAccess(interaction, interaction.user.id, "importdata"):
            return

        await interaction.response.defer(ephemeral=True)

        if file.size > MAX_IMPORT_FILE_SIZE:
            await interaction.edit_original_response(content="That file is too large to be a valid data export.")
            return

        try:
            raw = await file.read()
            parsed = json.loads(raw.decode("utf-8"))
        except Exception:
            await interaction.edit_original_response(content="Couldn't read that file. Make sure it's a valid .json export.")
            return

        if not isinstance(parsed, dict):
            await interaction.edit_original_response(content="Invalid data file: top level must be an object.")
            return

        importable = [store for store in userdatastores if store not in sensitivestores]

        to_write = {}
        skipped = []
        nonimportable = []
        errors = []

        for key, value in parsed.items():
            if key in NON_IMPORTABLE_STORES:
                nonimportable.append(key)
                continue
            if key in sensitivestores:
                skipped.append(key)
                continue
            if value == "[No data stored]":
                skipped.append(key)
                continue
            if key not in importable:
                errors.append(f"Unknown datastore `{key}`.")
                continue
            ok, error = IMPORT_VALIDATORS[key](value)
            if not ok:
                errors.append(error)
                continue
            to_write[key] = value

        if errors:
            errorlist = "\n".join(f"- {error}" for error in errors)
            await interaction.edit_original_response(content=f"Import cancelled, found the following issue(s) with your file:\n{errorlist}")
            return

        if not to_write:
            await interaction.edit_original_response(content="That file didn't contain any importable data.")
            return

        summary = ", ".join(f"`{store}`" for store in to_write)
        skippednote = f"\n\nSkipped (can't be imported, or nothing to import): {', '.join(f'`{store}`' for store in skipped)}" if skipped else ""
        nonimportablenote = "\n\n" + "\n".join(f"Note: {NON_IMPORTABLE_STORES[store]}." for store in nonimportable) if nonimportable else ""
        view = ConfirmView(interaction.user.id)
        await interaction.edit_original_response(content=f"This will **overwrite** your existing data in: {summary}. This cannot be undone.{skippednote}{nonimportablenote}", view=view)
        await view.wait()

        if view.value is not True:
            await interaction.edit_original_response(content="Cancelled." if view.value is False else "Confirmation timed out, cancelled.", view=None)
            return

        setCooldown(interaction.user.id, "importdata", 15)

        succeeded = []
        failed = []
        for store, value in to_write.items():
            data = loadData(store)
            if data == "":
                data = {}
            data[str(interaction.user.id)] = value
            if saveData(store, data):
                succeeded.append(store)
            else:
                failed.append(store)

        resultlines = []
        if succeeded:
            resultlines.append(f"Imported: {', '.join(f'`{store}`' for store in succeeded)}")
        if failed:
            resultlines.append(f"Failed to import: {', '.join(f'`{store}`' for store in failed)}")
        if skipped:
            resultlines.append(f"Skipped (can't be imported): {', '.join(f'`{store}`' for store in skipped)}")
        if nonimportable:
            resultlines.append(f"Ignored (gimmicks can't be imported): {', '.join(f'`{store}`' for store in nonimportable)}")

        await interaction.edit_original_response(content="\n".join(resultlines), view=None)

    @app_commands.command(name="etanbot-delete-data", description="Deletes all your data from etan bot.")
    async def deleteData(self, interaction: discord.Interaction):
        if not await handleCommandAccess(interaction, interaction.user.id, "deletedata"):
            return

        view = ConfirmView(interaction.user.id)
        await interaction.response.send_message(content="Are you sure you want to delete **all** your data from etan bot? This cannot be undone.", view=view, ephemeral=True)
        await view.wait()

        if view.value is not True:
            await interaction.edit_original_response(content="Cancelled." if view.value is False else "Confirmation timed out, cancelled.", view=None)
            return

        setCooldown(interaction.user.id, "deletedata", 15)
        if purgeUserData(interaction.user.id):
            await interaction.edit_original_response(content="All your data has been deleted from etan bot.", view=None)
        else:
            await interaction.edit_original_response(content="An error occurred while deleting your data.", view=None)

async def setup(bot: commands.Bot):
    await bot.add_cog(datamanagement(bot))
