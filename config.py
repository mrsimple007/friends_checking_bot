import os
import logging
from datetime import datetime, timezone, timedelta
import asyncio
import json
import uuid
from typing import Dict, List, Optional

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    CallbackQueryHandler, filters, ContextTypes
)

import google.generativeai as genai
from supabase import create_client, Client

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

# Environment variables
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("ACTIVITY_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("ACTIVITY_SUPABASE_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


ADMIN_USERNAME="@Simplelearn_main_admin"
ADMIN_USERNAME_2="@Uzbek\\_europe\\_admin"


CARD_NUMBER = "4073 4200 3711 6443"
ADMIN_CHAT_ID = "8437026582"
NOTIFICATION_ADMIN_IDS = [8437026582]


# # Admin for Instagram verification
# INSTAGRAM_ADMIN_IDS = [7967610894, 
#                        8437026582, 
#                        122290051, 
#                        999932510, 
#                        8126290272]

# Admin for Instagram verification
ADMIN_IDS = [8437026582, 122290051, 999932510]



# Free tier limits
FREE_BIRTHDAY_LIMIT = 50
FREE_TEST_LIMIT = 3

# Premium pricing
PREMIUM_PRICE_MONTHLY = 4.99
PREMIUM_PRICE_YEARLY = 49.99

# Birthday reminder settings
REMINDER_TIME_UTC = "09:00"  # Send reminders at 9 AM UTC
REMINDER_ADVANCE_DAYS = 0  # Days before birthday to send reminder (0 = on the day)

# Test settings
TOTAL_TEST_QUESTIONS = 15
TEST_OPTIONS_PER_QUESTION = 4

# AI settings
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_TEMPERATURE = 0.7
GEMINI_MAX_TOKENS = 1000

# Supported languages
SUPPORTED_LANGUAGES = ['uz', 'ru', 'en']
DEFAULT_LANGUAGE = 'en'

# Bot messages
BOT_NAME = "Birthday & Friendship Bot"
BOT_VERSION = "1.0.0"

# Rate limiting (optional - for future implementation)
MAX_REQUESTS_PER_HOUR = 100
MAX_BIRTHDAYS_PER_DAY = 10

# Database settings
DB_CONNECTION_TIMEOUT = 30
DB_POOL_SIZE = 10

# Cache settings (for future optimization)
CACHE_TTL_SECONDS = 300  # 5 minutes
ENABLE_CACHING = False

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "bot.log"

# Feature flags
ENABLE_ANALYTICS = True
ENABLE_PREMIUM = True
ENABLE_VOICE_MESSAGES = False  # Future feature
ENABLE_GROUP_CHATS = False  # Future feature

# Timezone settings
DEFAULT_TIMEZONE = "UTC"
TIMEZONE_DETECTION_ENABLED = False  # Auto-detect user timezone (future)

# Birthday wish settings
WISH_LENGTH_MIN = 50  # Minimum characters in generated wish
WISH_LENGTH_MAX = 200  # Maximum characters in generated wish

# Test sharing settings
TEST_LINK_EXPIRY_DAYS = 365  # Links expire after 1 year
TEST_MAX_ATTEMPTS_PER_USER = 1  # Users can only take each test once

# Notification settings
NOTIFY_ON_TEST_COMPLETION = True
NOTIFY_TEST_CREATOR = True

# Data retention
DELETE_INACTIVE_TESTS_AFTER_DAYS = 180
DELETE_OLD_ANALYTICS_AFTER_DAYS = 90

