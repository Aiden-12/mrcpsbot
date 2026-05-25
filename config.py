import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
PREFIX = os.getenv("PREFIX", "!")
GUILD_ID = int(os.getenv("GUILD_ID", 0))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))
# PSD Investigation Settings
PSD_LOG_CHANNEL_ID = 1508532271433383999

# Anti-Raid Settings
JOIN_RATE_LIMIT = 5
JOIN_TIME_WINDOW = 10
NEW_ACCOUNT_AGE = 60 * 60 * 24 * 7  # 7 days