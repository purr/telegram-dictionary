#!/usr/bin/env python3
"""
Dictionary Bot Runner
This script starts the Dictionary Bot and handles errors gracefully.
"""

import sys
import asyncio
import logging

from bot import main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


# Check if required NLTK data is available
def check_nltk_data():
    try:
        import nltk
        from nltk.corpus import wordnet

        # Check if WordNet is available by running a simple query
        synsets = wordnet.synsets("test")
        if not synsets:
            logger.warning("WordNet data not found, downloading now...")
            nltk.download("wordnet")
            nltk.download("omw-1.4")
        else:
            logger.info("WordNet data found")
    except ImportError:
        logger.error("NLTK package not installed. Run 'pip install nltk'")
        sys.exit(1)
    except LookupError:
        logger.warning("WordNet data not found, downloading now...")
        nltk.download("wordnet")
        nltk.download("omw-1.4")
    except Exception as e:
        logger.error(f"Error checking WordNet data: {e}")
        sys.exit(1)


if __name__ == "__main__":

    try:
        # Check for required NLTK data
        check_nltk_data()

        # Run the bot
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}", exc_info=True)
        sys.exit(1)
