from __future__ import annotations
from typing import Optional

from src.single_guild_bot import SingleGuildBot as Bot
from src.custom_help_command import CommandWithDocs

from discord import Member
from discord.ext import commands, tasks
from discord.ext.commands import Context
import discord.errors

from src.cogs.access_levels import *

from .punishments import *
from .punishments import WarnPunishment

from src.collection_handlers import ActivePunishments, PunishmentRegistry
import bson


UNPUNISH_LOOP_DURATION_MINUTES = 1


class View:
    def active(self, amounts: dict) -> discord.Embed:
        return discord.Embed.from_dict(
            {"title": "Amount of active punishments"} | self._fields_from_types(amounts)
        )

    def registry(self, amounts: dict) -> discord.Embed:
        return discord.Embed.from_dict(
            {"title": "Amount of punishments"} | self._fields_from_types(amounts)
        )

    def registry_per_member(self, amounts: dict, member: Member) -> discord.Embed:
        embed = discord.Embed.from_dict(
            {"title": f"Amount of punishments for user {member.display_name}"}
            | self._fields_from_types(amounts)
        )
        embed.set_thumbnail(url=member.avatar_url)
        return embed

    @staticmethod
    def _fields_from_types(amounts: dict) -> dict:
        fields = [
            {"name": _type, "value": amount, "inline": True}
            for _type, amount in amounts.items()
        ]

        return {
            "fields": fields,
            "color": discord.Color.red().value,
        }


class ServerManagement(commands.Cog):
    def __init__(
        self, bot: Bot, active: ActivePunishments, registry: PunishmentRegistry
    ):
        self.bot = bot

        self.database_info = View()
        self.registry = registry
        self.active = active

        self.lift_punishments.start()

    @tasks.loop(minutes=UNPUNISH_LOOP_DURATION_MINUTES)
    async def lift_punishments(self):
        records = await self.active.get_to_deactivate()

        async for record in records:
            punishment_type = timed_punishment_from_id.get(record["punishment_id"])
            await punishment_type.unpunish(record["user_id"], self.bot)

        await self.active.deactivate()

    async def record_punishment(self, punishment: Punishment) -> None:
        data = punishment.encode_to_mongo()
        _id = bson.ObjectId()

        to_registry = data.get("registry")
        to_active = data.get("active")

        if to_active is not None:
            await self.active.new_punishment(_id, to_active)

        await self.registry.new_punishment(_id, to_registry)

        await self.bot.admin_log(
            f"**Punished user** <{punishment.to_punish.id}> ({punishment.to_punish.display_name}) with"
            f" {punishment.punishment_id.value}\n"
            f"   **Punished by:** {punishment.punished_by.mention}\n"
            f"   **Reason:** {punishment.reason}\n"
            f"   **Punishment registry id:** {_id}"
        )

    @property
    async def muted_role(self) -> discord.Role:
        return (await self.bot.the_guild).get_role(Roles.MUTED.value)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if await self.active.has_active_mute(member.id):
            await member.add_roles(await self.muted_role)

    @commands.command(cls=CommandWithDocs)
    @commands.has_any_role(*ACCESS_LEVEL_2)
    async def warn(self, ctx: Context, user: Member, *, warn: Optional[WarnPunishment]):
        await ctx.message.delete()

        if not warn:
            warn = WarnPunishment(user, ctx.author)
        await self.record_punishment(warn)

        await warn.punish(ctx)

    @commands.command(cls=CommandWithDocs)
    @commands.has_any_role(*ACCESS_LEVEL_2)
    async def mute(self, ctx: Context, user: Member, *, mute: Optional[MutePunishment]):
        await ctx.message.delete()

        if not mute:
            mute = MutePunishment(user, ctx.author)
        await self.record_punishment(mute)

        await mute.punish(ctx)

    @commands.command(cls=CommandWithDocs)
    @commands.has_any_role(*ACCESS_LEVEL_2)
    async def kick(self, ctx: Context, user: Member, *, kick: Optional[KickPunishment]):
        await ctx.message.delete()

        if not kick:
            kick = KickPunishment(user, ctx.author)
        await self.record_punishment(kick)

        await kick.punish(ctx)

    @commands.command(cls=CommandWithDocs)
    @commands.has_any_role(*ACCESS_LEVEL_2)
    async def ban(self, ctx: Context, user: Member, *, ban: Optional[BanPunishment]):
        await ctx.message.delete()

        if not ban:
            ban = BanPunishment(user, ctx.author)
        await self.record_punishment(ban)

        await ban.punish(ctx)

    @commands.command(cls=CommandWithDocs)
    @commands.has_any_role(*ACCESS_LEVEL_2)
    async def permaban(
        self, ctx: Context, user: Member, *, ban: Optional[PermaBanPunishment]
    ):
        await ctx.message.delete()

        if not ban:
            ban = PermaBanPunishment(user, ctx.author)
        await self.record_punishment(ban)

        await ban.punish(ctx)

    @commands.group(aliases=("pun", "p", "punish"))
    @commands.has_any_role(*ACCESS_LEVEL_2)
    async def punishment(self, ctx: Context) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.channel.send(
                "```Options: /punishment info, /punishment active, /punishment registry``"
            )

    @punishment.command(cls=CommandWithDocs)
    async def info(self, ctx: Context, registry_id: str) -> None:
        try:
            record = await self.registry.get_info(registry_id)
        except bson.errors.InvalidId:
            await ctx.channel.send(f"```dts\n# Invalid Punishment ID\n```")
        else:
            if record is None:
                await ctx.channel.send(f"```dts\n# This document doesn't exist\n```")
            else:
                embed_string = "\n".join(
                    [f"**{k}** : {v}" for k, v in record.items() if k != "_id"]
                )
                embed = discord.Embed(
                    title=f"Punishment id {registry_id}",
                    description=embed_string,
                    colour=discord.Color.red(),
                )
                await ctx.channel.send(embed=embed)

    @punishment.group()
    async def active(self, ctx: Context) -> None:
        if ctx.invoked_subcommand is None:
            amount = await self.active.count_total_amount()
            await ctx.channel.send(f"```\nTotal amount of punishments is {amount}\n```")

    @active.command()
    async def type(self, ctx: Context):
        amounts = await self.active.count_all_types()
        await ctx.send(embed=self.database_info.active(amounts))

    @punishment.group()
    async def registry(self, ctx: Context) -> None:
        if ctx.invoked_subcommand is None:
            amount = await self.registry.count_total_amount()
            await ctx.channel.send(f"```\nTotal amount of punishments is {amount}\n```")

    @registry.command()
    async def user(self, ctx: Context, user: Member):
        amounts = await self.registry.count_all_by_user(user.id)
        await ctx.send(embed=self.database_info.registry_per_member(amounts, user))

    @registry.command(aliases=("type", "types"))
    async def _type(self, ctx: Context):
        amounts = await self.registry.count_all_type()
        await ctx.send(embed=self.database_info.registry(amounts))
