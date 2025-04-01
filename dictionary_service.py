import re
import asyncio
import logging

import requests
from nltk.corpus import wordnet

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

            # Always try to get Urban Dictionary results
            urban_response = await loop.run_in_executor(
                None,
                lambda: requests.get(config.URBAN_DICTIONARY_API.format(word)),
            )
            urban_data = None
            if urban_response.status_code == 200:
                urban_data = urban_response.json()

            if response.status_code == 200:
                data = response.json()
                return {"source": "dictionary", "data": data, "urban_data": urban_data}
            else:
                # Fallback to WordNet
                logging.warning(
                    f"Word not found in primary API: {word}, status code: {response.status_code}"
                )

                # Try WordNet
                synsets = wordnet.synsets(word)
                if synsets:
                    return {
                        "source": "wordnet",
                        "data": synsets,
                        "urban_data": urban_data,
                    }

                # If neither WordNet nor dictionary API have results but Urban Dictionary does
                if urban_data and "list" in urban_data and urban_data["list"]:
                    return {
                        "source": "urban_only",
                        "data": None,
                        "urban_data": urban_data,
                    }

                logging.warning(f"Word not found in any dictionary: {word}")
                return None

        except Exception as e:
            logging.error(f"Error looking up word: {e}")
            return None

    @staticmethod
    def get_phonetic(data):
        """Extract phonetic notation from dictionary data"""
        if not data or data.get("source") != "dictionary":
            return None

        data = data.get("data")
        if not isinstance(data, list) or len(data) == 0:
            return None

        entry = data[0]

        # Try to get phonetic directly
        if "phonetic" in entry and entry["phonetic"]:
            return entry["phonetic"]

        # If no direct phonetic, try to get from phonetics array
        phonetics = entry.get("phonetics", [])
        for phonetic in phonetics:
            if "text" in phonetic and phonetic["text"]:
                return phonetic["text"]

        return None

    @staticmethod
    def format_brief_definition(data, word):
        """Format a brief definition for inline query results"""
        if not data:
            return "No definition available"

        source = data.get("source")
        data = data.get("data")

        if source == "dictionary":
            if not isinstance(data, list) or len(data) == 0:
                return "No definition available"

            meanings = data[0].get("meanings", [])
            if not meanings or len(meanings) == 0:
                return "No definition available"

            definitions = meanings[0].get("definitions", [])
            if not definitions or len(definitions) == 0:
                return "No definition available"

            brief_definition = definitions[0].get(
                "definition", "No definition available"
            )

        elif source == "wordnet":
            if not data or len(data) == 0:
                return "No definition available"

            # Get the first definition from WordNet
            brief_definition = data[0].definition()

        else:
            return "No definition available"

        # Truncate if too long
        if len(brief_definition) > 100:
            brief_definition = brief_definition[:97] + "..."

        return brief_definition

    @staticmethod
    def format_definition(data, word):
        """Format the full definition data for display"""
        if not data:
            return None

        source = data.get("source")
        data = data.get("data")

        # Standard header regardless of source
        result = f"📚 <b>{word.capitalize()}</b>"

        # Add source if it's WordNet
        if source == "wordnet":
            result += " (WordNet)"
        # Add phonetics if it's dictionary source
        elif source == "dictionary" and isinstance(data, list) and len(data) > 0:
            entry = data[0]
            phonetic = None
            audio_url = None

            # Try to get phonetic directly
            if "phonetic" in entry and entry["phonetic"]:
                phonetic = entry["phonetic"]

            # Try to get audio URL and possibly phonetic from phonetics array
            phonetics = entry.get("phonetics", [])
            for ph in phonetics:
                if "audio" in ph and ph["audio"] and not audio_url:
                    audio_url = ph["audio"]
                if not phonetic and "text" in ph and ph["text"]:
                    phonetic = ph["text"]

            # Add phonetic to header
            if phonetic:
                result += f" • /{phonetic.strip('/')}/".replace("//", "/")

            # Add audio icon if available
            if audio_url:
                result += f" 🔊"

        result += "\n\n"

        if source == "dictionary":
            if not isinstance(data, list) or len(data) == 0:
                return None

            entry = data[0]

            # Process meanings (limited to first 3)
            meanings = entry.get("meanings", [])
            for i, meaning in enumerate(meanings[:3]):
                part_of_speech = meaning.get("partOfSpeech", "").capitalize()
                definitions = meaning.get("definitions", [])

                if part_of_speech and definitions:
                    result += f"<b>{part_of_speech}</b>:\n"

                    # Add up to 2 definitions per part of speech
                    for j, definition in enumerate(definitions[:2]):
                        result += f"{j + 1}. {definition.get('definition', '')}\n"

                        # Add example if available
                        if "example" in definition and definition["example"]:
                            result += f"   <i>Example:</i> {definition['example']}\n"

                    # Add synonyms for this part of speech
                    if "synonyms" in meaning and meaning["synonyms"]:
                        synonyms = meaning["synonyms"][:5]  # Limit to 5 synonyms
                        result += f"   <b>Synonyms:</b> {', '.join(synonyms)}\n"

                    # Add antonyms for this part of speech
                    if "antonyms" in meaning and meaning["antonyms"]:
                        antonyms = meaning["antonyms"][:5]  # Limit to 5 antonyms
                        result += f"   <b>Antonyms:</b> {', '.join(antonyms)}\n"

                    result += "\n"

            # Add pronunciation audio link if available
            phonetics = entry.get("phonetics", [])
            audio_url = None
            for phonetic in phonetics:
                if "audio" in phonetic and phonetic["audio"]:
                    audio_url = phonetic["audio"]
                    break

            if audio_url:
                result += f"🔊 <a href='{audio_url}'>Listen to pronunciation</a>"

        elif source == "wordnet":
            if not data or len(data) == 0:
                return None

            # Group synsets by part of speech
            pos_groups = {}
            for synset in data:
                pos = synset.pos()
                if pos not in pos_groups:
                    pos_groups[pos] = []
                pos_groups[pos].append(synset)

            # Display information for each part of speech (limited to first 3 synsets per POS)
            for pos, synsets in pos_groups.items():
                pos_full = {
                    "n": "Noun",
                    "v": "Verb",
                    "a": "Adjective",
                    "s": "Adjective Satellite",
                    "r": "Adverb",
                }.get(pos, pos.upper())

                result += f"<b>{pos_full}</b>:\n"

                # Add up to 2 definitions per part of speech
                for i, synset in enumerate(synsets[:2]):
                    result += f"{i + 1}. {synset.definition()}\n"

                    # Add examples
                    examples = synset.examples()
                    if examples:
                        example = examples[0]  # Just show one example for consistency
                        result += f"   <i>Example:</i> {example}\n"

                    # Add synonyms
                    lemmas = synset.lemmas()
                    synonyms = [
                        lemma.name().replace("_", " ")
                        for lemma in lemmas
                        if lemma.name().lower() != word.lower()
                    ]
                    if synonyms:
                        result += f"   <b>Synonyms:</b> {', '.join(synonyms[:5])}\n"

                    # Add antonyms if available
                    all_antonyms = []
                    for lemma in lemmas:
                        antonyms = [
                            ant.name().replace("_", " ") for ant in lemma.antonyms()
                        ]
                        all_antonyms.extend(antonyms)

                    if all_antonyms:
                        result += f"   <b>Antonyms:</b> {', '.join(all_antonyms[:5])}\n"

                result += "\n"

        return result

    @staticmethod
    def format_detailed_definition(data, word):
        """Format a more comprehensive definition with all available information"""
        if not data:
            return None

        source = data.get("source")
        data = data.get("data")

        # Standard header regardless of source
        result = f"📚 <b>{word.capitalize()}</b>"

        # Add source if it's WordNet
        if source == "wordnet":
            result += " (WordNet)"
        # Add phonetics if it's dictionary source
        elif source == "dictionary" and isinstance(data, list) and len(data) > 0:
            entry = data[0]
            phonetic = None
            audio_url = None

            # Try to get phonetic directly
            if "phonetic" in entry and entry["phonetic"]:
                phonetic = entry["phonetic"]

            # Try to get audio URL and possibly phonetic from phonetics array
            phonetics = entry.get("phonetics", [])
            for ph in phonetics:
                if "audio" in ph and ph["audio"] and not audio_url:
                    audio_url = ph["audio"]
                if not phonetic and "text" in ph and ph["text"]:
                    phonetic = ph["text"]

            # Add phonetic to header
            if phonetic:
                result += f" • /{phonetic.strip('/')}/".replace("//", "/")

            # Add audio icon if available
            if audio_url:
                result += f" 🔊"

        result += "\n\n"

        if source == "dictionary":
            if not isinstance(data, list) or len(data) == 0:
                return None

            entry = data[0]

            # Add etymology if available
            if "origin" in entry and entry["origin"]:
                result += f"<b>Etymology:</b> {entry['origin']}\n\n"

            # Process all meanings with all definitions
            meanings = entry.get("meanings", [])
            for i, meaning in enumerate(meanings):
                part_of_speech = meaning.get("partOfSpeech", "").capitalize()
                definitions = meaning.get("definitions", [])

                if part_of_speech and definitions:
                    result += f"<b>{part_of_speech}</b>:\n"

                    # Add all definitions
                    for j, definition in enumerate(definitions):
                        result += f"{j + 1}. {definition.get('definition', '')}\n"

                        # Add example if available
                        if "example" in definition and definition["example"]:
                            result += f"   <i>Example:</i> {definition['example']}\n"

                    # Add synonyms for this part of speech
                    if "synonyms" in meaning and meaning["synonyms"]:
                        synonyms = meaning["synonyms"][
                            :10
                        ]  # Limit to 10 synonyms in detailed view
                        result += f"   <b>Synonyms:</b> {', '.join(synonyms)}\n"

                    # Add antonyms for this part of speech
                    if "antonyms" in meaning and meaning["antonyms"]:
                        antonyms = meaning["antonyms"][
                            :10
                        ]  # Limit to 10 antonyms in detailed view
                        result += f"   <b>Antonyms:</b> {', '.join(antonyms)}\n"

                    result += "\n"

            # Add pronunciation audio link if available
            phonetics = entry.get("phonetics", [])
            audio_url = None
            for phonetic in phonetics:
                if "audio" in phonetic and phonetic["audio"]:
                    audio_url = phonetic["audio"]
                    break

            if audio_url:
                result += f"🔊 <a href='{audio_url}'>Listen to pronunciation</a>"

        elif source == "wordnet":
            if not data or len(data) == 0:
                return None

            # Group synsets by part of speech
            pos_groups = {}
            for synset in data:
                pos = synset.pos()
                if pos not in pos_groups:
                    pos_groups[pos] = []
                pos_groups[pos].append(synset)

            # Display information for each part of speech
            for pos, synsets in pos_groups.items():
                pos_full = {
                    "n": "Noun",
                    "v": "Verb",
                    "a": "Adjective",
                    "s": "Adjective Satellite",
                    "r": "Adverb",
                }.get(pos, pos.upper())

                result += f"<b>{pos_full}</b>:\n"

                # Add all definitions for this part of speech (limited to 5)
                for i, synset in enumerate(synsets[:5]):
                    result += f"{i + 1}. {synset.definition()}\n"

                    # Add examples
                    examples = synset.examples()
                    if examples:
                        result += "   <i>Examples:</i>\n"
                        for j, ex in enumerate(examples[:2]):  # Limit to 2 examples
                            result += f"   • {ex}\n"

                    # Add synonyms
                    lemmas = synset.lemmas()
                    synonyms = [
                        lemma.name().replace("_", " ")
                        for lemma in lemmas
                        if lemma.name().lower() != word.lower()
                    ]
                    if synonyms:
                        result += f"   <b>Synonyms:</b> {', '.join(synonyms[:10])}\n"

                    # Add antonyms if available
                    all_antonyms = []
                    for lemma in lemmas:
                        antonyms = [
                            ant.name().replace("_", " ") for ant in lemma.antonyms()
                        ]
                        all_antonyms.extend(antonyms)

                    if all_antonyms:
                        result += (
                            f"   <b>Antonyms:</b> {', '.join(all_antonyms[:10])}\n"
                        )

                    result += "\n"

            # Add hypernyms (broader terms) for nouns if available
            noun_synsets = pos_groups.get("n", [])
            if noun_synsets:
                hypernyms = []
                for synset in noun_synsets[:2]:  # Take first two noun synsets only
                    direct_hypernyms = synset.hypernyms()
                    hypernyms.extend(
                        [
                            h.name().split(".")[0].replace("_", " ")
                            for h in direct_hypernyms
                        ]
                    )

                if hypernyms:
                    result += f"<b>Broader terms:</b> {', '.join(hypernyms[:10])}\n"

        return result

    @staticmethod
    def format_complete_wordnet_definition(data, word):
        """Format a complete WordNet definition for display"""
        if not data:
            return None

        source = data.get("source")
        data = data.get("data")

        if source != "wordnet" or not data:
            return None

        # Standard header
        result = f"📚 <b>{word.capitalize()}</b> (WordNet)\n\n"

        # Group synsets by part of speech
        pos_groups = {}
        for synset in data:
            pos = synset.pos()
            if pos not in pos_groups:
                pos_groups[pos] = []
            pos_groups[pos].append(synset)

        # Display information for each part of speech
        for pos, synsets in pos_groups.items():
            pos_full = {
                "n": "Noun",
                "v": "Verb",
                "a": "Adjective",
                "s": "Adjective Satellite",
                "r": "Adverb",
            }.get(pos, pos.upper())

            result += f"<b>{pos_full}</b>:\n"

            # Add definitions for this part of speech (limited to 3)
            for i, synset in enumerate(synsets[:3]):
                result += f"{i + 1}. {synset.definition()}\n"

                # Add examples
                examples = synset.examples()
                if examples:
                    example = examples[0]  # Just show one example for clarity
                    result += f"   <i>Example:</i> {example}\n"

                # Add synonyms
                lemmas = synset.lemmas()
                synonyms = [
                    lemma.name().replace("_", " ")
                    for lemma in lemmas
                    if lemma.name().lower() != word.lower()
                ]
                if synonyms:
                    result += f"   <b>Synonyms:</b> {', '.join(synonyms[:7])}\n"

                # Add antonyms if available
                all_antonyms = []
                for lemma in lemmas:
                    antonyms = [
                        ant.name().replace("_", " ") for ant in lemma.antonyms()
                    ]
                    all_antonyms.extend(antonyms)

                if all_antonyms:
                    result += f"   <b>Antonyms:</b> {', '.join(all_antonyms[:7])}\n"

                result += "\n"

        # If it's a noun, add hypernyms/hyponyms
        noun_synsets = pos_groups.get("n", [])
        if noun_synsets:
            # Add hypernyms (broader terms)
            hypernyms = []
            for synset in noun_synsets[:1]:  # Only for first noun synset
                direct_hypernyms = synset.hypernyms()
                hypernyms.extend(
                    [h.name().split(".")[0].replace("_", " ") for h in direct_hypernyms]
                )

            if hypernyms:
                result += f"<b>Broader terms:</b> {', '.join(hypernyms[:5])}\n"

            # Add hyponyms (more specific terms)
            hyponyms = []
            for synset in noun_synsets[:1]:  # Only for first noun synset
                direct_hyponyms = synset.hyponyms()
                hyponyms.extend(
                    [h.name().split(".")[0].replace("_", " ") for h in direct_hyponyms]
                )

            if hyponyms:
                result += f"<b>More specific terms:</b> {', '.join(hyponyms[:5])}\n"

        return result

    @staticmethod
    def format_brief_urban_definition(definition_data):
        """Format a brief Urban Dictionary definition for inline query results"""
        definition = definition_data.get("definition", "No definition available")

        # Clean up formatting - handle HTML entities and square brackets
        definition = definition.replace("<", "&lt;").replace(">", "&gt;")

        # Remove Urban Dictionary's square bracket formatting for the brief description
        definition = definition.replace("[", "").replace("]", "")

        # Truncate if too long
        if len(definition) > 100:
            definition = definition[:97] + "..."

        return definition

    @staticmethod
    def get_urban_word(definition_data, default_word):
        """Get the word as defined by Urban Dictionary"""
        if not definition_data:
            return default_word.capitalize()

        # Use word from Urban Dictionary if available
        word = definition_data.get("word", default_word)

        # Escape any HTML entities that might be in the word
        word = word.replace("<", "&lt;").replace(">", "&gt;")

        return word

    @staticmethod
    def format_urban_definition(definition_data, word, result_id):
        """Format an Urban Dictionary definition for display"""
        if not definition_data:
            return None

        # Use word from Urban Dictionary if available
        urban_word = definition_data.get("word", word)

        # Sanitize the word to prevent HTML injection
        urban_word = urban_word.replace("<", "&lt;").replace(">", "&gt;")

        definition = definition_data.get("definition", "")
        example = definition_data.get("example", "")
        thumbs_up = definition_data.get("thumbs_up", 0)
        thumbs_down = definition_data.get("thumbs_down", 0)
        author = definition_data.get("author", "Anonymous")
        permalink = definition_data.get("permalink", "")

        # Sanitize the author to prevent HTML injection
        author = author.replace("<", "&lt;").replace(">", "&gt;")

        # Clean up formatting in a safe way - replace potential HTML entities
        # and remove Urban Dictionary's square bracket formatting
        definition = definition.replace("<", "&lt;").replace(">", "&gt;")
        example = example.replace("<", "&lt;").replace(">", "&gt;")

        # Process Urban Dictionary links (words in square brackets)
        # Format: replace [word] with hyperlinked word
        def replace_ud_links(text):
            # Pattern to find words in square brackets
            pattern = r"\[(.*?)\]"

            def make_link(match):
                word = match.group(1)
                # Create a safe hyperlink to Urban Dictionary search
                safe_word = word.replace(" ", "%20")
                return f'<a href="https://www.urbandictionary.com/define.php?term={safe_word}">{word}</a>'

            # Replace all instances with hyperlinks
            processed_text = re.sub(pattern, make_link, text)
            return processed_text

        # Apply link processing
        definition = replace_ud_links(definition)
        example = replace_ud_links(example)

        # Add paragraph breaks for better readability
        definition = (
            definition.replace("\r\n", "\n").replace("\n\n", "\n").replace("\n", "\n\n")
        )

        # Format examples with special styling
        formatted_example = ""
        if example:
            # Split examples by newlines and format each with a quote style
            example_lines = example.split("\n")
            formatted_example_lines = []
            for line in example_lines:
                if line.strip():
                    formatted_example_lines.append(f"💬 <i>{line.strip()}</i>")
            formatted_example = "\n".join(formatted_example_lines)

        # Create the formatted message
        result = f"🏙️ <b>{urban_word}</b> (Urban #{result_id})\n\n"
        result += f"{definition}\n\n"

        if formatted_example:
            result += f"<b>📝 Examples:</b>\n{formatted_example}\n\n"

        # Add rating and source with emojis
        result += f"👍 {thumbs_up} | 👎 {thumbs_down} | ✍️ By: {author}\n"
        if permalink:
            result += f"🔗 <a href='{permalink}'>View on Urban Dictionary</a>"

        # Just add a zero-width space to prevent auto-preview of the first link
        # but don't add any visible text
        result += "\n\u200b"

        return result
