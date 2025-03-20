import asyncio
import logging

import requests

import config


class DictionaryService:
    """Service for dictionary word lookups"""

    @staticmethod
    async def lookup_word(word):
        """Look up a word definition using dictionary APIs"""
        try:
            # Use asyncio to run the requests in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(config.FREE_DICTIONARY_API.format(word)),
            )

            if response.status_code == 200:
                data = response.json()
                return data
            else:
                # TODO: Add fallback to secondary dictionary API if needed
                logging.warning(
                    f"Word not found: {word}, status code: {response.status_code}"
                )
                return None

        except Exception as e:
            logging.error(f"Error looking up word: {e}")
            return None

    @staticmethod
    def format_brief_definition(data, word):
        """Format a brief definition for inline query results"""
        if not data or not isinstance(data, list) or len(data) == 0:
            return "No definition available"

        meanings = data[0].get("meanings", [])
        if not meanings or len(meanings) == 0:
            return "No definition available"

        definitions = meanings[0].get("definitions", [])
        if not definitions or len(definitions) == 0:
            return "No definition available"

        brief_definition = definitions[0].get("definition", "No definition available")

        # Truncate if too long
        if len(brief_definition) > 100:
            brief_definition = brief_definition[:97] + "..."

        return brief_definition

    @staticmethod
    def format_definition(data, word):
        """Format the full definition data for display"""
        if not data or not isinstance(data, list) or len(data) == 0:
            return None

        result = f"📚 <b>{word.capitalize()}</b>"

        entry = data[0]
        if "phonetic" in entry and entry["phonetic"]:
            result += f" – <i>{entry['phonetic']}</i>"

        result += "\n"

        meanings = entry.get("meanings", [])
        for i, meaning in enumerate(meanings[:3]):  # Limit to first 3 meanings
            part_of_speech = meaning.get("partOfSpeech", "")
            definitions = meaning.get("definitions", [])

            if part_of_speech and definitions:
                result += f"\n<b>{part_of_speech}</b>:\n"

                # Add up to 2 definitions per part of speech
                for j, definition in enumerate(definitions[:2]):
                    result += f"{j + 1}. {definition.get('definition', '')}\n"

                    # Add example if available
                    if "example" in definition and definition["example"]:
                        result += f"   <i>Example: {definition['example']}</i>\n"

        # Add synonyms if available
        synonyms = []
        for meaning in meanings:
            if "synonyms" in meaning and meaning["synonyms"]:
                synonyms.extend(
                    meaning["synonyms"][:5]
                )  # Limit to 5 synonyms per meaning

        if synonyms:
            result += f"\n<b>Synonyms</b>: {', '.join(synonyms[:10])}\n"  # Limit to 10 total synonyms

        # Add pronunciation audio link if available
        phonetics = entry.get("phonetics", [])
        audio_url = None
        for phonetic in phonetics:
            if "audio" in phonetic and phonetic["audio"]:
                audio_url = phonetic["audio"]
                break

        if audio_url:
            result += f"\n🔊 <a href='{audio_url}'>Listen to pronunciation</a>"

        return result

    @staticmethod
    def format_detailed_definition(data, word):
        """Format a more comprehensive definition with all available information"""
        if not data or not isinstance(data, list) or len(data) == 0:
            return None

        result = f"📚 <b>{word.capitalize()}</b>"

        entry = data[0]

        # Add phonetics
        if "phonetic" in entry and entry["phonetic"]:
            result += f" – <i>{entry['phonetic']}</i>"

        result += "\n"

        # Add etymology if available
        if "origin" in entry and entry["origin"]:
            result += f"\n<b>Etymology</b>: {entry['origin']}\n"

        # Add all meanings with all definitions
        meanings = entry.get("meanings", [])
        for i, meaning in enumerate(meanings):
            part_of_speech = meaning.get("partOfSpeech", "")
            definitions = meaning.get("definitions", [])

            if part_of_speech and definitions:
                result += f"\n<b>{part_of_speech}</b>:\n"

                # Add all definitions
                for j, definition in enumerate(definitions):
                    result += f"{j + 1}. {definition.get('definition', '')}\n"

                    # Add example if available
                    if "example" in definition and definition["example"]:
                        result += f"   <i>Example: {definition['example']}</i>\n"

                # Add synonyms for this part of speech
                if "synonyms" in meaning and meaning["synonyms"]:
                    result += (
                        f"   <b>Synonyms</b>: {', '.join(meaning['synonyms'][:15])}\n"
                    )

                # Add antonyms for this part of speech
                if "antonyms" in meaning and meaning["antonyms"]:
                    result += (
                        f"   <b>Antonyms</b>: {', '.join(meaning['antonyms'][:15])}\n"
                    )

        # Add pronunciation audio link if available
        phonetics = entry.get("phonetics", [])
        audio_url = None
        for phonetic in phonetics:
            if "audio" in phonetic and phonetic["audio"]:
                audio_url = phonetic["audio"]
                break

        if audio_url:
            result += f"\n🔊 <a href='{audio_url}'>Listen to pronunciation</a>"

        return result
