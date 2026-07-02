import discord  # type: ignore
from discord import app_commands  # type: ignore
from discord.ext import commands  # type: ignore
import re
import traceback

import requests  # type: ignore
from bs4 import BeautifulSoup  # type: ignore

from common import kokocreditdefaulturl, loadData, repositoryurl, saveData, supportserver, checkIfCooldown, setCooldown

def get_koko_balance(token: str):
    try:
        try:
            response = requests.get(f"{kokocreditdefaulturl}{token}")
        except Exception as e:
            print(f"Error sending request to koko amusement: {e}")
            return "ERROR_NET"
        if response.status_code != 200:
            print(f"Error fetching koko balance: Received status code {response.status_code}")
            return "ERROR_NET"
        soup = BeautifulSoup(response.text, 'html.parser')

        labels = ["Cash Balance", "Cash Bonus", "Points"]
        thingo = []
        for label in labels:
            node = soup.find(string=re.compile(r"^\s*" + re.escape(label) + r"\s*$", re.I))
            value = None
            if node:
                parent = node.parent
                nxt = parent.find_next_sibling()
                if nxt and nxt.get_text(strip=True):
                    value = nxt.get_text(strip=True)
                else:
                    nxt_tag = parent.find_next(['td', 'span', 'div'])
                    if nxt_tag:
                        value = nxt_tag.get_text(strip=True)
            if not value:
                m = re.search(re.escape(label) + r"\s*[:\-]?\s*([\d,\.]+)", soup.get_text(), re.I)
                if m:
                    value = m.group(1)

            thingo.append(f"{label}: {value if value else 'Not found'}")
        return "Your koko amusement balance:\n" + "\n".join(thingo)
    except Exception as e:
        print(f"Error fetching koko balance: {e}")
        return "ERROR"

class KokoLinking(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="etanbot-koko-help", description="Need help on linking your Koko Amusement card?")
    async def koko_help(self, interaction: discord.Interaction):
        await interaction.response.defer()
        cooldown = checkIfCooldown(interaction.user.id, "koko_help")
        if cooldown != -1:
            await interaction.edit_original_response(content=f"You can use this command again <t:{cooldown}:R>")
            return
        setCooldown(interaction.user.id, "koko_help", 10)
        things = [
            "To link your Koko Amusement card, you need to get your token from the Koko Amusement website. Here's how you can do it:",
            "1. Scan the QR code on the back of your Koko Amusement card using your phone.",
            f"2. Open the link that appears in your browser. It should look something like this: `{kokocreditdefaulturl}[YourTokenHere]` on your browser's URL address bar.",
            "3. Copy everything that appears after the `?i=` in the URL. This is your token.",
            "4. Use the `/etanbot-koko-link-card` command and paste your token there to link your card to your Discord account!",
            "You're all set! You won't have to do this again, just use /etanbot-koko-balance to check your balance whenever you want.",
            "Rerun the link command if you want to update your card token or if you get an error when checking your balance."
        ]
        await interaction.edit_original_response(content="\n".join(things))

    @app_commands.command(name="etanbot-koko-link-card", description="Link your Koko Amusement card to your discord account to check your balance and transactions!")
    @app_commands.describe(token="/BalanceMobile.aspx?i=[this set of characters]")
    async def link_card(self, interaction: discord.Interaction, token: str):
        await interaction.response.defer(ephemeral=True)
        cooldown = checkIfCooldown(interaction.user.id, "link_card")
        if cooldown != -1:
            await interaction.edit_original_response(content=f"You can use this command again <t:{cooldown}:R>")
            return
        setCooldown(interaction.user.id, "link_card", 15)
        linkedkokocards = loadData("linkedkokocards")
        if linkedkokocards == "":
            await interaction.edit_original_response(content="An error occurred while accessing the database. Please try again later.")
            return
        linkedkokocards[str(interaction.user.id)] = token
        saveData("linkedkokocards", linkedkokocards)
        await interaction.edit_original_response(content="Token linked to your Discord account! Checking balance...")
        thingo = get_koko_balance(token)
        if thingo == "ERROR":
            await interaction.edit_original_response(content=f"An error occurred while fetching your koko amusement balance. Please make sure your token is correct and try again later. If this error persists, please join our [support server](<{supportserver}>) or [report a bug](<{repositoryurl}/issues>).")
            return
        if thingo == "ERROR_NET":
            await interaction.edit_original_response(content=f"An error occurred while sending request. Please try again later. (if issue persists, check the card balance manually, and if it does work, please join our [support server](<{supportserver}>) or [report a bug](<{repositoryurl}/issues>).")
            return
        await interaction.edit_original_response(content=f"Successfully linked koko amusement card! {thingo}\nYou can always rerun this command to update your card!")

    @app_commands.command(name="etanbot-koko-balance", description="Check your koko amusement balance if you have linked your card using /etanbot-koko-link-card!")
    @app_commands.describe(creditcost="Credit cost of an arcade game (e.g. 4 for a $4 game)")
    async def my_koko_balance(self, interaction: discord.Interaction, creditcost: float = None):
        await interaction.response.defer()
        cooldown = checkIfCooldown(interaction.user.id, "my_koko_balance")
        if cooldown != -1:
            await interaction.edit_original_response(content=f"You can use this command again <t:{cooldown}:R>")
            return
        setCooldown(interaction.user.id, "my_koko_balance", 15)
        linkedkokocards = loadData("linkedkokocards")
        if linkedkokocards == "":
            await interaction.edit_original_response(content="An error occurred while accessing the database. Please try again later.")
            return
        token = linkedkokocards.get(str(interaction.user.id))
        if not token:
            await interaction.edit_original_response(content="You have not linked a koko amusement card yet! Use /etanbot-koko-link-card to link your card and check your balance. If you need help, use /etanbot-koko-help for instructions on how to link your card.")
            return
        await interaction.edit_original_response(content="Checking balance...")
        thingo = get_koko_balance(token)
        if thingo == "ERROR":
            await interaction.edit_original_response(content=f"An error occurred while fetching your koko amusement balance. Please make sure your token is correct and try again later. If this error persists, please join our [support server](<{supportserver}>) or [report a bug](<{repositoryurl}/issues>).")
            return
        if thingo == "ERROR_NET":
            await interaction.edit_original_response(content=f"An error occurred while sending request. Please try again later. (if issue persists, check the card balance manually, and if it does work, please join our [support server](<{supportserver}>) or [report a bug](<{repositoryurl}/issues>).)")
            return
        if creditcost is not None:
            totalbalance = 0
            for line in thingo.splitlines():
                if line.startswith("Cash Balance:"):
                    balance_str = line.split(":", 1)[1].strip().replace(",", "")
                    try:
                        balance = float(balance_str[2:])
                        totalbalance += balance
                    except ValueError:
                        pass
                elif line.startswith("Cash Bonus:"):
                    balance_str = line.split(":", 1)[1].strip().replace(",", "")
                    try:
                        balance = float(balance_str[2:])
                        totalbalance += balance
                    except ValueError:
                        pass
            thingo += f"\nYou have approximately {totalbalance / creditcost:.2f} credits, if a credit is worth ${creditcost:.2f}." if creditcost > 0 else "\nInvalid credit cost provided, cannot calculate credits."
        await interaction.edit_original_response(content=thingo)

    @app_commands.command(name="etanbot-koko-unlink-card", description="Unlink your koko amusement card from your discord account.")
    async def unlink_card(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        linkedkokocards = loadData("linkedkokocards")
        if linkedkokocards == "":
            await interaction.edit_original_response(content=f"An error occurred while accessing the database. Please try again later.")
            return
        if str(interaction.user.id) in linkedkokocards:
            del linkedkokocards[str(interaction.user.id)]
            saveData("linkedkokocards", linkedkokocards)
            await interaction.edit_original_response(content="Successfully unlinked your koko amusement card.")
        else:
            await interaction.edit_original_response(content="You do not have a koko amusement card linked.")


async def setup(bot: commands.Bot):
    await bot.add_cog(KokoLinking(bot))