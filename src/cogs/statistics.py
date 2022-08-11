from io import BytesIO
import datetime
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd

from discord import File
from discord.ext.commands import Cog, Context
from discord.ext import commands
import discord
from src.collection_handlers import UserStatCollectionHandler

from src.heatmap import generate_heatmap

from src.single_guild_bot import SingleGuildBot as Bot


class Statistics(Cog):
    def __init__(self, bot: Bot, collection: UserStatCollectionHandler) -> None:
        self.bot = bot
        self.collection = collection

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        await self.collection.insert(message.channel.id, message.author.id)

    async def send_heatmap(self, fig: plt.Figure, ctx: Context) -> None:
        with BytesIO() as buffer:
            fig.savefig(buffer, format="png", bbox_inches="tight", dpi=400)
            buffer.seek(0)
            await ctx.reply(file=File(buffer, filename=f"{ctx.author.id}_activity.png"))

    @commands.command()
    async def get(self, ctx, user_id: int, cmap: Optional[str]) -> None:
        data = await self.collection.find_by_user(user_id)
        if not data:
            await ctx.send(f"No data for user `{user_id}` available")
            return
        series = self.prepare_data(data)
        fig = generate_heatmap(series, cmap)
        await self.send_heatmap(fig, ctx)

    @commands.command()
    async def channel(self, ctx, channel_id: int, cmap: Optional[str] = None):
        data = await self.collection.find_by_channel(channel_id)
        if not data:
            await ctx.send(f"No data for channel `{channel_id}` available")
            return
        series = self.prepare_data(data)
        fig = generate_heatmap(series, cmap)
        await self.send_heatmap(fig, ctx)

    @staticmethod
    def prepare_data(data) -> pd.Series:
        # range is fixed to one year for now
        end = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - datetime.timedelta(days=365)
        parsed_data = {e["day"]: e["total"] for e in data}

        data = pd.Series(parsed_data)
        data.index = pd.DatetimeIndex(data.index)

        idx = pd.date_range(start, end)
        return data.reindex(idx, fill_value=0)
