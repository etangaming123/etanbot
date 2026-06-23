from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
import os
import discord  # type: ignore
from discord import app_commands  # type: ignore
from discord.ext import commands  # type: ignore
import re
import traceback
import time

from common import setCooldown, checkIfCooldown

def parent_dir(path, levels=1):
    for _ in range(levels):
        path = os.path.dirname(path)
    return path

taskmanagertemplate = os.path.join(parent_dir(__file__, 2), "assets/taskmanager_base.png")
font = ImageFont.truetype(os.path.join(parent_dir(__file__, 2), "assets/PressStart2P-Regular.ttf"), 20)
fontButBigger = ImageFont.truetype(os.path.join(parent_dir(__file__, 2), "assets/PressStart2P-Regular.ttf"), 32)

def generate_task_manager_image(followers, stress, affection, md):
    # Create a new image based on the template
    img = Image.open(taskmanagertemplate)
    draw = ImageDraw.Draw(img)

    # Define positions for each stat
    positions = {
        "Followers": (70, 70),
        "Stress": (75, 140),
        "Affection": (75, 210),
        "MD": (75, 275)
    }

    # Let's draw!
    draw.multiline_text(positions["Followers"], str(followers), fill=(77, 33, 203), font=fontButBigger, align="left")
    if stress >= 80:
        draw.multiline_text(positions["Stress"], str(stress), fill=(216, 72, 85), font=font, align="right")
    else:
        draw.multiline_text(positions["Stress"], str(stress), fill=(77, 33, 203), font=font, align="right")

    draw.multiline_text(positions["Affection"], str(affection), fill=(77, 33, 203), font=font, align="right")

    if md >= 80:
        draw.multiline_text(positions["MD"], str(md), fill=(216, 72, 85), font=font, align="right")
    else:
        draw.multiline_text(positions["MD"], str(md), fill=(77, 33, 203), font=font, align="right")

    # Define the three stat bars on the right side of the template
    bar_positions = {
        "Stress": (228, 115, 350, 167),
        "Affection": (228, 180, 350, 235),
        "MD": (228, 250, 350, 300)
    }

    def draw_fill_bar(bounds, value):
        if value <= 0:
            return  # Don't draw anything for 0 or negative values
        x1, y1, x2, y2 = bounds
        bar_height = y2 - y1
        fill_height = max(1, int(bar_height * max(0, min(value, 100)) / 100))
        fill_top = y2 - fill_height

        # Match the example: a purple container with a cyan fill rising from the bottom.
        draw.rectangle([x1, y1, x2, y2], fill=(211, 180, 239))
        draw.rectangle([x1, fill_top, x2, y2], fill=(108, 178, 204))

    draw_fill_bar(bar_positions["Stress"], stress)
    draw_fill_bar(bar_positions["Affection"], affection)
    draw_fill_bar(bar_positions["MD"], md)

    return img

class NSOTaskManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="etanbot-nso-taskmanager", description="Make a NEEDY STREAMER OVERLOAD based task manager based on your mood!")
    @app_commands.describe(followers="Number of followers", stress="Stress level (0-100)", affection="Affection level (0-100)", md="MD level (0-100)")
    async def nso_taskmanager(self, interaction: discord.Interaction, followers: app_commands.Range[int, 0, 999999999], stress: app_commands.Range[int, 0, 100], affection: app_commands.Range[int, 0, 100], md: app_commands.Range[int, 0, 100]):
        await interaction.response.defer()
        cooldown = checkIfCooldown(interaction.user.id, "nso_taskmanager")
        if cooldown != -1:
            await interaction.edit_original_response(content=f"You can use this command again <t:{cooldown}:R>")
            return
        setCooldown(interaction.user.id, "nso_taskmanager", 10)
        try:
            img = generate_task_manager_image(followers, stress, affection, md)
            with BytesIO() as image_binary:
                img.save(image_binary, 'PNG')
                image_binary.seek(0)
                await interaction.followup.send(file=discord.File(fp=image_binary, filename='taskmanager.png'))
        except Exception as e:
            print(f"Error generating task manager image: {e}")
            traceback.print_exc()
            await interaction.followup.send("Something went wrong while generating your task manager image.")

async def setup(bot: commands.Bot):
    await bot.add_cog(NSOTaskManager(bot))