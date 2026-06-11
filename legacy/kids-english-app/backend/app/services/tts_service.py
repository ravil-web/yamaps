"""
Text-to-Speech Service for pronunciation
"""
import os
import uuid
import hashlib
from pathlib import Path
from typing import Optional
from gtts import gTTS
from app.config import settings


class TTSService:
    """
    Text-to-Speech service for generating pronunciation audio.
    Uses Google Text-to-Speech (gTTS) as the primary provider.
    """
    
    def __init__(self):
        self.cache_dir = Path(settings.MEDIA_UPLOAD_DIR) / "audio_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.language = settings.TTS_LANGUAGE
        self.slow = settings.TTS_SLOW
    
    def generate_audio(
        self,
        text: str,
        language: str = "en",
        slow: bool = False
    ) -> str:
        """
        Generate audio file for the given text.
        
        Args:
            text: Text to convert to speech
            language: Language code (default: en)
            slow: Whether to speak slowly (for learning)
            
        Returns:
            Relative path to the generated audio file
        """
        # Create cache key from text
        cache_key = self._get_cache_key(text, language, slow)
        cache_path = self.cache_dir / f"{cache_key}.mp3"
        
        # Return cached file if exists
        if cache_path.exists():
            return f"/media/audio_cache/{cache_key}.mp3"
        
        # Generate new audio file
        tts = gTTS(text=text, lang=language, slow=slow)
        tts.save(str(cache_path))
        
        return f"/media/audio_cache/{cache_key}.mp3"
    
    def generate_word_pronunciation(
        self,
        word: str,
        slow: bool = True
    ) -> str:
        """
        Generate pronunciation for a single word.
        Uses slow speed by default for learning.
        """
        return self.generate_audio(word, language="en", slow=slow)
    
    def generate_sentence_pronunciation(
        self,
        sentence: str,
        slow: bool = False
    ) -> str:
        """
        Generate pronunciation for a sentence.
        Uses normal speed by default.
        """
        return self.generate_audio(sentence, language="en", slow=slow)
    
    def generate_translation_pronunciation(
        self,
        text: str,
        language: str = "ru"
    ) -> str:
        """
        Generate pronunciation for translation text.
        """
        return self.generate_audio(text, language=language, slow=False)
    
    def _get_cache_key(self, text: str, language: str, slow: bool) -> str:
        """Generate cache key from parameters"""
        key_string = f"{text}_{language}_{slow}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get_audio_url(self, text: str, language: str = "en") -> str:
        """
        Get URL for audio file, generating if necessary.
        """
        return self.generate_audio(text, language=language, slow=self.slow)
    
    def batch_generate(
        self,
        texts: list,
        language: str = "en",
        slow: bool = False
    ) -> dict:
        """
        Generate audio for multiple texts.
        
        Returns:
            Dictionary mapping text to audio URL
        """
        results = {}
        for text in texts:
            try:
                results[text] = self.generate_audio(text, language, slow)
            except Exception as e:
                results[text] = None
        return results


class PronunciationService:
    """Service for managing word pronunciations"""
    
    def __init__(self):
        self.tts = TTSService()
    
    def get_word_with_pronunciation(self, word: str) -> dict:
        """
        Get word with pronunciation data.
        """
        return {
            "word": word,
            "audio_url": self.tts.generate_word_pronunciation(word),
            "slow_audio_url": self.tts.generate_word_pronunciation(word, slow=True),
        }
    
    def get_vocabulary_audio(self, vocabulary_item) -> dict:
        """
        Get all audio URLs for a vocabulary item.
        """
        audio_data = {
            "word_audio": self.tts.generate_word_pronunciation(vocabulary_item.word),
            "word_slow_audio": self.tts.generate_word_pronunciation(vocabulary_item.word, slow=True),
        }
        
        if vocabulary_item.example_sentence:
            audio_data["example_audio"] = self.tts.generate_sentence_pronunciation(
                vocabulary_item.example_sentence
            )
        
        return audio_data


# Global TTS service instance
tts_service = TTSService()
pronunciation_service = PronunciationService()
