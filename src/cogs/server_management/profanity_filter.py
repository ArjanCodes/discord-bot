import asyncio

import discord
from discord.ext import commands

from .management_core import PRIVILEGED_USERS

from src.single_guild_bot import SingleGuildBot as Bot
import re

CONFIRM = "✅"
CANCEL = "❌"


class Cancelled(Exception):
    pass


class MessageToSet(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> set:
        argument = argument.lower()
        quoted = self.extract_quoted_words(argument)

        for word in quoted:
            argument = argument.replace(f'"{word}"', "")

        in_set = set(argument.split())

        return quoted.union(in_set)

    @staticmethod
    def extract_quoted_words(argument: str) -> set:
        return set(re.findall(r"\"(.+?)\"", argument))


class ProfanityFilter(commands.Cog):
    filter: set

    def __init__(self, bot: Bot):
        self.bot = bot

        self.reload_filter_data()

    def reload_filter_data(self):
        with open("src/cogs/server_management/profanity_list.txt") as file:
            self.filter = set(file.read().split(","))

    def add_to_filter(self, words: set):
        to_file = "," + ",".join(words)
        with open("src/cogs/server_management/profanity_list.txt", "a") as file:
            file.write(to_file)

        self.reload_filter_data()

    def has_profanity(self, message: str) -> bool:
        in_lower = message.lower()
        return bool(self.filter.intersection(set(in_lower.split())))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.content.startswith(self.bot.command_prefix):
            return

        if self.has_profanity(message.content):
            await message.channel.send(
                f"{message.author.mention} Please avoid using profanity"
            )
            await message.delete()

    @commands.command()
    @commands.has_any_role(*PRIVILEGED_USERS)
    async def add(self, ctx: commands.Context, *, words_to_add: MessageToSet) -> None:
        embed = discord.Embed(
            color=discord.Color.red(),
            title="Add these words to the profanity filter ?",
            description=words_to_add,
        )
        embed.set_footer(text="This message becomes unresponsive after 30 seconds")

        message = await ctx.channel.send(embed=embed)
        await message.add_reaction(CONFIRM)
        await message.add_reaction(CANCEL)

        def check(payload):
            if payload.message_id != message.id:
                return False

            if payload.user_id == ctx.author.id:
                if str(payload.emoji) == CONFIRM:
                    return True
                if str(payload.emoji) == CANCEL:
                    raise Cancelled()
            else:
                return False

        try:
            await self.bot.wait_for("raw_reaction_add", timeout=30, check=check)
        except Cancelled:
            await ctx.channel.send("```dts\n# Command cancelled\n```")
        except asyncio.TimeoutError:
            await ctx.channel.send("```dts\n# Time ran out\n```")
        else:
            self.add_to_filter(words_to_add)

            await ctx.channel.send(
                f"```md\n# Words {words_to_add} were added to the profanity filter\n```"
            )
