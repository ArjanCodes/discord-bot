import discord

from src.single_guild_bot import SingleGuildBot
import src.cogs as cogs

from pymongo import MongoClient
import src.collection_handlers as coll

import config as env

PREFIX = "/"
CASE_INSENSITIVE = True


INTENTS = discord.Intents.default()
INTENTS.members = True


class Bot(SingleGuildBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        _client = MongoClient(env.DB_CONNECTION_STRING)
        self._db = _client["bot"]

        _cogs = [
            cogs.ServerManagement(
                self,
                coll.ActivePunishments(self._db),
                coll.PunishmentRegistry(self._db),
            )
        ]
        for cog in _cogs:
            self.add_cog(cog)

    @property
    async def the_guild(self) -> discord.Guild:
        return await self.fetch_guild(env.GUILD_ID)

    async def admin_log(self, payload: str):
        channel: discord.TextChannel = await self.fetch_channel(
            env.ADMIN_LOG_CHANNEL_ID
        )
        await channel.send(payload)

    async def on_ready(self):
        print("Bot is online")
        await self.change_presence(
            activity=discord.Game(name="Being developed by the ArjanCodes community")
        )


bot = Bot(command_prefix=PREFIX, case_insensitive=CASE_INSENSITIVE, intents=INTENTS)

bot.run(env.TOKEN)
