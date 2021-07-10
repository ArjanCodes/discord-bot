import datetime
from typing import Optional

from discord import Member
from discord.ext import commands, tasks

import config
from config import TEST_CHANNEL_ID
from src.cogs.punishments import (
    MutePunishment,
    BanPunishment,
    KickPunishment,
    punished_users,
    PermaBanPunishment,
    GENERIC_REASONS,
)


UNPUNISH_LOOP_DURATION_MINUTES = 5


PRIVILEGED_USERS = [
    config.ADMINISTRATOR_ROLE_ID,
    config.MODERATOR_ROLE_ID,
    config.BOT_MASTER_ROLE_ID,
]


class ServerManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.automatic_unpunish.start()

    @tasks.loop(minutes=UNPUNISH_LOOP_DURATION_MINUTES)
    async def automatic_unpunish(self):
        for punishment in punished_users:
            if punishment.expires < datetime.datetime.now():
                await punishment.unpunish(self.bot)

    @commands.command()
    @commands.has_any_role(*PRIVILEGED_USERS)
    async def kick(
        self, ctx: commands.Context, user: Member, kick: Optional[KickPunishment]
    ):
        await ctx.message.delete()

        if not kick:
            kick = KickPunishment.generic(user)
        await kick.punish(ctx)

        await ctx.channel.send(kick.notify_punishment())

    @commands.command()
    @commands.has_any_role(*PRIVILEGED_USERS)
    async def mute(
        self, ctx: commands.Context, user: Member, *, mute: Optional[MutePunishment]
    ):
        await ctx.message.delete()

        if not mute:
            mute = MutePunishment.generic(user)
        await mute.punish(ctx)

        await ctx.channel.send(mute.notify_punishment())

    @commands.command()
    @commands.has_any_role(*PRIVILEGED_USERS)
    async def warn(self, ctx: commands.Context, user: Member):
        await ctx.message.delete()

        await ctx.send(f"{user.mention} you are being warned, change the way you act.")

    @commands.command()
    @commands.has_any_role(*PRIVILEGED_USERS)
    async def ban(
        self, ctx: commands.Context, user: Member, *, ban: Optional[BanPunishment]
    ):
        await ctx.message.delete()

        if not ban:
            ban = BanPunishment.generic(user)
        await ban.punish(ctx)

        await ctx.channel.send(ban.notify_punishment())

    @commands.command()
    @commands.has_any_role(*PRIVILEGED_USERS)
    async def permaban(
        self, ctx: commands.Context, user: Member, *, ban: Optional[PermaBanPunishment]
    ):
        await ctx.message.delete()

        if not ban:
            ban = PermaBanPunishment.generic(user)
        await ban.punish(ctx)

        await ctx.channel.send(ban.notify_punishment())

    @commands.command()
    @commands.has_any_role(*PRIVILEGED_USERS)
    async def print_generic_reasons(self, ctx: commands.Context):
        channel = await self.bot.fetch_channel(TEST_CHANNEL_ID)
        await channel.send(GENERIC_REASONS)

    @commands.command()
    @commands.has_any_role(*PRIVILEGED_USERS)
    async def add_generic_reason(self, ctx: commands.Context, *, reason: str):
        GENERIC_REASONS.append(reason)

    @commands.command()
    @commands.has_any_role(*PRIVILEGED_USERS)
    async def remove_generic_reason(self, ctx: commands.Context, index: int):
        GENERIC_REASONS.pop(index)

    @commands.command()
    @commands.has_any_role(*PRIVILEGED_USERS)
    async def print_punishments(self, ctx: commands.Context):
        data = "".join(
            [
                f"ID: {index} **{p.to_punish}** + {p.reason} -> {p.expires}\n"
                for index, p in enumerate(punished_users)
            ]
        )
        channel = await self.bot.fetch_channel(TEST_CHANNEL_ID)

        data = data if data else "No punishments in this server :)"
        await channel.send(data)

    @commands.command(aliases=["unpunish"])
    @commands.has_any_role(*PRIVILEGED_USERS)
    async def manual_unpunish(self, ctx: commands.Context, user: Member):
        for punishment in punished_users:
            if punishment.to_punish.id == user.id:
                await punishment.unpunish(self.bot)
