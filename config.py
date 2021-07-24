import os

from dotenv import load_dotenv
from enum import Enum, unique

load_dotenv()


# Database
DB_CONNECTION_STRING = os.environ.get("DB_CONNECTION_STRING")


# Discord Core
TOKEN = os.environ.get("TOKEN")
GUILD_ID = int(os.environ.get("GUILD_ID"))


class Channels(Enum):
    ADMIN_LOG = int(os.environ.get("ADMIN_LOG_CHANNEL_ID"))
    BOT_TESTING = int(os.environ.get("TEST_CHANNEL_ID"))


@unique
class Roles(Enum):
    ADMINISTRATOR = int(os.environ.get("ADMINISTRATOR_ROLE_ID"))
    MODERATOR = int(os.environ.get("MODERATOR_ROLE_ID"))
    BOT_MASTER = int(os.environ.get("BOT_MASTER_ROLE_ID"))
    BOT_CODER = int(os.environ.get("BOT_CODER_ROLE_ID"))
    MUTED = int(os.environ.get("MUTED_ROLE_ID"))
