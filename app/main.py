from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Literal

from app.config import settings
from app.models import (
    TranslationRequest,
    TranslationResponse,
    BatchTranslationRequest,
    BatchTranslationResponse,
    HealthResponse
)
from app.translator import deepseek_translator, openai_translator

# Initialize FastAPI app
app = FastAPI(
    title="Chinese Translation API",
    description="""
## 🇨🇳 → 🌍 Chinese Translation API

**Multi-Provider Translation API** with DeepSeek and OpenAI support.

### Providers:
| Provider | Endpoint Prefix | Model |
|----------|-----------------|-------|
| DeepSeek | `/deepseek/*` | deepseek-chat |
| OpenAI | `/openai/*` | gpt-4.1-mini |

### Supported Target Languages:
- `uz` - Uzbek (O'zbek)
- `ru` - Russian (Русский)  
- `en` - English

### Features:
- ⚡ **Fast**: Optimized prompts + caching
- 🧠 **Smart**: Auto-summarization for verbose text
- 🔄 **Flexible**: Choose your AI provider
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===========================================
# Health Endpoints
# ===========================================

@app.get("/", tags=["Health"])
async def root():
    """API health check with provider status."""
    
    def mask_key(key: str) -> str:
        if len(key) > 10:
            return f"{key[:8]}...{key[-4:]}"
        return "NOT SET" if not key else "SET (short)"
    
    return {
        "status": "healthy",
        "version": "2.0.0",
        "providers": {
            "deepseek": {
                "configured": deepseek_translator.is_configured(),
                "model": settings.DEEPSEEK_MODEL,
                "key_preview": mask_key(settings.DEEPSEEK_API_KEY)
            },
            "openai": {
                "configured": openai_translator.is_configured(),
                "model": settings.OPENAI_MODEL,
                "key_preview": mask_key(settings.OPENAI_API_KEY)
            }
        },
        "supported_languages": settings.SUPPORTED_TARGET_LANGUAGES
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return await root()


# ===========================================
# DeepSeek Translation Endpoints
# ===========================================

@app.post("/deepseek/translate", response_model=TranslationResponse, tags=["DeepSeek"])
async def deepseek_translate(request: TranslationRequest):
    """
    Translate Chinese JSON using **DeepSeek AI**.
    
    Fast and cost-effective translations.
    """
    if not deepseek_translator.is_configured():
        raise HTTPException(status_code=500, detail="DeepSeek API key not configured")
    
    try:
        translated, usage = await deepseek_translator.translate(
            data=request.data,
            target_language=request.target_language,
            keys_to_translate=request.keys_to_translate,
            summarize=request.summarize
        )
        return TranslationResponse(
            success=True,
            translated_data=translated,
            target_language=request.target_language,
            provider="deepseek",
            summarized=request.summarize or False,
            total_tokens=usage["total"],
            input_tokens=usage["input"],
            output_tokens=usage["output"]
        )
    except Exception as e:
        return TranslationResponse(
            success=False,
            translated_data=None,
            target_language=request.target_language,
            provider="deepseek",
            error=str(e)
        )


@app.post("/deepseek/translate/batch", response_model=BatchTranslationResponse, tags=["DeepSeek"])
async def deepseek_translate_batch(request: BatchTranslationRequest):
    """Batch translate multiple items using DeepSeek."""
    if not deepseek_translator.is_configured():
        raise HTTPException(status_code=500, detail="DeepSeek API key not configured")
    
    return await _batch_translate(deepseek_translator, request, "deepseek")


@app.get("/deepseek/translate/simple", response_model=TranslationResponse, tags=["DeepSeek"])
async def deepseek_translate_simple(
    text: str = Query(..., description="Chinese text"),
    lang: Literal["uz", "ru", "en"] = Query(default="en"),
    summarize: bool = Query(default=False)
):
    """Quick GET translation with DeepSeek."""
    if not deepseek_translator.is_configured():
        raise HTTPException(status_code=500, detail="DeepSeek API key not configured")
    
    try:
        translated, usage = await deepseek_translator.translate(
            data={"text": text},
            target_language=lang,
            summarize=summarize
        )
        return TranslationResponse(
            success=True,
            translated_data=translated,
            target_language=lang,
            provider="deepseek",
            summarized=summarize,
            total_tokens=usage["total"],
            input_tokens=usage["input"],
            output_tokens=usage["output"]
        )
    except Exception as e:
        return TranslationResponse(success=False, translated_data=None, target_language=lang, provider="deepseek", error=str(e))


# ===========================================
# OpenAI Translation Endpoints
# ===========================================

@app.post("/openai/translate", response_model=TranslationResponse, tags=["OpenAI"])
async def openai_translate(request: TranslationRequest):
    """
    Translate Chinese JSON using **OpenAI**.
    
    Supports dynamic model selection:
    - **gpt-5.1**: High intelligence (Default)
    - **gpt-5-mini**: Fast & cost effective
    """
    if not openai_translator.is_configured():
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    try:
        translated, usage = await openai_translator.translate(
            data=request.data,
            target_language=request.target_language,
            keys_to_translate=request.keys_to_translate,
            summarize=request.summarize,
            model=request.model
        )
        return TranslationResponse(
            success=True,
            translated_data=translated,
            target_language=request.target_language,
            provider=f"openai ({request.model or settings.OPENAI_MODEL})",
            summarized=request.summarize or False,
            total_tokens=usage["total"],
            input_tokens=usage["input"],
            output_tokens=usage["output"]
        )
    except Exception as e:
        return TranslationResponse(
            success=False,
            translated_data=None,
            target_language=request.target_language,
            provider="openai",
            error=str(e)
        )


@app.post("/openai/translate/batch", response_model=BatchTranslationResponse, tags=["OpenAI"])
async def openai_translate_batch(request: BatchTranslationRequest):
    """Batch translate multiple items using OpenAI."""
    if not openai_translator.is_configured():
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    return await _batch_translate(openai_translator, request, "openai")


@app.get("/openai/translate/simple", response_model=TranslationResponse, tags=["OpenAI"])
async def openai_translate_simple(
    text: str = Query(..., description="Chinese text"),
    lang: Literal["uz", "ru", "en"] = Query(default="en"),
    summarize: bool = Query(default=False)
):
    """Quick GET translation with OpenAI."""
    if not openai_translator.is_configured():
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    try:
        translated, usage = await openai_translator.translate(
            data={"text": text},
            target_language=lang,
            summarize=summarize
        )
        return TranslationResponse(
            success=True,
            translated_data=translated,
            target_language=lang,
            provider="openai",
            summarized=summarize,
            total_tokens=usage["total"],
            input_tokens=usage["input"],
            output_tokens=usage["output"]
        )
    except Exception as e:
        return TranslationResponse(success=False, translated_data=None, target_language=lang, provider="openai", error=str(e))


# ===========================================
# Legacy Endpoints (DeepSeek default)
# ===========================================

@app.post("/translate", response_model=TranslationResponse, tags=["Unified"])
async def translate_unified(request: TranslationRequest):
    """
    Unified Endpoint: Choose provider and model dynamically.
    
    defaults:
    - provider: defined in DEFAULT_PROVIDER (default: deepseek)
    - model: default for that provider
    """
    # Determine provider (default to deepseek if not specified)
    provider = request.provider or "deepseek"
    
    if provider == "openai":
        return await openai_translate(request)
    elif provider == "deepseek":
        return await deepseek_translate(request)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")


@app.get("/translate/simple", response_model=TranslationResponse, tags=["Legacy"])
async def translate_simple_legacy(
    text: str = Query(...),
    lang: Literal["uz", "ru", "en"] = Query(default="en"),
    summarize: bool = Query(default=False)
):
    """Legacy simple endpoint - uses DeepSeek."""
    return await deepseek_translate_simple(text, lang, summarize)


# ===========================================
# Info Endpoints
# ===========================================

@app.get("/languages", tags=["Info"])
async def get_languages():
    """Get supported languages."""
    return {
        "source": {"code": "zh", "name": "Chinese"},
        "targets": [
            {"code": "uz", "name": "Uzbek"},
            {"code": "ru", "name": "Russian"},
            {"code": "en", "name": "English"}
        ]
    }


@app.get("/providers", tags=["Info"])
async def get_providers():
    """Get available translation providers."""
    return {
        "providers": [
            {
                "name": "deepseek",
                "endpoint": "/deepseek/translate",
                "model": settings.DEEPSEEK_MODEL,
                "configured": deepseek_translator.is_configured()
            },
            {
                "name": "openai",
                "endpoint": "/openai/translate",
                "model": settings.OPENAI_MODEL,
                "configured": openai_translator.is_configured()
            }
        ]
    }


# ===========================================
# Helper Functions
# ===========================================

async def _batch_translate(translator, request: BatchTranslationRequest, provider: str) -> BatchTranslationResponse:
    """Shared batch translation logic."""
    results = []
    errors = []
    total_tokens = 0
    successful = 0
    
    for idx, item in enumerate(request.items):
        try:
            translated, tokens = await translator.translate(
                data=item,
                target_language=request.target_language,
                keys_to_translate=request.keys_to_translate,
                summarize=request.summarize
            )
            results.append(translated)
            total_tokens += tokens
            successful += 1
        except Exception as e:
            errors.append(f"Item {idx}: {str(e)}")
            results.append(item)
    
    return BatchTranslationResponse(
        success=len(errors) == 0,
        translated_items=results,
        target_language=request.target_language,
        provider=provider,
        total_items=len(request.items),
        successful_translations=successful,
        failed_translations=len(errors),
        total_tokens_used=total_tokens,
        errors=errors if errors else None
    )


# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"error": str(exc), "success": False})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
