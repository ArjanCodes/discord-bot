from __future__ import annotations
from typing import Optional

from ..single_guild_bot import SingleGuildBot as Bot

from discord import Member
from discord.ext import commands, tasks
import discord.errors

import config

from .punishments import *

from src.collection_handlers import ActivePunishments, PunishmentRegistry
from bson import ObjectId

UNPUNISH_LOOP_DURATION_MINUTES = 1

PRIVILEGED_USERS = [
    config.ADMINISTRATOR_ROLE_ID,
    config.MODERATOR_ROLE_ID,
    config.BOT_MASTER_ROLE_ID,
]


class PunishmentConverter(commands.Converter):
    async def convert(self, ctx, argument) -> PunishmentID:
        return PunishmentID[argument.upper()]


class ServerManagement(commands.Cog):
    def __init__(
        self, bot: Bot, active: ActivePunishments, registry: PunishmentRegistry
    ):
        self.bot = bot
        self.active = active
        self.registry = registry

        self.lift_punishments.start()

    @tasks.loop(minutes=UNPUNISH_LOOP_DURATION_MINUTES)
    async def lift_punishments(self):
        records = self.active.get_to_deactivate()

        for record in records:
            punishment_type = timed_punishment_from_id.get(record["punishment_id"])
            await punishment_type.unpunish(record["user_id"], self.bot)

        self.active.deactivate()

    async def handle_punishment(self, punishment: Punishment) -> None:
        data = punishment.encode_to_mongo()
        _id = ObjectId()

        to_registry = data.get("registry")
        to_active = data.get("active")

        if to_active is not None:
            self.active.new_punishment(_id, to_active)

        self.registry.new_punishment(_id, to_registry)

        await self.bot.admin_log(
            f"**Punished user** <{punishment.to_punish.id}> ({punishment.to_punish.display_name}) with {punishment.punishment_id.value}\n"
            f"   **Punished by:** {punishment.punished_by.mention}\n"
            f"   **Reason:** {punishment.reason}\n"
            f"   **Punishment registry id:** {_id}"
        )

    @property
    async def muted_role(self) -> discord.Role:
        return (await self.bot.the_guild).get_role(config.MUTED_ROLE_ID)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if self.active.has_active_mute(member.id):
            await member.add_roles(await self.muted_role)

    @commands.command()
    @commands.has_any_role(*PRIVILEGED_USERS)
    async def warn(
        self, ctx: commands.Context, user: Member, *, warn: Optional[WarnPunishment]
    ):
        await ctx.message.delete()

        if not warn:
            warn = WarnPunishment.default(user, ctx.author)
        await self.handle_punishment(warn)

        await warn.punish(ctx)

    @commands.command()
    @commands.has_any_role(*PRIVILEGED_USERS)
    async def mute(
        self, ctx: commands.Context, user: Member, *, mute: Optional[MutePunishment]
    ):
        await ctx.message.delete()

        if not mute:
            mute = MutePunishment.default(user, ctx.author)
        await self.handle_punishment(mute)

        await mute.punish(ctx)

    @commands.command()
    @commands.has_any_role(*PRIVILEGED_USERS)
    async def kick(
        self, ctx: commands.Context, user: Member, *, kick: Optional[KickPunishment]
    ):
        await ctx.message.delete()

        if not kick:
            kick = KickPunishment.default(user, ctx.author)
        await self.handle_punishment(kick)

        await kick.punish(ctx)

    @commands.command()
    @commands.has_any_role(*PRIVILEGED_USERS)
    async def ban(
        self, ctx: commands.Context, user: Member, *, ban: Optional[BanPunishment]
    ):
        await ctx.message.delete()

        if not ban:
            ban = BanPunishment.default(user, ctx.author)
        await self.handle_punishment(ban)

        await ban.punish(ctx)

    @commands.command()
    @commands.has_any_role(*PRIVILEGED_USERS)
    async def permaban(
        self, ctx: commands.Context, user: Member, *, ban: Optional[PermaBanPunishment]
    ):
        await ctx.message.delete()

        if not ban:
            ban = PermaBanPunishment.default(user, ctx.author)
        await self.handle_punishment(ban)

        await ban.punish(ctx)

    @commands.command()
    @commands.has_any_role(*PRIVILEGED_USERS)
    async def active(
        self, ctx: commands.Context, _type: Optional[PunishmentConverter]
    ) -> None:
        if _type is None:
            await ctx.channel.send(self.active.count_total_amount())
        else:
            await ctx.channel.send(self.active.count_type(_type))

    @commands.command()
    @commands.has_any_role(*PRIVILEGED_USERS)
    async def registry(
        self,
        ctx: commands.Context,
        user: Optional[discord.Member],
        _type: Optional[PunishmentConverter],
    ) -> None:
        if _type is None and user is None:
            await ctx.channel.send(self.registry.count_total_amount())
        elif _type is None:
            await ctx.channel.send(self.registry.count_by_user(user.id))
        elif user is None:
            await ctx.channel.send(self.registry.count_type(_type))
        else:
            await ctx.channel.send(self.registry.count_type_by_user(user.id, _type))

    @commands.command()
    @commands.has_any_role(*PRIVILEGED_USERS)
    async def info(self, ctx: commands.Context, registry_id: str) -> None:
        record = self.registry.get_info(registry_id)

        if record is None:
            await ctx.channel.send("No such document was found")
            return

        embed_string = "\n".join(
            [f"**{k}** : {v}" for k, v in record.items() if k != "_id"]
        )
        embed = discord.Embed(
            title=f"Punishment id {registry_id}",
            description=embed_string,
            colour=discord.Color.red(),
        )
        await ctx.channel.send(embed=embed)
