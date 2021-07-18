from __future__ import annotations

from src.single_guild_bot import SingleGuildBot as Bot

from abc import ABC, abstractmethod
from enum import Enum, unique
from dataclasses import dataclass, field

import datetime
import random

import discord
from discord.ext import commands
from discord.utils import get

from config import MUTED_ROLE_ID

DEFAULT_PUNISHMENT_UNIT = "minute"
DEFAULT_PUNISHMENT_AMOUNT = 5

UNITS = ["minute", "minutes", "min", "hour", "hours", "day", "days"]
GENERIC_REASONS = [
    "inappropriate behavior",
    "breaking the community guidelines",
    "breaking rules",
]


@unique
class PunishmentID(Enum):
    WARN = "WARN"
    MUTE = "MUTE"
    KICK = "KICK"
    BAN = "BAN"
    PERMABAN = "PERMABAN"


def get_random_reason() -> str:
    return random.choice(GENERIC_REASONS)


def extract_amount_and_unit(argument) -> (int, str, str):
    """A simple input parser to get needed data from a command string"""
    argument = argument.split()

    if argument[0].isnumeric() and argument[1] in UNITS:
        command_amount, command_unit = int(argument[0]), argument[1]
        command_reason = (
            get_random_reason() if len(argument) == 2 else " ".join(argument[2:])
        )

    else:
        command_amount = DEFAULT_PUNISHMENT_AMOUNT
        command_unit = DEFAULT_PUNISHMENT_UNIT
        command_reason = " ".join(argument)

    return command_amount, command_unit, command_reason


def translate_to_datetime(amount: int, unit: str) -> datetime.datetime:
    if unit in ["days", "day"]:
        return datetime.datetime.now() + datetime.timedelta(days=amount)
    elif unit in ["hours", "hour"]:
        return datetime.datetime.now() + datetime.timedelta(hours=amount)
    elif unit in ["minutes", "minute", "min"]:
        return datetime.datetime.now() + datetime.timedelta(minutes=amount)
    else:
        raise TypeError()


@dataclass(frozen=True)
class Punishment(ABC):
    to_punish: discord.Member
    punished_by: discord.Member
    punishment_id: PunishmentID

    action: str
    reason: str = get_random_reason()

    @classmethod
    @abstractmethod
    async def convert(cls, ctx, argument) -> Punishment:
        raise NotImplementedError

    @abstractmethod
    async def punish(self, ctx: commands.Context) -> None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def default(
        cls, to_punish: discord.Member, punished_by: discord.Member
    ) -> Punishment:
        raise NotImplementedError

    @abstractmethod
    def encode_to_mongo(self) -> dict:
        raise NotImplementedError


@dataclass(frozen=True)
class OneTimePunishment(Punishment, ABC):
    def encode_to_mongo(self) -> dict:
        return {
            "registry": {
                "user_id": self.to_punish.id,
                "punishment_id": self.punishment_id.value,
                "reason": self.reason,
                "punished_by": self.punished_by.id,
            }
        }

    @classmethod
    async def convert(cls, ctx: commands.Context, argument) -> OneTimePunishment:
        to_punish = ctx.args[2]
        return cls(
            to_punish=to_punish,
            reason=argument,
            punishment_id=cls.punishment_id,
            action=cls.action,
            punished_by=ctx.author,
        )

    @classmethod
    def default(
        cls, to_punish: discord.Member, punished_by: discord.Member
    ) -> OneTimePunishment:
        return cls(
            to_punish=to_punish,
            punishment_id=cls.punishment_id,
            action=cls.action,
            punished_by=punished_by,
        )


@dataclass(frozen=True)
class TimedPunishment(Punishment, ABC):
    amount: int = DEFAULT_PUNISHMENT_AMOUNT
    unit: str = DEFAULT_PUNISHMENT_UNIT

    created_at: datetime.datetime = datetime.datetime.now()
    expires: datetime.datetime = field(init=False)

    def __post_init__(self):
        object.__setattr__(
            self, "expires", translate_to_datetime(self.amount, self.unit)
        )

    @classmethod
    @abstractmethod
    async def unpunish(cls, user_id: int, bot: Bot) -> None:
        raise NotImplementedError

    @classmethod
    async def convert(cls, ctx: commands.Context, argument) -> TimedPunishment:
        to_punish = ctx.args[2]

        amount, unit, reason = extract_amount_and_unit(argument)
        return cls(
            to_punish=to_punish,
            punishment_id=cls.punishment_id,
            action=cls.action,
            amount=amount,
            unit=unit,
            reason=reason,
            punished_by=ctx.author,
        )

    @classmethod
    def default(
        cls, to_punish: discord.Member, punished_by: discord.Member
    ) -> TimedPunishment:
        return cls(
            to_punish=to_punish,
            punishment_id=cls.punishment_id,
            action=cls.action,
            punished_by=punished_by,
        )

    def encode_to_mongo(self) -> dict:
        return {
            "registry": {
                "user_id": self.to_punish.id,
                "punishment_id": self.punishment_id.value,
                "reason": self.reason,
                "punished_by": self.punished_by.id,
                "duration": f"{self.amount} {self.unit}",
                "expires_at": self.expires,
            },
            "active": {
                "user_id": self.to_punish.id,
                "punishment_id": self.punishment_id.value,
                "expires_at": self.expires,
            },
        }


class WarnPunishment(OneTimePunishment):
    punishment_id = PunishmentID.WARN
    action = "warned"

    async def punish(self, ctx: commands.Context) -> None:
        await ctx.send(
            f"{self.to_punish.mention} you are being warned for breaking the community guidelines."
        )


@dataclass(frozen=True)
class MutePunishment(TimedPunishment):
    punishment_id = PunishmentID.MUTE
    action = "muted"

    async def punish(self, ctx: commands.Context) -> None:
        muted_role = await self.get_muted_role(ctx.guild)

        await self.to_punish.add_roles(muted_role)

    @classmethod
    async def unpunish(cls, user_id: int, bot: Bot) -> None:
        try:
            member = await (await bot.the_guild).fetch_member(user_id)
        except discord.errors.NotFound:
            await bot.admin_log(
                f"Failed to lift punishment\n"
                f"   Error : user <{user_id}> is no longer present in the server"
            )
        else:
            muted_role = await cls.get_muted_role(await bot.the_guild)
            await member.remove_roles(muted_role)

            await bot.admin_log(f"Unpunished user <{user_id}> ({member.display_name})")

    @staticmethod
    async def get_muted_role(guild: discord.Guild) -> discord.Role:
        roles = await guild.fetch_roles()
        return get(roles, id=MUTED_ROLE_ID)


@dataclass(frozen=True)
class KickPunishment(OneTimePunishment):
    punishment_id: PunishmentID = PunishmentID.KICK
    action: str = "kicked"

    async def punish(self, ctx: commands.Context) -> None:
        await self.to_punish.kick()


@dataclass(frozen=True)
class BanPunishment(TimedPunishment):
    punishment_id = PunishmentID.BAN
    action = "banned"

    async def punish(self, ctx: commands.Context) -> None:
        await self.to_punish.ban(reason=self.reason)

    @classmethod
    async def unpunish(cls, user_id: int, bot: Bot) -> None:
        user = await bot.fetch_user(user_id)
        await (await bot.the_guild).unban(user)

        await bot.admin_log(f"Unpunished user <{user_id}> ({user.display_name})")


@dataclass(frozen=True)
class PermaBanPunishment(OneTimePunishment):
    punishment_id = PunishmentID.PERMABAN
    action = "perma banned"

    async def punish(self, ctx: commands.Context) -> None:
        await self.to_punish.ban(reason=self.reason)


timed_punishment_from_id = {
    "MUTE": MutePunishment,
    "BAN": BanPunishment,
}

__all__ = [
    "WarnPunishment",
    "MutePunishment",
    "KickPunishment",
    "BanPunishment",
    "PermaBanPunishment",
    "GENERIC_REASONS",
    "timed_punishment_from_id",
    "Punishment",
    "PunishmentID",
]
