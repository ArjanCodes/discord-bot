from typing import Optional

import discord
from discord import Member, TextChannel
from discord.ext import commands
from discord.ext.commands import Context, Greedy

from src.cogs.access_levels import ACCESS_LEVEL_2

from ..single_guild_bot import SingleGuildBot as Bot


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
        message: Optional[str] = "Please, move your conversation to the target channel",
    ) -> None:
        await ctx.message.delete()

        users = f"**Users:** {','.join(member.mention for member in members)}"
        target_channel = f"**Target channel:** {channel.mention}"

        embed = discord.Embed(
            title="Request to move discussion",
            description=users + "\n" + target_channel + "\n" + message,
            colour=discord.Colour.red(),
        )

        await ctx.channel.send(embed=embed)
