from abc import abstractmethod, ABC
from discord.ext.commands import Bot

import discord


class SingleGuildBot(ABC, Bot):
    @property
    @abstractmethod
    async def the_guild(self) -> discord.Guild:
        raise NotImplementedError

    @abstractmethod
    async def admin_log(
        self, message: str = None, embed: discord.Embed = None
    ) -> discord.Message:
        raise NotImplementedError
