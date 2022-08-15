from abc import ABC, abstractmethod

import disnake
from disnake.ext.commands import Bot


class SingleGuildBot(ABC, Bot):
    @property
    @abstractmethod
    async def the_guild(self) -> disnake.Guild:
        raise NotImplementedError

