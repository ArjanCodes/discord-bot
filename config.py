import os

from dotenv import load_dotenv

load_dotenv()


# Database
DB_CONNECTION_STRING = os.environ.get("DB_CONNECTION_STRING")


# Discord Core
TOKEN = os.environ.get("TOKEN")
GUILD_ID = int(os.environ.get("GUILD_ID"))


# Channels
ADMIN_LOG_CHANNEL_ID = int(os.environ.get("ADMIN_LOG_CHANNEL_ID"))
TEST_CHANNEL_ID = int(os.environ.get("TEST_CHANNEL_ID"))


# ROLES
ADMINISTRATOR_ROLE_ID = int(os.environ.get("ADMINISTRATOR_ROLE_ID"))
MODERATOR_ROLE_ID = int(os.environ.get("MODERATOR_ROLE_ID"))
BOT_MASTER_ROLE_ID = int(os.environ.get("BOT_MASTER_ROLE_ID"))
MUTED_ROLE_ID = int(os.environ.get("MUTED_ROLE_ID"))
