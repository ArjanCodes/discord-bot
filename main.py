import json

import discord

from src.custom_help_command import CustomHelpCommand
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
            ),
            cogs.Utilities(self),
        ]
        with open("./src/cogs/helps.json") as file:
            data = json.load(file)
            for cog in _cogs:
                self.load_command_docs(cog, data.get(cog.qualified_name))
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

    @staticmethod
    def load_command_docs(cog, data):
        if data is None:
            return
        else:
            for command in cog.walk_commands():
                command.help = data.get(command.qualified_name)


bot = Bot(
    command_prefix=PREFIX,
    case_insensitive=CASE_INSENSITIVE,
    intents=INTENTS,
    help_command=CustomHelpCommand(),
)

bot.run(env.TOKEN)
