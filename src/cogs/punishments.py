import datetime
import random
from abc import ABC, abstractmethod

import discord
from discord.ext import commands
from discord.utils import get

from config import TEST_CHANNEL_ID, MUTED_ROLE_ID, GUILD_ID


DEFAULT_PUNISHMENT_UNIT = "minute"
DEFAULT_PUNISHMENT_AMOUNT = 5
UNITS = ["minute", "minutes", "hour", "hours", "day", "days"]

punished_users = []

GENERIC_REASONS = ["bad behavior", "insulting other members", "profanity", "being rude"]


def get_random_reason():
    return random.choice(GENERIC_REASONS)


class Punishment(commands.Converter, ABC):
    to_punish: discord.Member

    @abstractmethod
    async def convert(self, ctx, argument):
        raise NotImplementedError

    @abstractmethod
    async def punish(self, ctx: commands.Context):
        raise NotImplementedError

    @abstractmethod
    def generic(self, to_punish: discord.Member):
        raise NotImplementedError

    @abstractmethod
    def notify_punishment(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def action(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def reason(self) -> str:
        raise NotImplementedError

    @reason.setter
    def reason(self, value):
        self.reason = value


class OneTimePunishment(Punishment, ABC):
    reason = None

    # leaving it here as it might be useful in the future
    async def punish(self, ctx) -> None:
        pass

    @classmethod
    def generic(cls, to_punish: discord.Member):
        instance = cls()

        instance.to_punish = to_punish

        instance.reason = get_random_reason()

        return instance

    async def convert(self, ctx: commands.Context, argument):
        self.reason = argument

        self.to_punish = ctx.args[2]

        return self

    def notify_punishment(self) -> str:
        return f"{self.to_punish.mention} was {self.action} for {self.reason}"


class TimedPunishment(Punishment, ABC):
    amount: int
    unit: str
    expires: datetime.datetime

    reason = None

    @classmethod
    def generic(cls, to_punish: discord.Member):
        instance = cls()

        instance.to_punish = to_punish

        instance.amount = DEFAULT_PUNISHMENT_AMOUNT
        instance.unit = DEFAULT_PUNISHMENT_UNIT
        instance.reason = get_random_reason()

        instance.expires = instance.translate_to_datetime(
            instance.amount, instance.unit
        )

        return instance

    async def convert(self, ctx, argument):
        self.amount, self.unit, self.reason = self.extract_amount_and_unit(argument)

        self.expires = self.translate_to_datetime(self.amount, self.unit)
        self.to_punish = ctx.args[2]

        return self

    async def punish(self, ctx) -> None:
        punished_users.append(self)

    def notify_punishment(self) -> str:
        return f"{self.to_punish.mention} was {self.action} for {self.amount} {self.unit} for {self.reason}"

    async def unpunish(self, bot):
        punished_users.remove(self)

    def notify_unpunishment(self):
        return f"{self.to_punish.mention} has been {self.action} for {self.amount} {self.unit}, welcome back!"

    @staticmethod
    def extract_amount_and_unit(argument):
        argument = argument.split()

        command_reason = " ".join(argument)
        command_amount = DEFAULT_PUNISHMENT_AMOUNT
        command_unit = DEFAULT_PUNISHMENT_UNIT

        if argument[0].isnumeric() and argument[1] in UNITS:
            command_amount, command_unit = int(argument[0]), argument[1]
            command_reason = " ".join(argument[2:])

            if not command_reason:
                command_reason = get_random_reason()

        return command_amount, command_unit, command_reason

    @staticmethod
    def translate_to_datetime(amount, unit):
        if unit in ["days", "day"]:
            return datetime.datetime.now() + datetime.timedelta(days=amount)
        elif unit in ["hours", "hour"]:
            return datetime.datetime.now() + datetime.timedelta(hours=amount)
        elif unit in ["minutes", "minute"]:
            return datetime.datetime.now() + datetime.timedelta(minutes=amount)
        else:
            raise TypeError()


class MutePunishment(TimedPunishment):
    action = "muted"

    async def punish(self, ctx: commands.Context):
        await super().punish(ctx)

        muted_role = await self.get_muted_role(ctx.guild)

        await self.to_punish.add_roles(muted_role)

    async def unpunish(self, bot):
        await super().unpunish(bot)
        muted_role = await self.get_muted_role(await bot.the_guild)

        await self.to_punish.remove_roles(muted_role)

        channel = await bot.fetch_channel(TEST_CHANNEL_ID)
        await channel.send(self.notify_unpunishment())

    @staticmethod
    async def get_muted_role(guild):
        roles = await guild.fetch_roles()
        return get(roles, id=MUTED_ROLE_ID)


class BanPunishment(TimedPunishment):
    action = "banned"

    async def punish(self, ctx):
        await super().punish(ctx)

        await self.to_punish.ban()

    async def unpunish(self, bot):
        await super().unpunish(bot)

        await self.to_punish.unban()

        channel = await bot.fetch_channel(TEST_CHANNEL_ID)
        await channel.send(self.notify_unpunishment())


class KickPunishment(OneTimePunishment):
    action = "kicked"

    async def punish(self, ctx):
        await super().punish(ctx)

        await self.to_punish.kick()


class PermaBanPunishment(OneTimePunishment):
    action = "perma banned"

    async def punish(self, ctx) -> None:
        await super().punish(ctx)

        await self.to_punish.ban()
