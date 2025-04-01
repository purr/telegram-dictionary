import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import (
    InlineQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputTextMessageContent,
    InlineQueryResultArticle,
)
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

    # Create an example word for demonstration
    example_word = "dictionary"

    # Create inline keyboard with a try button
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Try with '{example_word}'",
                    switch_inline_query_current_chat=example_word,
                )
            ]
        ]
    )

    # Create a detailed welcome message
    welcome_text = (
        f"👋 Welcome @{bot_username} v{config.VERSION}!\n\n"
        f"📚 This bot helps you find definitions for words using multiple sources:\n"
        f"• Standard dictionary definitions\n"
        f"• WordNet linguistic database\n"
        f"• Urban Dictionary for slang and colloquial terms\n\n"
        f"🔎 How to use:\n"
        f"1. Type <code>@{bot_username}</code> followed by a word in any chat\n"
        f"2. Select from the definition options that appear\n"
        f"3. The definition will be sent to your chat\n\n"
        f"✨ Features:\n"
        f"• Fast word lookups\n"
        f"• Pronunciations and audio links\n"
        f"• Multiple definitions\n"
        f"• Examples, synonyms, and antonyms\n"
        f"• Urban Dictionary results for modern slang\n\n"
        f"Try it now with the button below!"
    )

    await message.answer(welcome_text, reply_markup=markup, parse_mode=ParseMode.HTML)


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

    results = []

    if data:
        source = data.get("source")
        urban_data = data.get("urban_data", None)

        # Create results based on the source
        if source == "dictionary":
            # Word found in primary dictionary, create results
            brief_definition = DictionaryService.format_brief_definition(data, text)
            basic_definition = DictionaryService.format_definition(data, text)
            detailed_definition = DictionaryService.format_detailed_definition(
                data, text
            )

            # Get pronunciation if available
            phonetic = DictionaryService.get_phonetic(data)
            word_title = text.capitalize()

            # Add pronunciation to title if available
            title_with_phonetic = word_title
            if phonetic:
                title_with_phonetic = f"{word_title} • /{phonetic.strip('/')}/".replace(
                    "//", "/"
                )

            # Primary dictionary result - always first
            results.append(
                InlineQueryResultArticle(
                    id="1",
                    title=f"📚 {title_with_phonetic}",
                    description=brief_definition,
                    input_message_content=InputTextMessageContent(
                        message_text=basic_definition,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=False,
                    ),
                    thumb_url="https://img.icons8.com/color/48/000000/book.png",
                    thumb_width=48,
                    thumb_height=48,
                )
            )

            # Add detailed definition option - only if it's different from the basic definition
            if detailed_definition and detailed_definition != basic_definition:
                # Check if it provides additional information
                if (
                    len(detailed_definition) > len(basic_definition) * 1.2
                ):  # At least 20% more content
                    results.append(
                        InlineQueryResultArticle(
                            id="2",
                            title=f"ℹ️ Detailed information for '{word_title}'",
                            description="View all meanings, examples, and related words",
                            input_message_content=InputTextMessageContent(
                                message_text=detailed_definition,
                                parse_mode=ParseMode.HTML,
                                disable_web_page_preview=False,
                            ),
                            thumb_url="https://img.icons8.com/color/48/000000/info.png",
                            thumb_width=48,
                            thumb_height=48,
                        )
                    )

        elif source == "wordnet":
            # Word found in WordNet, create comprehensive result
            brief_definition = DictionaryService.format_brief_definition(data, text)
            complete_wordnet_definition = (
                DictionaryService.format_complete_wordnet_definition(data, text)
            )

            # WordNet result - first if no primary dictionary
            results.append(
                InlineQueryResultArticle(
                    id="1",
                    title=f"📚 {text.capitalize()} (WordNet)",
                    description=brief_definition,
                    input_message_content=InputTextMessageContent(
                        message_text=complete_wordnet_definition,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=False,
                    ),
                    thumb_url="https://img.icons8.com/color/48/000000/graduation-cap.png",
                    thumb_width=48,
                    thumb_height=48,
                )
            )

        elif source == "urban_only":
            # Instead of showing "not found in standard dictionaries" message,
            # we'll just skip straight to showing Urban Dictionary results
            pass
            # No header message for "not found in standard dictionaries"

        # Add Urban Dictionary results if available
        if urban_data and "list" in urban_data and urban_data["list"]:
            urban_definitions = urban_data["list"]

            # Calculate how many Urban results to show (up to the maximum, minus existing results)
            remaining_slots = 20 - len(results)
            urban_limit = min(remaining_slots, config.MAX_URBAN_RESULTS)

            for i, definition in enumerate(urban_definitions[:urban_limit]):
                result_id = i + 1
                brief_urban_def = DictionaryService.format_brief_urban_definition(
                    definition
                )
                urban_word = DictionaryService.get_urban_word(definition, text)
                full_urban_def = DictionaryService.format_urban_definition(
                    definition, text, result_id
                )

                results.append(
                    InlineQueryResultArticle(
                        id=f"urban_{i}",
                        title=f"🏙️ {urban_word} (Urban #{result_id})",
                        description=brief_urban_def,
                        input_message_content=InputTextMessageContent(
                            message_text=full_urban_def,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True,
                        ),
                        thumb_url="https://img.icons8.com/color/48/000000/city.png",
                        thumb_width=48,
                        thumb_height=48,
                    )
                )

    else:
        # Word not found in any dictionary
        results = [
            InlineQueryResultArticle(
                id="not_found",
                title="❌ Word not found",
                description=f"No definition found for '{text}'",
                input_message_content=InputTextMessageContent(
                    message_text=f"❌ No definition found for <b>{text}</b>",
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
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
