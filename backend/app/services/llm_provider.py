

import logging
from typing import Optional, Dict, Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

logger = logging.getLogger("langchain_provider")

# ----------------------------------------------------------------------
# Model Registry – map logical names to actual model identifiers
# ----------------------------------------------------------------------
MODEL_REGISTRY = {
    # Reasoning / General purpose
    "reasoning_best": "llama-3.3-70b-versatile",      # 70B, strong reasoning
    "reasoning_fast": "llama3-8b-8192",               # 8B, fast
    "reasoning_long": "gemini-1.5-pro",               # 1M context (via Gemini)
    
    # Function calling / Tool use
    "function_calling": "llama-3.3-70b-versatile",    # Groq supports tool calls
    
    # Multilingual (Indian languages)
    "multilingual": "llama-3.3-70b-versatile",        # Defaulting to 70B for strong multi-lingual
    
    # Vision (if you need multimodal)
    "vision": "llama-3.2-90b-vision-preview",         # Llama 3.2 90B Vision
    
    # Fallback for safety / content moderation
    "safety": "llama-3.3-70b-versatile",              # Best overall OSS fallback
}

def get_llm(model_name: str, temperature: float = 0.1, **kwargs) -> Optional[BaseChatModel]:
    """
    Factory function to get a specific model by name.
    Supports Groq and Google models (Gemini). Returns None if the model isn't available.
    """
    # Try Groq first
    if settings.GROQ_API_KEY:
        try:
            return ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model_name=model_name,
                temperature=temperature,
                max_retries=2,
                **kwargs
            )
        except Exception as e:
            logger.warning(f"Groq model {model_name} unavailable: {e}")
    
    # Try Gemini if the model name matches a Gemini variant
    if settings.GEMINI_API_KEY and "gemini" in model_name.lower():
        try:
            return ChatGoogleGenerativeAI(
                google_api_key=settings.GEMINI_API_KEY,
                model=model_name,
                temperature=temperature,
                max_retries=2,
                **kwargs
            )
        except Exception as e:
            logger.warning(f"Gemini model {model_name} unavailable: {e}")
    
    logger.error(f"No provider available for model {model_name}")
    return None

def get_enterprise_llm(temperature: float = 0.1) -> BaseChatModel:
    """
    Returns a unified LangChain ChatModel with fallbacks across providers.
    Uses primary Groq with a fallback to Gemini if available.
    You can also override the model by setting an environment variable.
    """
    # Determine which model to use as primary
    primary_model_name = settings.PRIMARY_LLM_MODEL or MODEL_REGISTRY["reasoning_best"]
    
    # Try primary model
    primary = get_llm(primary_model_name, temperature=temperature)
    
    # Define fallback models (in order)
    fallback_models = []
    if settings.GEMINI_API_KEY:
        fallback_models.append(get_llm("gemini-1.5-pro", temperature=temperature))
    if settings.GROQ_API_KEY and primary_model_name != "llama-3.3-70b-versatile":
        # Fallback to a known good Groq model if primary is not available
        fallback_models.append(get_llm("llama-3.3-70b-versatile", temperature=temperature))
    # Filter out None values
    fallback_models = [m for m in fallback_models if m is not None]
    
    if primary:
        if fallback_models:
            return primary.with_fallbacks(fallback_models)
        return primary
    elif fallback_models:
        return fallback_models[0]
    
    # No keys at all
    logger.error("No LLM API keys provided in environment.")
    raise RuntimeError("Missing Core LLM configurations for Intelligence Engine.")

# ----------------------------------------------------------------------
# Optional: Specialised functions for other modalities (TTS, STT)
# ----------------------------------------------------------------------
def get_tts_model():
    """
    Returns a Text-to-Speech model from Groq if available.
    (You would need a separate client – LangChain doesn't have TTS built-in.)
    """
    if not settings.GROQ_API_KEY:
        return None
    # This is a placeholder – you'd need to use Groq's TTS API directly.
    # Example: from groq import Groq; client = Groq(api_key=settings.GROQ_API_KEY)
    # Then client.audio.speech.create(...)
    return "Groq TTS models available: ElevenLabs TTS, Orpheus English, etc."

def get_stt_model():
    """
    Returns a Speech-to-Text model from Groq.
    """
    if not settings.GROQ_API_KEY:
        return None
    # Similar to TTS, you'd use the Groq client with the Whisper model.
    return "Whisper Large v3 / v3 Turbo available"