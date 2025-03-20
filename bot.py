import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import InlineQuery, InputTextMessageContent, InlineQueryResultArticle
from aiogram.filters import CommandStart

import config
from dictionary_service import DictionaryService

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start_command(message: types.Message):
    """Handler for the /start command"""
    # Get bot info to display actual username
    bot_info = await bot.get_me()
    bot_username = bot_info.username

    await message.answer(
        f"👋 Welcome to the Dictionary Bot v{config.VERSION}!\n\n"
        f"Use this bot in inline mode by typing @{bot_username} followed by "
        f"the word you want to look up. For example: @{bot_username} hello\n\n"
        "The bot will search for definitions in public dictionaries and "
        "display the results directly in your chat."
    )


@dp.inline_query()
async def inline_query_handler(query: InlineQuery):
    """Handler for inline queries"""
    text = query.query.strip().lower()

    if not text:
        # No query text provided
        return await query.answer(
            results=[],
            switch_pm_text="Type a word to look up",
            switch_pm_parameter="start",
            cache_time=5,
        )

    # Wait for user to finish typing (debounce)
    await asyncio.sleep(config.INLINE_QUERY_DEBOUNCE)

    # Check if the inline query has been cancelled or changed
    if text != query.query.strip().lower():
        return

    # Look up the word
    data = await DictionaryService.lookup_word(text)

    if data:
        # Word found, create results
        brief_definition = DictionaryService.format_brief_definition(data, text)
        basic_definition = DictionaryService.format_definition(data, text)
        detailed_definition = DictionaryService.format_detailed_definition(data, text)

        results = [
            InlineQueryResultArticle(
                id="1",
                title=f"📚 {text.capitalize()}",
                description=brief_definition,
                input_message_content=InputTextMessageContent(
                    message_text=basic_definition, parse_mode=ParseMode.HTML
                ),
                thumb_url="https://img.icons8.com/color/48/000000/book.png",
                thumb_width=48,
                thumb_height=48,
            )
        ]

        # Add detailed definition option
        if detailed_definition:
            results.append(
                InlineQueryResultArticle(
                    id="2",
                    title=f"ℹ️ Detailed information for '{text}'",
                    description="View all meanings, examples, and related words",
                    input_message_content=InputTextMessageContent(
                        message_text=detailed_definition, parse_mode=ParseMode.HTML
                    ),
                    thumb_url="https://img.icons8.com/color/48/000000/info.png",
                    thumb_width=48,
                    thumb_height=48,
                )
            )
    else:
        # Word not found
        results = [
            InlineQueryResultArticle(
                id="not_found",
                title="❌ Word not found",
                description=f"No definition found for '{text}'",
                input_message_content=InputTextMessageContent(
                    message_text=f"❌ No definition found for <b>{text}</b>",
                    parse_mode=ParseMode.HTML,
                ),
                thumb_url="https://img.icons8.com/color/48/000000/cancel.png",
                thumb_width=48,
                thumb_height=48,
            )
        ]

    # Answer the inline query
    await query.answer(results=results, cache_time=config.INLINE_RESULTS_CACHE_TIME)


async def main():
    # Start the bot
    bot_info = await bot.get_me()
    logging.info(f"Starting Dictionary Bot v{config.VERSION} as @{bot_info.username}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
