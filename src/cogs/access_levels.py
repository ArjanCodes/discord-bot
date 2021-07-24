from config import Roles

ACCESS_LEVEL_1 = [Roles.ADMINISTRATOR.value]
"""Administrator level access"""

ACCESS_LEVEL_2 = [*ACCESS_LEVEL_1, Roles.MODERATOR.value, Roles.BOT_MASTER.value]
"""Moderator level access"""

BOT_ACCESS = [*ACCESS_LEVEL_1, Roles.BOT_MASTER.value, Roles.BOT_CODER.value]
"""Access for testing functionalities of the bot"""
