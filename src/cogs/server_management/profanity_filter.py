import string
from typing import Dict

import discord
from discord.ext import commands, menus
from discord.ext.commands import Context

from src.single_guild_bot import SingleGuildBot as Bot
from .management_core import PRIVILEGED_USERS

CONFIRM = "✅"
CANCEL = "❌"

PROFANITY_LIST_PATH = "src/cogs/server_management/profanity_list.txt"


class AddToFilterPrompt(menus.Menu):
    def __init__(self, to_add: set):
        self.result = False
        self.timeout = 30
        super().__init__(timeout=self.timeout, clear_reactions_after=True)

        self.words_to_add = to_add

    async def send_initial_message(
        self, ctx: Context, channel: discord.TextChannel
    ) -> discord.Message:
        embed = discord.Embed(
            color=discord.Color.red(),
            title="Add these words to the profanity filter ?",
            description=self.words_to_add,
        )
        embed.set_footer(
            text=f"fThis message becomes unresponsive after {self.timeout} seconds"
        )

        return await channel.send(embed=embed)

    @menus.button(CONFIRM)
    async def confirmed(self, _: Context) -> None:
        self.result = True
        self.stop()

    @menus.button(CANCEL)
    async def cancelled(self, _: Context) -> None:
        self.result = False
        self.stop()

    async def prompt(self, ctx: Context) -> bool:
        await self.start(ctx, wait=True)
        return self.result


class Prompt:
    @staticmethod
    def words_added(to_add: set) -> str:
        return f"```md\n# Words {to_add} were added to the profanity filter\n```"

    @staticmethod
    def words_removed(to_remove: set) -> str:
        return f"```md\n# Words {to_remove} were removed from the profanity filter\n```"

    @staticmethod
    async def add_to_filer(ctx: Context, to_add: set) -> bool:
        return await AddToFilterPrompt(to_add=to_add).prompt(ctx)

    @staticmethod
    def false_positive(message: str, triggered_words: set) -> discord.Embed:
        headline = (
            f"**Message content:**\n{message}\n"
            f"**Triggered by words**\n{triggered_words}\n\n"
        )
        options = (
            f"To confirm as **false positive**, react with {CONFIRM}\n"
            f"To confirm as **true positive**, react with {CANCEL}\n"
        )

        return discord.Embed(
            description=headline + options,
            title="Possible false positive profanity reported",
            colour=discord.Color.red(),
        )

    @staticmethod
    async def notify_user(
        ctx: Context, triggered_words: set, dm_channel: discord.DMChannel
    ) -> bool:
        embed = discord.Embed(
            title="Profanity Detected",
            description=f"{ctx.author.mention}, please avoid using profanity",
            colour=discord.Color.red(),
        )
        embed.set_thumbnail(url=ctx.author.avatar_url)
        await ctx.channel.send(embed=embed)

        return await ProfanityReport(triggered_words, dm_channel).prompt(ctx)


class ProfanityReport(menus.Menu):
    def __init__(self, triggered_words, dm_channel):
        self.dm_channel = dm_channel
        self.triggered_words = triggered_words

        self.author_avatar_url = None
        self.result = False

        self.timeout = 30

        super().__init__(timeout=self.timeout, clear_reactions_after=True)

    async def send_initial_message(
        self, ctx: Context, channel: discord.DMChannel
    ) -> discord.Message:
        description = (
            f"**Message content:**\n{ctx.message.content}\n"
            f"**Triggered by words**\n{self.triggered_words}\n\n"
            f"Is this a false positive ? React with {CONFIRM}"
        )
        title = "It seems like you used profanity in your message"
        footer_text = f"This message becomes unresponsive after {self.timeout} seconds"

        embed = discord.Embed(
            title=title, description=description, colour=discord.Color.red()
        )
        embed.set_thumbnail(url=ctx.author.avatar_url)
        embed.set_footer(text=footer_text)

        return await channel.send(embed=embed)

    @menus.button(CONFIRM)
    async def on_confirm(self, _: Context) -> None:
        self.result = True
        await self.dm_channel.send(
            "```Message was marked as a possible false positive and will be reviewed by the moderators```"
        )
        self.stop()

    async def prompt(self, ctx: Context) -> bool:
        self.author_avatar_url = ctx.author.avatar_url

        await self.start(ctx, wait=True, channel=self.dm_channel)
        return self.result


class Model:
    filter: set = set()

    def __init__(self):
        self.reload()

    def __len__(self) -> int:
        return len(self.filter)

    def reload(self) -> None:
        with open(PROFANITY_LIST_PATH, "r") as file:
            self.filter = set(line.strip() for line in file)

    def add(self, words: set) -> None:
        to_add = {word for word in words if word not in self.filter}

        if not to_add:
            return

        to_file = "\n".join(to_add) + "\n"
        with open(PROFANITY_LIST_PATH, "a") as file:
            file.write(to_file)

        self.reload()

    def remove(self, words: set) -> None:
        with open(PROFANITY_LIST_PATH, "r") as file_in:
            new_list = [line.strip() for line in file_in if line.strip() not in words]

        with open(PROFANITY_LIST_PATH, "w") as file_out:
            file_out.writelines("\n".join(new_list) + "\n")

        self.reload()

    def contains_profanity(self, message: str) -> bool:
        return bool(self.profane_words(message))

    def profane_words(self, message: str) -> set:
        to_compare = self.prepare_message(message)

        return self.filter.intersection(to_compare)

    @staticmethod
    def prepare_message(msg: str) -> set:
        message = msg.translate(str.maketrans("", "", string.punctuation)).lower()

        return set(message.split())


class ProfanityFilter(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

        self.model = Model()
        self.prompt = Prompt()

        self._false_positives: Dict[int, set] = {}

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self, payload: discord.RawReactionActionEvent
    ) -> None:
        if payload.user_id == self.bot.user.id:
            return
        if payload.message_id in self._false_positives.keys():
            await self.resolve_report(payload.message_id, str(payload.emoji))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.id == self.bot.user.id:
            return

        if message.content.startswith(self.bot.command_prefix):
            return

        if self.model.contains_profanity(message.content):
            await self.handle_profanity(message)

    async def record_report(self, message: str) -> None:
        profanities = self.model.profane_words(message)
        report_content = self.prompt.false_positive(message, profanities)
        report = await self.bot.admin_log(embed=report_content)

        await report.add_reaction(CONFIRM)
        await report.add_reaction(CANCEL)

        self._false_positives[report.id] = profanities

    async def resolve_report(self, report_id: int, reaction: str) -> None:
        if reaction == CONFIRM:
            to_remove = self._false_positives.get(report_id)

            await self.bot.admin_log(
                f"```md\n# Words {to_remove} were removed from the profanity filter\n```"
            )

            self.model.remove(to_remove)
            del self._false_positives[report_id]

        elif reaction == CANCEL:
            del self._false_positives[report_id]

    async def handle_profanity(self, message) -> None:
        await message.delete()

        triggered_words = self.model.profane_words(message.content)

        channel = await message.author.create_dm()
        new_ctx = Context(
            bot=self.bot,
            message=message,
            prefix=self.bot.command_prefix,
            author=message.author,
            channel=channel
        )
        should_report = await self.prompt.notify_user(new_ctx, triggered_words, channel)

        if should_report:
            await self.record_report(message.content)

    @commands.group()
    @commands.has_any_role(*PRIVILEGED_USERS)
    async def profanity(self, ctx: Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.channel.send("```Pass in a subcommand```")

    @profanity.command()
    async def add(self, ctx: Context, *, to_add: str) -> None:
        to_add_set = set(to_add.lower().split())

        should_add = await self.prompt.add_to_filer(ctx, to_add_set)
        if should_add:
            self.model.add(to_add_set)
            await ctx.channel.send(self.prompt.words_added(to_add_set))
        else:
            await ctx.channel.send("```dts\n# Command cancelled\n```")

    @profanity.command()
    async def remove(self, ctx: Context, *, to_remove: str) -> None:
        to_remove: set = set(to_remove.lower().split())

        self.model.remove(to_remove)
        await ctx.send(self.prompt.words_removed(to_remove))

    @profanity.command()
    async def count(self, ctx: Context) -> None:
        await ctx.send(
            f"```The profanity list currently consists of {len(self.model)} blacklisted words```"
        )
