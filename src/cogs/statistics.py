import datetime
from io import BytesIO
from typing import List, Optional, Union

import disnake
import pandas as pd
from disnake import File
from disnake.ext import commands
from disnake.ext.commands import Cog, CommandError, Context

from src.collection_handlers import StatData, UserStatCollectionHandler
from src.heatmap import generate_heatmap
from src.single_guild_bot import SingleGuildBot as Bot

CMAP = "ref: https://matplotlib.org/stable/tutorials/colors/colormaps.html"

Sendable = Union[disnake.ApplicationCommandInteraction, Context]


class Statistics(Cog):
    def __init__(
        self,
        bot: Bot,
        collection: UserStatCollectionHandler,
    ) -> None:
        self.bot = bot
        self.collection = collection

    async def cog_command_error(
        self,
        ctx: Context,
        error: CommandError,
    ) -> None:
        await ctx.send(str(error))

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        await self.collection.insert(message.channel.id, message.author.id)

    @commands.user_command(name="User activity")
    async def user_stats(self, inter: disnake.ApplicationCommandInteraction) -> None:
        if inter.target is None:
            return

        assert isinstance(inter.target, Union[disnake.User, disnake.Member])
        embed = disnake.Embed()
        if inter.target.avatar is not None:
            embed.set_author(
                name=f"{inter.target.display_name}'s activity",
                icon_url=inter.target.avatar.url,
            )

        data = await self.collection.find_by_user(inter.target.id)
        await self._process_stats(inter, data, embed)

    @commands.command()
    async def user(
        self,
        ctx: Context[Bot],
        user: disnake.User,
        cmap: Optional[str],
    ) -> None:
        embed = disnake.Embed()

        if user.avatar is not None:
            embed.set_author(
                name=f"{user.display_name}'s activity", icon_url=user.avatar.url
            )
        data = await self.collection.find_by_user(user.id)
        await self._process_stats(ctx, data, embed, cmap)

    @commands.command()
    async def channel(
        self,
        ctx: Context,
        channel: disnake.TextChannel,
        cmap: Optional[str] = None,
    ) -> None:
        embed = disnake.Embed(title=f"Activity in {channel.name}")
        data = await self.collection.find_by_channel(channel.id)
        await self._process_stats(ctx, data, embed, cmap)

    @commands.command()
    async def cmap(self, ctx: Context) -> None:
        await ctx.send(CMAP)

    async def _process_stats(
        self,
        sendable: Sendable,
        data: List[StatData],
        embed: disnake.Embed,
        cmap: Optional[str] = None,
    ) -> None:
        if data is None:
            await sendable.send("No data available")
            return

        series = self._prepare_data(data)
        fig = generate_heatmap(series, cmap)
        with BytesIO() as buffer:
            fig.savefig(buffer, format="png", bbox_inches="tight", dpi=400)
            buffer.seek(0)
            embed.set_image(file=File(buffer, "actifity.png"))
            embed.colour = disnake.Color.red()
            await sendable.send(embed=embed)

    @staticmethod
    def _prepare_data(data: List[StatData]) -> pd.Series:
        # range is fixed to one year for now
        end = datetime.datetime.now().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        start = end - datetime.timedelta(days=365)
        parsed_data = {e["day"]: e["total"] for e in data}

        series = pd.Series(parsed_data)
        series.index = pd.DatetimeIndex(series.index)

        idx = pd.date_range(start, end)
        return series.reindex(idx, fill_value=0)
