import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Settings
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found in .env file")

# Dictionary API Configuration
FREE_DICTIONARY_API = "https://api.dictionaryapi.dev/api/v2/entries/en/{}"

# Debounce time (in seconds) for inline queries
INLINE_QUERY_DEBOUNCE = 0.3

# Cache time (in seconds) for inline query results
INLINE_RESULTS_CACHE_TIME = 300  # 5 minutes

# Version
VERSION = "1.0.4"
