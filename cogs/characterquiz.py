import json
import math
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from common import handleCommandAccess, setCooldown, truncateMessage

QUIZZES_DIR = Path(__file__).resolve().parent.parent / "quizzes"
COOLDOWN_SECONDS = 10
RESULTS_SHOWN = 10


def list_quiz_files() -> list[Path]:
    if not QUIZZES_DIR.exists():
        return []
    return sorted(QUIZZES_DIR.glob("*.json"))


def load_quiz(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or not data.get("questions") or not data.get("characters"):
            return None
        return data
    except Exception as e:
        print(f"Error loading quiz [{path}]: {e}")
        return None


def cosine_similarity(user_vector: dict, profile: dict, attributes: list[str]) -> float:
    va = [float(user_vector.get(attr, 0)) for attr in attributes]
    vb = [float(profile.get(attr, 0)) for attr in attributes]
    dot = sum(x * y for x, y in zip(va, vb))
    norm_a = math.sqrt(sum(x * x for x in va))
    norm_b = math.sqrt(sum(x * x for x in vb))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def score_quiz(quiz: dict, user_vector: dict) -> list[tuple[dict, float]]:
    attributes = quiz.get("attributes", [])
    results = [
        (char, cosine_similarity(user_vector, char.get("profile", {}), attributes) * 100)
        for char in quiz.get("characters", [])
    ]
    results.sort(key=lambda pair: pair[1], reverse=True)
    return results


def build_question_embed(quiz: dict, index: int, total: int) -> discord.Embed:
    question = quiz["questions"][index]
    embed = discord.Embed(
        title=quiz.get("title", "Character Quiz"),
        description=f"**Q{index + 1}/{total}.** {question['text']}",
        color=0x8649D7,
    )
    if index == 0 and quiz.get("description"):
        embed.add_field(name="About this quiz", value=truncateMessage(quiz["description"], 1024), inline=False)
    embed.set_footer(text=f"Question {index + 1} of {total}")
    return embed


def build_results_embed(quiz: dict, results: list[tuple[dict, float]]) -> discord.Embed:
    embed = discord.Embed(title=f"Results: {quiz.get('title', 'Character Quiz')}", color=0x8649D7)
    shown = results[:RESULTS_SHOWN]

    lines = []
    for char, pct in shown:
        bar_length = max(0, min(20, round(pct / 5)))
        bar = "█" * bar_length + "░" * (20 - bar_length)
        lines.append(f"**{char.get('name', char.get('id', '?'))}** — {pct:.1f}%\n`{bar}`")
    embed.description = truncateMessage("\n".join(lines), 4096) if lines else "No characters in this quiz."

    if results:
        top_char, top_pct = results[0]
        embed.add_field(
            name=f"You are most like: {top_char.get('name', '?')} ({top_pct:.1f}% match)",
            value=truncateMessage(top_char.get("description") or "​", 1024),
            inline=False,
        )
        runners_up = [(char, pct) for char, pct in results[1:] if top_pct - pct <= 5 and pct > 0]
        if runners_up:
            names = ", ".join(f"{char.get('name', '?')} ({pct:.1f}%)" for char, pct in runners_up)
            embed.add_field(name="Close runner-up(s)", value=truncateMessage(names, 1024), inline=False)

    remaining = len(results) - len(shown)
    if remaining > 0:
        plural = "s" if remaining != 1 else ""
        embed.set_footer(text=f"...and {remaining} more character{plural} (truncated)")
    return embed


class AnswerButton(discord.ui.Button):
    def __init__(self, label: str, choice: dict, row: int):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, row=row)
        self.choice = choice

    async def callback(self, interaction: discord.Interaction):
        await self.view.answer(interaction, self.choice)


class QuizView(discord.ui.View):
    def __init__(self, quiz: dict, owner_id: int, timeout: float = 240):
        super().__init__(timeout=timeout)
        self.quiz = quiz
        self.owner_id = owner_id
        self.index = 0
        self.user_vector = {attr: 0 for attr in quiz.get("attributes", [])}
        self.message: discord.Message | None = None
        self.add_question_buttons(0)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(content="This quiz isn't yours to answer.", ephemeral=True)
            return False
        return True

    def add_question_buttons(self, index: int):
        self.clear_items()
        question = self.quiz["questions"][index]
        for i, choice in enumerate(question.get("choices", [])[:25]):
            label = truncateMessage(choice.get("text", f"Choice {i + 1}"), 80)
            self.add_item(AnswerButton(label=label, choice=choice, row=i // 5))

    async def answer(self, interaction: discord.Interaction, choice: dict):
        for attr, value in choice.get("points", {}).items():
            self.user_vector[attr] = self.user_vector.get(attr, 0) + value
        self.index += 1

        questions = self.quiz.get("questions", [])
        if self.index < len(questions):
            self.add_question_buttons(self.index)
            embed = build_question_embed(self.quiz, self.index, len(questions))
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            self.clear_items()
            self.stop()
            results = score_quiz(self.quiz, self.user_vector)
            embed = build_results_embed(self.quiz, results)
            await interaction.response.edit_message(embed=embed, view=None)

    async def on_timeout(self):
        if self.message is None:
            return
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        try:
            await self.message.edit(view=self)
        except discord.HTTPException:
            pass


class characterQuizCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="etanbot-character-quiz", description="Take a quiz and find out which character you are!")
    @app_commands.describe(quiz="The quiz to take.", viewprivate="Whether to view the quiz privately or not. (defaults to public)")
    async def character_quiz(self, interaction: discord.Interaction, quiz: str, viewprivate: bool = False):
        if not await handleCommandAccess(interaction, interaction.user.id, "characterquiz"):
            return
        await interaction.response.defer(ephemeral=viewprivate)

        quiz_path = QUIZZES_DIR / f"{quiz}.json"
        quiz_data = load_quiz(quiz_path) if quiz_path.exists() else None
        if quiz_data is None:
            await interaction.edit_original_response(content="Couldn't find that quiz. Please pick one from the autocomplete suggestions.")
            return
        if not quiz_data.get("questions") or not quiz_data.get("characters"):
            await interaction.edit_original_response(content="That quiz doesn't have enough questions/characters to run.")
            return

        setCooldown(interaction.user.id, "characterquiz", COOLDOWN_SECONDS)
        view = QuizView(quiz_data, interaction.user.id)
        embed = build_question_embed(quiz_data, 0, len(quiz_data["questions"]))
        view.message = await interaction.edit_original_response(embed=embed, view=view)

    @character_quiz.autocomplete("quiz")
    async def character_quiz_autocomplete(self, interaction: discord.Interaction, current: str):
        choices = []
        for path in list_quiz_files():
            data = load_quiz(path)
            if data is None:
                continue
            title = data.get("title") or path.stem
            if current.lower() in title.lower() or current.lower() in path.stem.lower():
                choices.append(app_commands.Choice(name=truncateMessage(title, 100), value=path.stem))
        if not choices:
            return [app_commands.Choice(name="No matching quizzes found", value="")]
        return choices[:25]


async def setup(bot: commands.Bot):
    await bot.add_cog(characterQuizCog(bot))
