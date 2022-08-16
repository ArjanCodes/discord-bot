import datetime
from io import BytesIO
from typing import List, Optional

import disnake
import matplotlib.pyplot as plt
import pandas as pd
from disnake import File
from disnake.ext import commands
from disnake.ext.commands import Cog, CommandError, Context

from src.collection_handlers import StatData, UserStatCollectionHandler
from src.heatmap import generate_heatmap
from src.single_guild_bot import SingleGuildBot as Bot


CMAP = "ref: https://matplotlib.org/stable/tutorials/colors/colormaps.html"


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

    async def send_heatmap(self, fig: plt.Figure, ctx: Context) -> None:
        with BytesIO() as buffer:
            fig.savefig(buffer, format="png", bbox_inches="tight", dpi=400)
            buffer.seek(0)
            await ctx.reply(file=File(buffer, f"{ctx.author.id}_activity.png"))

    @commands.command()
    async def user(
        self,
        ctx: Context,
        user: disnake.User,
        cmap: Optional[str],
    ) -> None:
        data = await self.collection.find_by_user(user.id)
        if not data:
            await ctx.send(f"No data for user `{user.id}` available")
            return
        series = self.prepare_data(data)
        fig = generate_heatmap(series, cmap)
        await self.send_heatmap(fig, ctx)

    @commands.command()
    async def channel(
        self,
        ctx: Context,
        channel: disnake.TextChannel,
        cmap: Optional[str] = None,
    ) -> None:
        data = await self.collection.find_by_channel(channel.id)
        if not data:
            await ctx.send(f"No data for channel `{channel.id}` available")
            return
        series = self.prepare_data(data)
        fig = generate_heatmap(series, cmap)
        await self.send_heatmap(fig, ctx)

    @commands.command()
    async def cmap(self, ctx: Context) -> None:
        await ctx.send(CMAP)

    @staticmethod
    def prepare_data(data: List[StatData]) -> pd.Series:
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
