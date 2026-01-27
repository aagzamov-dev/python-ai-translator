from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class TranslationRequest(BaseModel):
    """Request model for translating Chinese JSON data."""
    
    data: Union[Dict[str, Any], List[Any]] = Field(
        ...,
        description="JSON data with Chinese text values to translate."
    )
    target_language: Literal["uz", "ru", "en"] = Field(
        default="en",
        description="Target language: uz (Uzbek), ru (Russian), en (English)."
    )
    keys_to_translate: Optional[List[str]] = Field(
        default=None,
        description="Specific keys to translate. None = all string values."
    )
    summarize: Optional[bool] = Field(
        default=None,
        description="Force summarization. None = auto-detect."
    )
    model: Optional[str] = Field(
        default=None,
        description="Specific model to use (e.g. 'gpt-5-mini', 'deepseek-chat')."
    )
    provider: Optional[Literal["deepseek", "openai"]] = Field(
        default=None,
        description="API provider to use. If None, uses default from server config."
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "data": {
                    "title": "新款智能手机",
                    "description": "这是一款高品质智能手机"
                },
                "target_language": "uz"
            }]
        }
    }


class TranslationResponse(BaseModel):
    """Response model for translated JSON data."""
    
    success: bool
    translated_data: Optional[Union[Dict[str, Any], List[Any]]] = None
    target_language: str
    provider: Optional[str] = None
    summarized: bool = False
    error: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class BatchTranslationRequest(BaseModel):
    """Batch translation request."""
    
    items: List[Dict[str, Any]]
    target_language: Literal["uz", "ru", "en"] = "en"
    keys_to_translate: Optional[List[str]] = None
    summarize: Optional[bool] = None


class BatchTranslationResponse(BaseModel):
    """Batch translation response."""
    
    success: bool
    translated_items: List[Dict[str, Any]]
    target_language: str
    provider: str
    total_items: int
    successful_translations: int
    failed_translations: int
    total_tokens_used: int
    errors: Optional[List[str]] = None


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str
    version: str
    providers: Dict[str, Any]
    supported_languages: List[str]
