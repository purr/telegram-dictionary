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

            if response.status_code == 200:
                data = response.json()
                return {"source": "dictionary", "data": data}
            else:
                # Fallback to WordNet
                logging.warning(
                    f"Word not found in primary API: {word}, status code: {response.status_code}"
                )

                # Try WordNet
                synsets = wordnet.synsets(word)
                if synsets:
                    return {"source": "wordnet", "data": synsets}

                logging.warning(f"Word not found in any dictionary: {word}")
                return None

        except Exception as e:
            logging.error(f"Error looking up word: {e}")
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

        result += "\n\n"

        if source == "dictionary":
            if not isinstance(data, list) or len(data) == 0:
                return None

            entry = data[0]

            # Add phonetics
            if "phonetic" in entry and entry["phonetic"]:
                result += f"<b>Pronunciation:</b> <i>{entry['phonetic']}</i>\n\n"

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

        result += "\n\n"

        if source == "dictionary":
            if not isinstance(data, list) or len(data) == 0:
                return None

            entry = data[0]

            # Add phonetics
            if "phonetic" in entry and entry["phonetic"]:
                result += f"<b>Pronunciation:</b> <i>{entry['phonetic']}</i>\n\n"

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
        """Format a complete WordNet definition with all useful information in a single view"""
        if not data or data.get("source") != "wordnet":
            return None

        data = data.get("data")
        if not data or len(data) == 0:
            return None

        # Header
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

            # Add definitions for this part of speech (up to 3 per POS)
            for i, synset in enumerate(synsets[:3]):
                result += f"{i + 1}. {synset.definition()}\n"

                # Add examples (up to 2)
                examples = synset.examples()
                if examples:
                    if len(examples) == 1:
                        result += f"   <i>Example:</i> {examples[0]}\n"
                    else:
                        result += "   <i>Examples:</i>\n"
                        for ex in examples[:2]:
                            result += f"   • {ex}\n"

                # Add synonyms
                lemmas = synset.lemmas()
                synonyms = [
                    lemma.name().replace("_", " ")
                    for lemma in lemmas
                    if lemma.name().lower() != word.lower()
                ]
                if synonyms:
                    result += f"   <b>Synonyms:</b> {', '.join(synonyms[:7])}\n"

                # Add antonyms
                all_antonyms = []
                for lemma in lemmas:
                    antonyms = [
                        ant.name().replace("_", " ") for ant in lemma.antonyms()
                    ]
                    all_antonyms.extend(antonyms)

                if all_antonyms:
                    result += f"   <b>Antonyms:</b> {', '.join(all_antonyms[:7])}\n"

                result += "\n"

        # Add hypernyms (broader terms) for nouns
        noun_synsets = pos_groups.get("n", [])
        if noun_synsets:
            hypernyms = []
            for synset in noun_synsets[:2]:
                direct_hypernyms = synset.hypernyms()
                hypernyms.extend(
                    [h.name().split(".")[0].replace("_", " ") for h in direct_hypernyms]
                )

            if hypernyms:
                result += f"<b>Broader terms:</b> {', '.join(hypernyms[:10])}\n\n"

        # Add hyponyms (more specific terms) for nouns if available
        if noun_synsets:
            all_hyponyms = []
            for synset in noun_synsets[:1]:  # Only for the first noun synset
                direct_hyponyms = synset.hyponyms()
                all_hyponyms.extend(
                    [h.name().split(".")[0].replace("_", " ") for h in direct_hyponyms]
                )

            if all_hyponyms:
                result += (
                    f"<b>More specific terms:</b> {', '.join(all_hyponyms[:10])}\n\n"
                )

        # Add domains if they exist
        all_domains = []
        for synset in data[:3]:  # Check only first few synsets
            topic_domains = [
                d.name().split(".")[0].replace("_", " ") for d in synset.topic_domains()
            ]
            if topic_domains:
                all_domains.extend(topic_domains)

        if all_domains:
            result += f"<b>Domains:</b> {', '.join(all_domains[:7])}\n"

        return result
