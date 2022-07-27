import discord

from config import GUILD_ID, TOKEN, DB_CONNECTION_STRING, Channels

from src.single_guild_bot import SingleGuildBot
import src.cogs as cogs

import motor.motor_asyncio as motor
import src.collection_handlers as coll

import json


PREFIX = "!"
CASE_INSENSITIVE = True


INTENTS = discord.Intents.default()
INTENTS.members = True


class Bot(SingleGuildBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        _client = motor.AsyncIOMotorClient(DB_CONNECTION_STRING)

        _cogs = [
            cogs.Utilities(self),
        ]

        for cog in _cogs:
            self.add_cog(cog)

    @property
    async def the_guild(self) -> discord.Guild:
        return await self.fetch_guild(GUILD_ID)

    async def on_ready(self):
        print("Bot is online")
        await self.change_presence(
            activity=discord.Game(name="Being developed by the ArjanCodes community")
        )


bot = Bot(
    command_prefix=PREFIX,
    case_insensitive=CASE_INSENSITIVE,
    intents=INTENTS,
)

bot.run(TOKEN)
