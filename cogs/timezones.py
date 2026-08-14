import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, time as datetime_time, timedelta, timezone
import re

from common import handleCommandAccess, hybridDefer

class timezonesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _format_timezone_label(self, offset: timedelta) -> str:
        total_seconds = int(offset.total_seconds())
        if total_seconds == 0:
            return "UTC"

        sign = "+" if total_seconds >= 0 else "-"
        total_seconds = abs(total_seconds)
        hours, remainder = divmod(total_seconds, 3600)
        minutes = remainder // 60
        return f"UTC{sign}{hours:02d}:{minutes:02d}"

    def _parse_timezone(self, timezone_value: str) -> tuple[timezone, str]:
        normalized = timezone_value.strip().upper()
        if normalized in {"UTC", "GMT", "Z"}:
            return timezone.utc, "UTC"

        match = re.fullmatch(r"(?:(?:UTC|GMT)\s*)?([+-])\s*(\d{1,2})(?::?(\d{2}))?", normalized)
        if not match:
            raise ValueError("Use UTC offsets like UTC+11, UTC-5, +11, or -05:30.")

        sign, hours_text, minutes_text = match.groups()
        hours = int(hours_text)
        minutes = int(minutes_text) if minutes_text else 0

        if hours > 23 or minutes > 59:
            raise ValueError("Timezone offsets must be within a valid range.")

        offset = timedelta(hours=hours, minutes=minutes)
        if sign == "-":
            offset = -offset

        return timezone(offset), self._format_timezone_label(offset)

    def _parse_time_of_day(self, time_value: str) -> datetime_time:
        normalized = time_value.strip().lower()

        am_pm_match = re.fullmatch(
            r"(\d{1,2})(?::(\d{2}))?(?::(\d{2}))?\s*(am|pm)",
            normalized,
        )
        if am_pm_match:
            hour = int(am_pm_match.group(1))
            minute = int(am_pm_match.group(2) or 0)
            second = int(am_pm_match.group(3) or 0)
            meridiem = am_pm_match.group(4)

            if hour < 1 or hour > 12:
                raise ValueError("12-hour times must use an hour between 1 and 12.")

            if meridiem == "pm" and hour != 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0

            return datetime_time(hour, minute, second)

        twenty_four_hour_match = re.fullmatch(r"(\d{1,2})(?::(\d{2}))?(?::(\d{2}))?", normalized)
        if twenty_four_hour_match:
            hour = int(twenty_four_hour_match.group(1))
            minute = int(twenty_four_hour_match.group(2) or 0)
            second = int(twenty_four_hour_match.group(3) or 0)

            if hour == 25:
                hour = 1 # 25:00 means 1 am (those who know)

            if hour < 0 or hour > 23:
                raise ValueError("24-hour times must use an hour between 0 and 23.")

            return datetime_time(hour, minute, second)

        raise ValueError("Use times like 11:39pm, 11:39 pm, or 23:39.")

    @commands.hybrid_command(name="etanbot-time", description="Get the current time in a specific UTC offset timezone.", aliases=["time"])
    @app_commands.describe(timezone="The timezone offset to use (e.g UTC+11, UTC-5, +11, or -05:30)")
    async def get_time(self, ctx: commands.Context, timezone: str):
        if not await handleCommandAccess(ctx, ctx.author.id, "timezones"):
            return
        handle = await hybridDefer(ctx)
        try:
            timezone_info, timezone_label = self._parse_timezone(timezone)
            current_time = datetime.now(timezone_info)
            await handle.edit(
                content=f"The current time in **{timezone_label}** is `{current_time.strftime('%Y-%m-%d %I:%M:%S %p')}`."
            )
        except Exception as e:
            await handle.edit(content=f"An error occurred while fetching the time for {timezone}: {str(e)}")

    @commands.hybrid_command(name="etanbot-time-convert", description="Convert a time from one UTC offset timezone to another.", aliases=["timeconvert"])
    @app_commands.describe(
        time_value="The time to convert (e.g 11:39pm or 23:39)",
        source_timezone="The timezone the time is in (e.g UTC-5)",
        target_timezone="The timezone to convert the time to (e.g UTC+11)",
    )
    async def convert_time(self, ctx: commands.Context, time_value: str, source_timezone: str, target_timezone: str):
        if not await handleCommandAccess(ctx, ctx.author.id, "timezones"):
            return
        handle = await hybridDefer(ctx)
        try:
            source_tz, source_label = self._parse_timezone(source_timezone)
            target_tz, target_label = self._parse_timezone(target_timezone)
            parsed_time = self._parse_time_of_day(time_value)

            source_now = datetime.now(source_tz)
            source_datetime = datetime(
                source_now.year,
                source_now.month,
                source_now.day,
                parsed_time.hour,
                parsed_time.minute,
                parsed_time.second,
                tzinfo=source_tz,
            )
            target_datetime = source_datetime.astimezone(target_tz)

            await handle.edit(
                content=(
                    f"**{time_value}** in **{source_label}** is `{target_datetime.strftime('%Y-%m-%d %I:%M:%S %p')}` in **{target_label}**.\n-# If today's date is in **{source_label}**."
                )
            )
        except Exception as e:
            await handle.edit(content=f"An error occurred while converting {time_value}: {str(e)}")

async def setup(bot: commands.Bot):
    await bot.add_cog(timezonesCog(bot))