from abc import ABC, abstractmethod

import discord
from discord.ext.commands import Bot


class SingleGuildBot(ABC, Bot):
    @property
    @abstractmethod
    async def the_guild(self) -> discord.Guild:
        raise NotImplementedError

