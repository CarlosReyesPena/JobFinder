"""
AutoTranslator module provides automatic translation functionality.
It uses deep-translator for translation and caches results in JSON files.
"""

import os
import json
from typing import Dict, List
from deep_translator import GoogleTranslator


class AutoTranslator:
    """
    Automatic translation manager.
    Caches translations in JSON files and uses deep-translator for new translations.
    """

    # Default languages
    DEFAULT_LANGUAGE = "en"

    # Available languages (codes supported by deep-translator)
    AVAILABLE_LANGUAGES = {
        "en": "English",
        "fr": "French",
        "es": "Spanish",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "nl": "Dutch",
        "zh-CN": "Chinese (Simplified)",
        "ja": "Japanese",
        "ar": "Arabic"
    }

    def __init__(self, translations_dir: str = None):
        """
        Initialize the auto translator.

        Args:
            translations_dir: Directory to store translation files (JSON)
        """
        # Set translations directory
        if translations_dir:
            self.translations_dir = translations_dir
        else:
            self.translations_dir = os.path.join(os.path.dirname(__file__), "translations_jsons")

        # Create the directory if it doesn't exist
        os.makedirs(self.translations_dir, exist_ok=True)

        # Initialize translation caches
        self.translations_cache: Dict[str, Dict[str, str]] = {}

        # Load existing translations
        self._load_all_translations()

    def _load_all_translations(self) -> None:
        """Load all translation files from the translations directory."""
        for lang_code in self.AVAILABLE_LANGUAGES.keys():
            if lang_code != self.DEFAULT_LANGUAGE:
                self._load_translations(lang_code)

    def _load_translations(self, lang_code: str) -> Dict[str, str]:
        """
        Load translations for a specific language from JSON file.

        Args:
            lang_code: Language code

        Returns:
            dict: Dictionary of translations (source text -> translated text)
        """
        translations = {}
        file_path = os.path.join(self.translations_dir, f"{lang_code}.json")

        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    translations = json.load(f)
                print(f"Loaded {len(translations)} translations for {lang_code}")
            else:
                print(f"No existing translation file for {lang_code}")
        except Exception as e:
            print(f"Error loading translations for {lang_code}: {e}")

        # Add to cache
        self.translations_cache[lang_code] = translations

        return translations

    def _save_translations(self, lang_code: str) -> bool:
        """
        Save translations for a specific language to JSON file.

        Args:
            lang_code: Language code

        Returns:
            bool: True if successful, False otherwise
        """
        if lang_code not in self.translations_cache:
            return False

        file_path = os.path.join(self.translations_dir, f"{lang_code}.json")

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.translations_cache[lang_code], f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving translations for {lang_code}: {e}")
            return False

    def translate(self, text: str, target_lang: str = None) -> str:
        """
        Translate text to the target language.
        If the translation is already cached, it will be returned from cache.
        Otherwise, deep-translator will be used and the result will be cached.

        Args:
            text: Source text (English)
            target_lang: Target language code

        Returns:
            str: Translated text
        """
        # Return original text if no target language is specified
        # or if target language is the default language (English)
        if not target_lang or target_lang == self.DEFAULT_LANGUAGE:
            return text

        # Check if target language is supported
        if target_lang not in self.AVAILABLE_LANGUAGES:
            print(f"Warning: Language '{target_lang}' is not supported. Using original text.")
            return text

        # Initialize translation cache for target language if not already done
        if target_lang not in self.translations_cache:
            self.translations_cache[target_lang] = {}

        # Check if translation is already cached
        if text in self.translations_cache[target_lang]:
            return self.translations_cache[target_lang][text]

        # Translate using deep-translator
        try:
            translator = GoogleTranslator(source=self.DEFAULT_LANGUAGE, target=target_lang)
            translated_text = translator.translate(text)

            # Add to cache
            self.translations_cache[target_lang][text] = translated_text

            # Save updated translations
            self._save_translations(target_lang)

            return translated_text
        except Exception as e:
            print(f"Error translating text to {target_lang}: {e}")
            return text

    def batch_translate(self, texts: List[str], target_lang: str = None) -> List[str]:
        """
        Translate multiple texts at once.

        Args:
            texts: List of source texts (English)
            target_lang: Target language code

        Returns:
            list: List of translated texts
        """
        return [self.translate(text, target_lang) for text in texts]

    def get_available_languages(self) -> Dict[str, str]:
        """
        Get a dictionary of available languages.

        Returns:
            dict: Dictionary of language codes and names
        """
        return self.AVAILABLE_LANGUAGES

    def add_manual_translation(self, source_text: str, translated_text: str,
                              lang_code: str) -> bool:
        """
        Add a manual translation to the cache.

        Args:
            source_text: Source text (English)
            translated_text: Translated text
            lang_code: Language code

        Returns:
            bool: True if successful, False otherwise
        """
        if lang_code not in self.AVAILABLE_LANGUAGES:
            return False

        # Initialize translation cache for target language if not already done
        if lang_code not in self.translations_cache:
            self.translations_cache[lang_code] = {}

        # Add translation to cache
        self.translations_cache[lang_code][source_text] = translated_text

        # Save updated translations
        return self._save_translations(lang_code)

    def generate_missing_translations(self, target_lang: str,
                                     source_texts: List[str]) -> Dict[str, str]:
        """
        Generate translations for texts that don't have translations yet.

        Args:
            target_lang: Target language code
            source_texts: List of source texts (English)

        Returns:
            dict: Dictionary of new translations
        """
        if target_lang not in self.AVAILABLE_LANGUAGES:
            return {}

        new_translations = {}

        # Initialize translation cache for target language if not already done
        if target_lang not in self.translations_cache:
            self.translations_cache[target_lang] = {}

        for text in source_texts:
            # Skip if translation already exists
            if text in self.translations_cache[target_lang]:
                continue

            # Translate
            try:
                translator = GoogleTranslator(source=self.DEFAULT_LANGUAGE, target=target_lang)
                translated_text = translator.translate(text)

                # Add to cache and result
                self.translations_cache[target_lang][text] = translated_text
                new_translations[text] = translated_text
            except Exception as e:
                print(f"Error translating text to {target_lang}: {e}")

        # Save updated translations
        if new_translations:
            self._save_translations(target_lang)

        return new_translations