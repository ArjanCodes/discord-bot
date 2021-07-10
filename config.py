import os

from dotenv import load_dotenv

load_dotenv()

TEST_CHANNEL_ID = int(os.environ.get("TEST_CHANNEL_ID"))
TOKEN = os.environ.get("TOKEN")
