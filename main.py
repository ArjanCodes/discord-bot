import discord
from discord.ext import commands

import config as env
import src.cogs

PREFIX = "/"
CASE_INSENSITIVE = True

INTENTS = discord.Intents.default()
INTENTS.members = True


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        _cogs = [src.cogs.server_management.ServerManagement(self)]
        for cog in _cogs:
            self.add_cog(cog)

    @property
    async def the_guild(self):
        return await self.fetch_guild(env.GUILD_ID)

    async def on_ready(self):
        print("Bot is online")


bot = Bot(command_prefix=PREFIX, case_insensitive=CASE_INSENSITIVE, intents=INTENTS)

bot.run(env.TOKEN)
