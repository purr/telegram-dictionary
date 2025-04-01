# Telegram Dictionary Bot 📚

This bot provides dictionary definitions for words directly in Telegram chats using inline queries.

## Features

- Fast inline query lookups for word definitions
- Multiple dictionary sources (Primary API, WordNet, Urban Dictionary)
- Detailed word information including:
  - Definitions
  - Examples
  - Synonyms and antonyms
  - Pronunciations
  - Audio links where available
- Fallback to WordNet when words aren't found in the primary API
- Urban Dictionary results for slang and colloquial meanings

## Requirements

- Python 3.7+
- NLTK with WordNet corpus
- Aiogram 3.x
- Requests

## NLTK Data Setup

This bot uses NLTK's WordNet corpus as a fallback dictionary. You need to download the WordNet data before running the bot:

```python
import nltk
nltk.download('wordnet')
```

You can run this in a Python interpreter, or add it to a setup script. The data is downloaded once and stored locally.

## Configuration

Create a `.env` file in the root directory with the following variables:

```
BOT_TOKEN=your_telegram_bot_token
```

## Installation

1. Clone this repository
2. Install requirements: `pip install -r requirements.txt`
3. Download NLTK data: `python -c "import nltk; nltk.download('wordnet')"`
4. Create a `.env` file with your Telegram bot token
5. Run the bot: `python run.py`

## Usage

In any Telegram chat, type `@YourBotUsername word` to look up definitions for "word".

The bot will display:

1. Dictionary definition (if available)
2. Detailed information (if significantly different from basic definition)
3. Urban Dictionary results (if available)

## How It Works

1. The bot monitors inline queries sent to it 📡
2. When a user types `@your_bot_name` followed by a word, it triggers an inline query
3. The bot waits for the user to finish typing (using a debounce technique) ⌨️
4. It then looks up the word in the Free Dictionary API 🔎
5. If a definition is found, it formats and returns it as an inline result ✅
6. If no definition is found in the primary dictionary, it falls back to WordNet 📚
7. If found in WordNet, it displays multiple definitions with synonyms and examples
8. If no definition is found in any dictionary, it notifies the user ❌

## Project Structure

- `bot.py`: Main bot implementation using aiogram
- `dictionary_service.py`: Service for dictionary lookups and formatting
- `config.py`: Configuration settings
- `run.py`: Script to run the bot with dependency checking
- `requirements.txt`: List of required Python packages
- `.env.example`: Example environment variables file

## License

This project is licensed under the MIT License - see the LICENSE file for details. 📜

## Acknowledgements

- [Free Dictionary API](https://dictionaryapi.dev/) for providing free dictionary data
- [NLTK WordNet](https://www.nltk.org/howto/wordnet.html) for comprehensive lexical database
- [aiogram](https://docs.aiogram.dev/) for the Telegram Bot framework

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 🤝
