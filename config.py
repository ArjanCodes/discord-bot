import os

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get("TOKEN")
GUILD_ID = int(os.environ.get("GUILD_ID"))

# Channels
TEST_CHANNEL_ID = int(os.environ.get("TEST_CHANNEL_ID"))

# Roles
ADMINISTRATOR_ROLE_ID = int(os.environ.get("ADMINISTRATOR_ROLE_ID"))
MODERATOR_ROLE_ID = int(os.environ.get("MODERATOR_ROLE_ID"))
MUTED_ROLE_ID = int(os.environ.get("MUTED_ROLE_ID"))
BOT_MASTER_ROLE_ID = int(os.environ.get("BOT_MASTER_ROLE_ID"))
