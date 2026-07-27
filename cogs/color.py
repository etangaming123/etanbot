import discord
from discord import app_commands
from discord.ext import commands
from io import BytesIO
import re

from PIL import Image, ImageDraw

from common import handleCommandAccess, setCooldown

def clamp(value, minimum=0, maximum=255):
    return max(minimum, min(maximum, value))

def rgb_to_hsl(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    maximum = max(r, g, b)
    minimum = min(r, g, b)
    l = (maximum + minimum) / 2
    if maximum == minimum:
        return 0, 0, round(l * 100)
    d = maximum - minimum
    s = d / (2 - maximum - minimum) if l > 0.5 else d / (maximum + minimum)
    if maximum == r:
        h = ((g - b) / d + (6 if g < b else 0)) / 6
    elif maximum == g:
        h = ((b - r) / d + 2) / 6
    else:
        h = ((r - g) / d + 4) / 6
    return round(h * 360) % 360, round(s * 100), round(l * 100)

def hsl_to_rgb(h, s, l):
    h = (h % 360) / 360.0
    s = s / 100.0
    l = l / 100.0
    if s == 0:
        value = round(l * 255)
        return value, value, value

    def hue_to_rgb(p, q, t):
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    r = round(hue_to_rgb(p, q, h + 1 / 3) * 255)
    g = round(hue_to_rgb(p, q, h) * 255)
    b = round(hue_to_rgb(p, q, h - 1 / 3) * 255)
    return clamp(r), clamp(g), clamp(b)

class ColorCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="etanbot-color-convert", description="Convert a color from hex, rgb, etc. to other formats!")
    @app_commands.describe(color="The color to convert (hex, rgb, hsl, etc.). Should be #ff0000, rgb(255, 0, 0), hsl(0, 100%, 50%)...")
    async def colorConvert(self, interaction: discord.Interaction, color: str):
        if not await handleCommandAccess(interaction, interaction.user.id):
            return
        await interaction.response.defer()
        setCooldown(interaction.user.id, "colorConvert", 5)
        try:
            color_value = color.strip().lower()
            hex_match = re.fullmatch(r"#?([0-9a-f]{6}|[0-9a-f]{3})", color_value)
            rgb_match = re.fullmatch(r"rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)", color_value)
            hsl_match = re.fullmatch(r"hsl\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(\d{1,3})%\s*,\s*(\d{1,3})%\s*\)", color_value)

            if hex_match:
                value = hex_match.group(1)
                if len(value) == 3:
                    value = "".join(char * 2 for char in value)
                r = int(value[0:2], 16)
                g = int(value[2:4], 16)
                b = int(value[4:6], 16)
            elif rgb_match:
                r = clamp(int(rgb_match.group(1)))
                g = clamp(int(rgb_match.group(2)))
                b = clamp(int(rgb_match.group(3)))
            elif hsl_match:
                h = float(hsl_match.group(1))
                s = clamp(int(hsl_match.group(2)), 0, 100)
                l = clamp(int(hsl_match.group(3)), 0, 100)
                r, g, b = hsl_to_rgb(h, s, l)
            else:
                raise ValueError("Unsupported color format")

            hex_color = f"#{r:02X}{g:02X}{b:02X}"
            rgb_color = f"rgb({r}, {g}, {b})"
            h, s, l = rgb_to_hsl(r, g, b)
            hsl_color = f"hsl({h}, {s}%, {l}%)"

            image = Image.new("RGB", (240, 120), (r, g, b))
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, 239, 119), outline=(255 - r, 255 - g, 255 - b), width=3)

            image_bytes = BytesIO()
            image.save(image_bytes, format="PNG")
            image_bytes.seek(0)
            preview_file = discord.File(image_bytes, filename="color_preview.png")

            await interaction.edit_original_response(
                content=f"Color conversion for `{color}`:\n- Hex: `{hex_color}`\n- RGB: `{rgb_color}`\n- HSL: `{hsl_color}`",
                attachments=[preview_file],
            )
        except Exception as e:
            await interaction.edit_original_response(content=f"Error converting color (did you input a valid color?) {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(ColorCog(bot))