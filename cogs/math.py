import discord
from discord import app_commands
from discord.ext import commands
import ast

from common import checkIfCooldown, setCooldown

units = ["inches", "centimeters", "pounds", "kilograms", "meters", "kilometers", "miles", "feet", "yards", "grams", "ounces", "tons", "liters", "milliliters", "gallons", "quarts", "pints"]

def safe_eval(node): # dude i never knew using eval() was so risky
    if isinstance(node, ast.Expression):
        return safe_eval(node.body)
    if isinstance(node, ast.Constant):
        # Only allow real numeric constants.
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ValueError("Unsupported expression")
        if isinstance(node.value, float) and node.value != node.value:
            raise ValueError("NaN is not supported")
        return node.value
    if isinstance(node, ast.BinOp):
        left = safe_eval(node.left)
        right = safe_eval(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.FloorDiv):
            return left // right
        if isinstance(node.op, ast.Mod):
            return left % right
        if isinstance(node.op, ast.Pow):
            # Restrict exponent size to avoid huge computations.
            if not isinstance(right, (int, float)):
                raise ValueError("Unsupported exponent type")
            if isinstance(right, float) and not right.is_integer():
                raise ValueError("Exponent must be an integer")
            if abs(right) > 20:
                raise ValueError("Exponent too large")
            # Prevent extremely large bases from being exponentiated.
            if abs(left) > 1e12 and right != 0:
                raise ValueError("Base too large")
            return left ** right
        raise ValueError("Unsupported operator")
    if isinstance(node, ast.UnaryOp):
        operand = safe_eval(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise ValueError("Unsupported operator")
    # Reject anything outside the explicitly supported arithmetic AST.
    raise ValueError("Unsupported expression")

class Math(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="etanbot-calculator", description="A simple calculator for basic arithmetic operations.")
    @app_commands.describe(expression="The arithmetic expression to evaluate (e.g., 2 + 2 * 3).")
    async def calculator(self, interaction: discord.Interaction, expression: str):
        await interaction.response.defer()
        cooldown = checkIfCooldown(interaction.user.id, "calculator")
        if cooldown != -1:
            await interaction.edit_original_response(content=f"You can use this command again <t:{cooldown}:R>")
            return
        setCooldown(interaction.user.id, "calculator", 10)
        
        try:
            parsed = ast.parse(expression, mode="eval")
            result = safe_eval(parsed)
            await interaction.edit_original_response(content=f"The result of `{expression}` is: `{result}`")
        except Exception as e:
            await interaction.edit_original_response(content=f"Error evaluating expression: {e}")
    
    @app_commands.command(name="etanbot-math-help", description="Provides help for using the calculator command.")
    async def math_help(self, interaction: discord.Interaction):
        help_message = (
            "To use the calculator, type an arithmetic expression after the command.\n"
            "For example: `/etanbot-calculator expression: 2 + 2 * 3`\n"
            "Supported operations include addition (+), subtraction (-), multiplication (*), and division (/).\n"
            "Please ensure your expression is valid and does not contain any unsupported characters."
        )
        await interaction.response.send_message(help_message, ephemeral=True)

    @app_commands.command(name="etanbot-convert", description="Convert from a unit to another (e.g inches to cm, pounds to kg, etc.)")
    @app_commands.describe(valuereal="The value to convert.", from_unit="The unit to convert from.", to_unit="The unit to convert to.")
    @app_commands.choices(from_unit=[app_commands.Choice(name=unit, value=unit) for unit in units], to_unit=[app_commands.Choice(name=unit, value=unit) for unit in units])
    async def convert(self, interaction: discord.Interaction, valuereal: float, from_unit: discord.app_commands.Choice[str], to_unit: discord.app_commands.Choice[str]):
        await interaction.response.defer()
        cooldown = checkIfCooldown(interaction.user.id, "convert")
        if cooldown != -1:
            await interaction.edit_original_response(content=f"You can use this command again <t:{cooldown}:R>")
            return
        setCooldown(interaction.user.id, "convert", 10)
        
        try:
            # Conversion factors to base units
            length_to_meters = {
                "inches": 0.0254,
                "centimeters": 0.01,
                "meters": 1,
                "kilometers": 1000,
                "miles": 1609.344,
                "feet": 0.3048,
                "yards": 0.9144,
            }
            weight_to_kg = {
                "pounds": 0.453592,
                "kilograms": 1,
                "grams": 0.001,
                "ounces": 0.0283495,
                "tons": 1000,
            }
            fluid_to_liters = {
                "liters": 1,
                "milliliters": 0.001,
                "gallons": 3.78541,
                "quarts": 0.946353,
                "pints": 0.473176,
            }
            temperature_to_celsius = {
                "celsius": 1,
                "fahrenheit": lambda f: (f - 32) * 5/9
            }
            
            from_unit_lower = from_unit.value.lower()
            to_unit_lower = to_unit.value.lower()
            
            # Check if both units are length units
            if from_unit_lower in length_to_meters and to_unit_lower in length_to_meters:
                converted_value = valuereal * length_to_meters[from_unit_lower] / length_to_meters[to_unit_lower]
                await interaction.edit_original_response(content=f"{valuereal} {from_unit_lower} is equal to {converted_value:.2f} {to_unit_lower}.")
            # Check if both units are weight units
            elif from_unit_lower in weight_to_kg and to_unit_lower in weight_to_kg:
                converted_value = valuereal * weight_to_kg[from_unit_lower] / weight_to_kg[to_unit_lower]
                await interaction.edit_original_response(content=f"{valuereal} {from_unit_lower} is equal to {converted_value:.2f} {to_unit_lower}.")
            # Check if both units are fluid units
            elif from_unit_lower in fluid_to_liters and to_unit_lower in fluid_to_liters:
                converted_value = valuereal * fluid_to_liters[from_unit_lower] / fluid_to_liters[to_unit_lower]
                await interaction.edit_original_response(content=f"{valuereal} {from_unit_lower} is equal to {converted_value:.2f} {to_unit_lower}.")
            # Check if both units are temperature units
            elif from_unit_lower in temperature_to_celsius and to_unit_lower in temperature_to_celsius:
                if from_unit_lower == "fahrenheit" and to_unit_lower == "celsius":
                    converted_value = temperature_to_celsius[from_unit_lower](valuereal)
                elif from_unit_lower == "celsius" and to_unit_lower == "fahrenheit":
                    converted_value = valuereal * 9/5 + 32
                await interaction.edit_original_response(content=f"{valuereal} {from_unit_lower} is equal to {converted_value:.2f} {to_unit_lower}.")
            else:
                await interaction.edit_original_response(content=f"Conversion from {from_unit_lower} to {to_unit_lower} is not supported.")
        except Exception as e:
            await interaction.edit_original_response(content=f"Error during conversion: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Math(bot))