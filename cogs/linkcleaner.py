import discord
from discord.ext import commands
from discord import app_commands
import re
import requests

from common import handleCommandAccess, setCooldown, hybridDefer

def cleanLink(url, toremove):
    if toremove == "*": # if toremove is *, remove all parameters from the link
        if "?" not in url:
            return url.split("&")[0] # Tiktok is known to use & instead of ? for their parameters sometimes, so we check for both and split by the one that exists
        return url.split("?")[0]
    cleaned_link = url
    for item in toremove:
        cleaned_link = re.sub(r'([&?])' + re.escape(item) + r'=[^&]*', '', cleaned_link)
    cleaned_link = re.sub(r'[?&]+$', '', cleaned_link) # remove trailing ? or &
    for item in toremove:
        cleaned_link = re.sub(r'([&])' + re.escape(item) + r'=[^&]*', '', cleaned_link) # run again, this time removing & params
    return cleaned_link

def cleanLinkV2(url, whitelist):
    if whitelist is None or len(whitelist) == 0:
        if "?" not in url:
            return url.split("&")[0]  # If no parameters, just return the base URL (Tiktok is known to use & instead of ? for their parameters sometimes, so we check for both and split by the one that exists)
        return url.split("?")[0]  # If no whitelist is provided, remove all parameters
    if "?" not in url:
        return url
    base_url, query_string = url.split("?", 1)
    params = query_string.split("&")
    cleaned_params = []
    for param in params:
        key = param.split("=")[0]
        if key in whitelist:
            cleaned_params.append(param)
    if cleaned_params:
        return f"{base_url}?{'&'.join(cleaned_params)}"
    else:
        return base_url

def cleanTiktokLink(url): # mfw vt.tiktok.com links
    response = requests.get(url) # make a request to the link to get the final URL after tiktok's trackers redirect it
    if response.status_code != 200:
        return f"Couldn't get real video link - status code {response.status_code}."
    actuallink = response.url
    cleaned_link = cleanLink(actuallink, "*")
    return f"We are using a different method to remove trackers from this link, as this tiktok link has embedded trackers: {cleaned_link}"

class linkCleanerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="etanbot-clean-link", description="Remove stinky link trackers.", aliases=["clean"])
    @app_commands.describe(link="The link you want to clean [Valid url with http:// or https://]", additional="Any additional parameters to remove, separated by commas (optional).")
    async def clean_link(self, ctx: commands.Context, link: str, additional: str = None):
        if not await handleCommandAccess(ctx, ctx.author.id, "cleanlink"):
            return
        handle = await hybridDefer(ctx)
        if not (link.startswith("http://") or link.startswith("https://")):
            await handle.edit(content="Please enter a valid URL that starts with http:// or https://")
            return
        if len(link) > 2000:
            await handle.edit(content="There's no way that's a real link. [Please enter a valid URL under 2000 characters.]")
            return
        toremove = ["igsh", "si", "fbclid", "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "is", "mibextid", "gclid", "dclid", "is_from_webapp", "sender_device", "_t", "_r", "t"] # common link trackers to remove
        if additional:
            toremove.extend(additional.split(","))
        cleaned_link = cleanLink(link, toremove)

        if "tiktok.com" in cleaned_link and "vt.tiktok.com" not in cleaned_link: # Fuck you tiktok, we're removing ALL your parameters
            cleaned_link = cleanLink(link, "*")

        if "www.tiktok.com/t/" in cleaned_link: # these are the same as vt links but like you can't get the original video url from a simple http request
            code = cleaned_link.split('www.tiktok.com/t/')[1].split('/')[0] # so we grab the share code
            cleaned_link = f"https://vt.tiktok.com/{code}" # and convert it into something we can grab the original video url from

        if "https://vt.tiktok" in cleaned_link[:17]: # wow tiktok that's slack
            await handle.edit(content=f"vt.tiktok links redirect you to a URL with trackers! Please wait as we get the real URL and clean that...")
            try:
                await handle.edit(content=f"{cleanTiktokLink(cleaned_link)}")
                return
            except Exception as e:
                print(f"Error cleaning link: {e}")
                await handle.edit(content="Something went wrong whilst trying to remove trackers. (Check your URL!)")
                return
        await handle.edit(content=f"Removed stinky link trackers: {cleaned_link}")

    @commands.hybrid_command(name="etanbot-clean-link-v2", description="Remove even more link trackers. May break some links.", aliases=["cleanv2"])
    @app_commands.describe(link="The link you want to clean [Valid url with http:// or https://]", whitelist="Any parameters you want to keep, separated by commas (optional). (overrides default whitelist)")
    async def clean_link_v2(self, ctx: commands.Context, link: str, whitelist: str = None):
        if not await handleCommandAccess(ctx, ctx.author.id, "cleanlink"):
            return
        handle = await hybridDefer(ctx)
        setCooldown(ctx.author.id, "cleanlink", 5)
        if not (link.startswith("http://") or link.startswith("https://")):
            await handle.edit(content="Please enter a valid URL that starts with http:// or https://")
            return
        if len(link) > 2000:
            await handle.edit(content="There's no way that's a real link. [Please enter a valid URL under 2000 characters.]")
            return
        defaultwhitelist = []
        whitelist_list = whitelist.split(",") if whitelist else defaultwhitelist
        if "steamcommunity.com" in link:
            whitelist_list.append("id") # id for sharedfiles
        if "youtube.com" in link or "youtu.be" in link:
            whitelist_list.append("v") # video id
            whitelist_list.append("t") # timestamp
            whitelist_list.append("list") # playlist

        cleaned_link = cleanLinkV2(link, whitelist_list)

        if "www.tiktok.com/t/" in cleaned_link: # these are the same as vt links but like you can't get the original video url from a simple http request
            code = cleaned_link.split('www.tiktok.com/t/')[1].split('/')[0] # so we grab the share code
            cleaned_link = f"https://vt.tiktok.com/{code}" # and convert it into something we can grab the original video url from

        if "https://vt.tiktok" in cleaned_link[:17]: # wow tiktok that's slack
            await handle.edit(content=f"vt.tiktok links redirect you to a URL with trackers! Please wait as we get the real URL and clean that...")
            try:
                await handle.edit(content=f"{cleanTiktokLink(cleaned_link)}")
                return
            except Exception as e:
                print(f"Error cleaning link: {e}")
                await handle.edit(content="Something went wrong whilst trying to remove trackers. (Check your URL!)")
                return

        await handle.edit(content=f"Removed a BUNCH of query parameters: {cleaned_link}")

async def setup(bot: commands.Bot):
    await bot.add_cog(linkCleanerCog(bot))