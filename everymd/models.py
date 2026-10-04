"""The one place that decides which AI model everymd uses. Nothing else in the code names a provider.

Switch the model by changing MODEL below, or without touching code by setting EVERYMD_MODEL in .env:

    EVERYMD_MODEL=openai:gpt-6-luna            OpenAI (the default, owner's decision 0004)
    EVERYMD_MODEL=anthropic:<model>            Anthropic        key ANTHROPIC_API_KEY
    EVERYMD_MODEL=google_genai:<model>         Google Gemini    key GOOGLE_API_KEY
    EVERYMD_MODEL=ollama:<model>               local, open      needs langchain-ollama, no key
    EVERYMD_MODEL=openai:<model>               any OpenAI-compatible server (vLLM, LM Studio, llama.cpp,
    EVERYMD_BASE_URL=http://host:8000/v1         OpenRouter, Together, Groq ...); key in EVERYMD_API_KEY

The name is "provider:model"; any provider LangChain's init_chat_model knows works once its package is in
requirements.txt and the image is rebuilt. OpenAI, Anthropic and Google packages are already in the image. The model must support tool calling. If it can't
read images, set EVERYMD_MODEL_SEES_IMAGES=false and the copy-editor works from the text alone.
"""

from __future__ import annotations

import base64
import io
import os
import re

from langchain_core.language_models import BaseChatModel

MODEL = "openai:gpt-6-luna"

# Settings are read at call time, so a notebook or test can change them after import.
def model_id() -> str:
    return os.environ.get("EVERYMD_MODEL") or MODEL


def base_url() -> str | None:
    """An OpenAI-compatible server to call instead of the provider's own API."""
    return os.environ.get("EVERYMD_BASE_URL") or None


def sees_images() -> bool:
    return os.environ.get("EVERYMD_MODEL_SEES_IMAGES", "true").lower() not in ("0", "false", "no")


# Production reasoning effort for OpenAI. Tests and development runs set EVERYMD_REASONING_EFFORT=low.
DEFAULT_REASONING_EFFORT = "medium"


def reasoning_effort() -> str:
    return os.environ.get("EVERYMD_REASONING_EFFORT", DEFAULT_REASONING_EFFORT)


def provider_settings(provider: str) -> dict:
    """Extra settings for a provider's model. Add a line here for another provider's options."""
    if provider == "openai" and not base_url():
        return {"reasoning_effort": reasoning_effort()}
    return {}


# The environment variable holding each provider's key, for a clear error before any work starts.
API_KEYS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google_genai": "GOOGLE_API_KEY",
    "mistralai": "MISTRAL_API_KEY",
    "groq": "GROQ_API_KEY",
    "together": "TOGETHER_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "fireworks": "FIREWORKS_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "xai": "XAI_API_KEY",
}


def split(name: str) -> tuple[str, str]:
    """("ollama", "qwen3-vl:8b") from "ollama:qwen3-vl:8b". A bare name is an OpenAI model, as before."""
    provider, sep, rest = name.partition(":")
    return (provider, rest) if sep else ("openai", name)


def build(model: str | BaseChatModel | None = None) -> BaseChatModel:
    """The chat model: a ready LangChain model, or a "provider:model" name (default: model_id())."""
    if isinstance(model, BaseChatModel):
        return model
    from dotenv import find_dotenv, load_dotenv
    from langchain.chat_models import init_chat_model

    load_dotenv(find_dotenv(usecwd=True))
    name = model or model_id()
    provider, model_name = split(name)
    settings = provider_settings(provider)
    if base_url():
        settings |= {"base_url": base_url(), "api_key": os.environ.get("EVERYMD_API_KEY") or "not-needed"}
    elif API_KEYS.get(provider) and not os.environ.get(API_KEYS[provider]):
        raise RuntimeError(f"llm_layer=True with {name} needs {API_KEYS[provider]} (put it in .env), or pass llm_layer=False.")
    try:
        return init_chat_model(model_name, model_provider=provider, **settings)
    except ImportError as exc:
        raise RuntimeError(f"{name} needs its LangChain package: add it to requirements.txt and rebuild ({exc})") from exc


# How a page image is sent. OpenAI takes a "detail" level; other providers get LangChain's standard
# image block, which each provider package translates to its own format.
IMAGE_DETAIL = "high"
MAX_IMAGE_SIDE = 2400  # downscale page images whose longest side is bigger


def image_block(image, llm: BaseChatModel) -> dict:
    image = image.convert("RGB")
    if max(image.size) > MAX_IMAGE_SIDE:
        image = image.copy()
        image.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    data = base64.b64encode(buffer.getvalue()).decode("ascii")
    if provider_of(llm) == "openai":
        return {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{data}", "detail": IMAGE_DETAIL}}
    return {"type": "image", "base64": data, "mime_type": "image/png"}


def provider_of(llm: BaseChatModel) -> str | None:
    return llm._get_ls_params().get("ls_provider")


def name_of(llm: BaseChatModel) -> str:
    return getattr(llm, "model_name", None) or getattr(llm, "model", None) or type(llm).__name__


def profile_key(llm: BaseChatModel) -> str | None:
    """The `provider:model` key Deep Agents uses to look up harness profiles, or None if unknown."""
    provider = provider_of(llm)
    identifier = getattr(llm, "model_name", None) or getattr(llm, "model", None)
    return f"{provider}:{identifier}" if provider and identifier else None


def price_of(model: str) -> dict[str, float] | None:
    """The price row for a model: its exact name, or a dated snapshot of it (`gpt-6-luna-2026-09-01`)."""
    for name, price in PRICES.items():
        if model == name or re.fullmatch(re.escape(name) + r"-\d{4}-\d{2}-\d{2}", model):
            return price
    return None


# Estimated cost only. USD per 1M tokens by model name; a model not listed gets no estimate.
PRICES_CHECKED = "2026-10-03"
PRICES_SOURCE = "https://developers.openai.com/api/docs/models/gpt-6-luna"
PRICES: dict[str, dict[str, float]] = {
    "gpt-6-luna": {"input": 0.10, "cached_input": 0.01, "cache_write": 0.125, "output": 0.50},
}
