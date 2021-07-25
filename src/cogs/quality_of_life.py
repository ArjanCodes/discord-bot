from typing import Optional

import discord
from discord import Member, TextChannel

from discord.ext import commands
from discord.ext.commands import Greedy, Context

from ..single_guild_bot import SingleGuildBot as Bot

from src.cogs.access_levels import ACCESS_LEVEL_2


class QoL(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.command(aliases=("move_to", "moveto"))
    @commands.has_any_role(*ACCESS_LEVEL_2)
    async def move(
        self,
        ctx: Context,
        members: Greedy[Member],
        channel: TextChannel,
        *,
        message: Optional[str] = "**Please, move your conversation here**"
    ) -> None:
        await ctx.message.delete()

        member_mentions = ",".join(member.mention for member in members)

        await channel.send(member_mentions + "\n" + message)
