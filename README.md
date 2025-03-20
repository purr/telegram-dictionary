# Telegram Dictionary Bot 📚

A Telegram bot that works in inline mode to lookup definitions of words in public dictionaries.

## Features

- **Inline Mode**: Works in any chat by typing `@your_bot_name` followed by the word to lookup
- **Debounce Implementation**: Waits for the user to finish typing before searching
- **Multiple Dictionaries**: Looks up definitions in public dictionaries (Free Dictionary API and WordNet)
- **API Fallback**: If a word isn't found in the primary dictionary, it falls back to WordNet
- **Multiple Results**: Shows multiple definitions, synonyms, and examples from WordNet
- **Rich Results**: Returns formatted definitions with phonetics, meanings, examples, and more
- **Detailed View**: Clicking on results shows comprehensive information about the word
- **Error Handling**: Provides notifications if no word has been found
- **No API Keys Required**: Uses freely available APIs and local libraries for lookups

## Requirements

- Python 3.7+
- aiogram 3.3.0+
- python-dotenv
- requests
- nltk

## Setup

1. Clone this repository:

   ```
   git clone https://github.com/purr/telegram-dictionary.git
   cd telegram-dictionary
   ```

2. Install the required dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Download WordNet data:

   ```
   python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
   ```

4. Create a Telegram bot using BotFather:

   - Open Telegram and search for `@BotFather` 🤖
   - Send `/newbot` command and follow the instructions
   - Once created, BotFather will give you a token
   - Enable inline mode for your bot by sending `/setinline` to BotFather
   - Set the inline placeholder text (e.g., "Type a word to lookup")

5. Create a `.env` file in the project directory and add your bot token:

   ```
   BOT_TOKEN=your_telegram_bot_token_here
   ```

6. Run the bot:
   ```
   python run.py
   ```

## Usage

1. In any Telegram chat (including direct messages with the bot), type `@your_bot_name` followed by a space and the word you want to look up.

   Example: `@your_bot_name hello`

2. The bot will search for the definition of the word and display a brief preview.

3. Tap on the result to send the full definition to the chat.

4. For more detailed information, tap on the "Detailed information" option.

5. If the word isn't found in the primary dictionary, it will automatically check WordNet and show those results instead.

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
