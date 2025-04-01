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
URBAN_DICTIONARY_API = "https://api.urbandictionary.com/v0/define?term={}"

# Debounce time (in seconds) for inline queries
INLINE_QUERY_DEBOUNCE = 0.3

# Cache time (in seconds) for inline query results
INLINE_RESULTS_CACHE_TIME = 86400  # 1 day

# Maximum number of Urban Dictionary results to display
MAX_URBAN_RESULTS = (
    18  # Allowing up to 18 urban results + 2 regular dictionary results = 20 total
)

# Version
VERSION = "1.0.9"
