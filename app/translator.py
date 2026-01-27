"""
Translation providers module.
Contains base translator and implementations for DeepSeek and OpenAI.
"""

import json
import hashlib
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
from openai import OpenAI
from app.config import settings


# Language display names
LANGUAGE_NAMES = {
    "zh": "Chinese",
    "en": "English", 
    "ru": "Russian",
    "uz": "Uzbek"
}

# Shared cache for all translators
_translation_cache: Dict[str, Tuple[Any, int]] = {}


def _get_cache_key(provider: str, data: str, target_language: str, summarize: bool) -> str:
    """Generate a cache key from the input data."""
    content = f"{provider}:{data}:{target_language}:{summarize}"
    return hashlib.md5(content.encode()).hexdigest()


class BaseTranslator(ABC):
    """Abstract base class for translation providers."""
    
    provider_name: str = "base"
    
    def __init__(self):
        self.max_tokens = settings.MAX_TOKENS
        self.temperature = settings.TEMPERATURE
        self.enable_summarization = settings.ENABLE_SUMMARIZATION
        self.summarize_threshold = settings.SUMMARIZE_THRESHOLD
        self.enable_cache = settings.ENABLE_CACHE
    
    def _should_summarize(self, text: str) -> bool:
        """Check if text needs summarization."""
        return self.enable_summarization and len(text) > self.summarize_threshold
    
    def _extract_strings(
        self,
        data: Union[Dict, List, Any],
        keys_to_translate: Optional[List[str]] = None,
        parent_key: str = ""
    ) -> Dict[str, str]:
        """Recursively extract string values from JSON data."""
        strings = {}
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{parent_key}.{key}" if parent_key else key
                if isinstance(value, str):
                    if keys_to_translate is None or key in keys_to_translate:
                        if value.strip():
                            strings[current_path] = value
                elif isinstance(value, (dict, list)):
                    strings.update(self._extract_strings(value, keys_to_translate, current_path))
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                current_path = f"{parent_key}[{idx}]"
                if isinstance(item, str):
                    if keys_to_translate is None and item.strip():
                        strings[current_path] = item
                elif isinstance(item, (dict, list)):
                    strings.update(self._extract_strings(item, keys_to_translate, current_path))
        
        return strings
    
    def _apply_translations(
        self,
        data: Union[Dict, List, Any],
        translations: Dict[str, str],
        parent_key: str = ""
    ) -> Union[Dict, List, Any]:
        """Apply translated strings back to JSON structure."""
        if isinstance(data, dict):
            return {
                key: (
                    translations.get(f"{parent_key}.{key}" if parent_key else key, value)
                    if isinstance(value, str) and (f"{parent_key}.{key}" if parent_key else key) in translations
                    else self._apply_translations(value, translations, f"{parent_key}.{key}" if parent_key else key)
                    if isinstance(value, (dict, list))
                    else value
                )
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [
                (
                    translations.get(f"{parent_key}[{idx}]", item)
                    if isinstance(item, str) and f"{parent_key}[{idx}]" in translations
                    else self._apply_translations(item, translations, f"{parent_key}[{idx}]")
                    if isinstance(item, (dict, list))
                    else item
                )
                for idx, item in enumerate(data)
            ]
        return data
    
    def _create_prompt(self, strings: Dict[str, str], target_language: str, summarize: bool) -> str:
        """Create optimized translation prompt."""
        target_name = LANGUAGE_NAMES.get(target_language, target_language)
        sum_note = " Summarize verbose text." if summarize else ""
        
        return f"""Translate Chinese→{target_name}. JSON only.{sum_note}
Keep keys, translate values. Natural translation.
{json.dumps(strings, ensure_ascii=False)}"""
    
    @abstractmethod
    def _get_client(self) -> OpenAI:
        """Get the API client."""
        pass
    
    @abstractmethod
    def _get_model(self) -> str:
        """Get the model name."""
        pass
    
    async def translate(
        self,
        data: Union[Dict[str, Any], List[Any]],
        target_language: str = "en",
        keys_to_translate: Optional[List[str]] = None,
        summarize: Optional[bool] = None
    ) -> Tuple[Union[Dict[str, Any], List[Any]], Dict[str, int]]:
        """Translate Chinese text in JSON to target language."""
        
        if target_language not in settings.SUPPORTED_TARGET_LANGUAGES:
            raise ValueError(f"Unsupported language: {target_language}. Use: {', '.join(settings.SUPPORTED_TARGET_LANGUAGES)}")
        
        strings = self._extract_strings(data, keys_to_translate)
        if not strings:
            return data, {"input": 0, "output": 0, "total": 0}
        
        should_summarize = summarize if summarize is not None else self._should_summarize("".join(strings.values()))
        
        # Check cache
        if self.enable_cache:
            cache_key = _get_cache_key(
                self.provider_name,
                json.dumps(strings, ensure_ascii=False),
                target_language,
                should_summarize
            )
            if cache_key in _translation_cache:
                cached, usage = _translation_cache[cache_key]
                # Allow legacy int cache for safety
                if isinstance(usage, int):
                     usage = {"input": 0, "output": 0, "total": usage}
                return self._apply_translations(data, cached), usage
        
        # Call API
        prompt = self._create_prompt(strings, target_language, should_summarize)
        
        response = self._get_client().chat.completions.create(
            model=self._get_model(),
            messages=[
                {"role": "system", "content": "Fast Chinese translator. JSON output only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            response_format={"type": "json_object"}
        )
        
        translated = json.loads(response.choices[0].message.content)
        
        usage = {
            "input": response.usage.prompt_tokens if response.usage else 0,
            "output": response.usage.completion_tokens if response.usage else 0,
            "total": response.usage.total_tokens if response.usage else 0
        }
        
        # Cache result
        if self.enable_cache:
            _translation_cache[cache_key] = (translated, usage)
        
        return self._apply_translations(data, translated), usage

class DeepSeekTranslator(BaseTranslator):
    """DeepSeek API translator implementation."""
    
    provider_name = "deepseek"
    
    def __init__(self):
        super().__init__()
        self._client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL
        )
    
    def _get_client(self) -> OpenAI:
        return self._client
    
    def _get_model(self) -> str:
        return settings.DEEPSEEK_MODEL
    
    def is_configured(self) -> bool:
        return bool(settings.DEEPSEEK_API_KEY)
        
    async def translate(
        self,
        data: Union[Dict[str, Any], List[Any]],
        target_language: str = "en",
        keys_to_translate: Optional[List[str]] = None,
        summarize: Optional[bool] = None,
        model: Optional[str] = None
    ) -> Tuple[Union[Dict[str, Any], List[Any]], Dict[str, int]]:
        """Translate using DeepSeek."""
        return await super().translate(
            data=data,
            target_language=target_language,
            keys_to_translate=keys_to_translate,
            summarize=summarize,
            model=model
        )


class OpenAITranslator(BaseTranslator):
    """OpenAI API translator implementation."""
    
    provider_name = "openai"
    
    def __init__(self):
        super().__init__()
        self._client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
    
    def _get_client(self) -> OpenAI:
        return self._client
    
    def _get_model(self) -> str:
        return settings.OPENAI_MODEL
    
    def is_configured(self) -> bool:
        return bool(settings.OPENAI_API_KEY)
    
    async def translate(
        self,
        data: Union[Dict[str, Any], List[Any]],
        target_language: str = "en",
        keys_to_translate: Optional[List[str]] = None,
        summarize: Optional[bool] = None,
        model: Optional[str] = None
    ) -> Tuple[Union[Dict[str, Any], List[Any]], Dict[str, int]]:
        """
        Translate using OpenAI with smart parameter adjustment for different models.
        Supports switching between gpt-5.1 (High IQ) and gpt-5-mini (Fast).
        """
        
        if target_language not in settings.SUPPORTED_TARGET_LANGUAGES:
            raise ValueError(f"Unsupported language: {target_language}")
        
        strings = self._extract_strings(data, keys_to_translate)
        if not strings:
            return data, {"input": 0, "output": 0, "total": 0}
        
        should_summarize = summarize if summarize is not None else self._should_summarize("".join(strings.values()))
        
        # Determine model to use
        # 1. User requested model
        # 2. Or configured default
        selected_model = model if model else self._get_model()
        
        # Smart Parameter Adjustment
        # Mini/Reasoning models often require temperature=1.0 and max_completion_tokens
        # Standard GPT models behave better for translation with low temperature (0.2)
        is_reasoning_or_mini = "mini" in selected_model.lower() or "o1" in selected_model.lower()
        api_temperature = 1.0 if is_reasoning_or_mini else 0.2
        
        # Check cache
        if self.enable_cache:
            cache_key = _get_cache_key(
                f"{self.provider_name}:{selected_model}",
                json.dumps(strings, ensure_ascii=False),
                target_language,
                should_summarize
            )
            if cache_key in _translation_cache:
                cached, usage = _translation_cache[cache_key]
                if isinstance(usage, int): usage = {"input": 0, "output": 0, "total": usage}
                return self._apply_translations(data, cached), usage
        
        # Call OpenAI API
        prompt = self._create_prompt(strings, target_language, should_summarize)
        
        response = self._get_client().chat.completions.create(
            model=selected_model,
            messages=[
                {"role": "system", "content": "Fast Chinese translator. JSON output only."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=self.max_tokens,
            temperature=api_temperature,
            response_format={"type": "json_object"}
        )
        
        translated = json.loads(response.choices[0].message.content)
        
        usage = {
            "input": response.usage.prompt_tokens if response.usage else 0,
            "output": response.usage.completion_tokens if response.usage else 0,
            "total": response.usage.total_tokens if response.usage else 0
        }
        
        # Cache result
        if self.enable_cache:
            _translation_cache[cache_key] = (translated, usage)
        
        return self._apply_translations(data, translated), usage


# Singleton instances
deepseek_translator = DeepSeekTranslator()
openai_translator = OpenAITranslator()

