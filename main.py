import json

import disnake
import motor.motor_asyncio as motor

import src.cogs as cogs
import src.collection_handlers as coll
from config import DB_CONNECTION_STRING, GUILD_ID, TOKEN
from src.single_guild_bot import SingleGuildBot

PREFIX = "!"
CASE_INSENSITIVE = True


INTENTS = disnake.Intents.default()
INTENTS.members = True
INTENTS.message_content = True


class Bot(SingleGuildBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        _client = motor.AsyncIOMotorClient(DB_CONNECTION_STRING)
        self._db = motor.AsyncIOMotorDatabase(_client, "statistics")

        _cogs = [
            cogs.Utilities(self),
            cogs.Statistics(self, coll.UserStatCollectionHandler(self._db)),
        ]

        for cog in _cogs:
            self.add_cog(cog)

    @property
    async def the_guild(self) -> disnake.Guild:
        return await self.fetch_guild(GUILD_ID)

    async def on_ready(self):
        print("Bot is online")
        await self.change_presence(
            activity=disnake.Game(name="Being developed by the ArjanCodes community")
        )


bot = Bot(
    command_prefix=PREFIX,
    case_insensitive=CASE_INSENSITIVE,
    intents=INTENTS,
    test_guilds=[GUILD_ID],
)
bot.run(TOKEN)
