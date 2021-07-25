import discord

from config import GUILD_ID, TOKEN, DB_CONNECTION_STRING, Channels

from src.custom_help_command import CustomHelpCommand, CommandWithDocs
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

        self._db = motor.AsyncIOMotorDatabase(_client, "bot")

        _cogs = [
            cogs.ServerManagement(
                self,
                coll.ActivePunishments(self._db),
                coll.PunishmentRegistry(self._db),
            ),
            cogs.Utilities(self),
            cogs.ProfanityFilter(self, coll.ProfanityListStorage(self._db)),
            cogs.QoL(self),
        ]
        with open("src/cogs/command_docs.json") as file:
            data = json.load(file)
            for cog in _cogs:
                self.load_command_docs(cog, data.get(cog.qualified_name))
                self.add_cog(cog)

    @property
    async def the_guild(self) -> discord.Guild:
        return await self.fetch_guild(GUILD_ID)

    async def admin_log(
        self, message: str = None, embed: discord.Embed = None
    ) -> discord.Message:
        channel: discord.TextChannel = await self.fetch_channel(
            Channels.ADMIN_LOG.value
        )
        return await channel.send(content=message, embed=embed)

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
                if isinstance(command, CommandWithDocs):
                    command.docs = data.get(command.qualified_name)


bot = Bot(
    command_prefix=PREFIX,
    case_insensitive=CASE_INSENSITIVE,
    intents=INTENTS,
    help_command=CustomHelpCommand(),
)

bot.run(TOKEN)
