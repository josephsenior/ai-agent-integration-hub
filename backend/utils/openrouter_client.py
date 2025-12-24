"""Gemini LLM client utility using LangChain's GooglePalm (API key).

This helper constructs a LangChain `GooglePalm` chat model using an
API key from the `GEMINI_API_KEY` environment variable.
"""

import os
import sys
from typing import Optional

# Import at top level to avoid E402
from langchain_compat import init_chat_model

# DEBUG: snapshot at import time
print("DEBUG import: os.environ GEMINI_MODEL =", repr(os.environ.get('GEMINI_MODEL')), file=sys.stderr)

try:
    _HAS_GOOGLE_PALM = True
except Exception:
    _HAS_GOOGLE_PALM = False


def create_llm(
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    api_key: Optional[str] = None,
) -> object:
    # DEBUG: snapshot at function entry
    print("DEBUG create_llm entry: os.environ GEMINI_MODEL =", repr(os.environ.get('GEMINI_MODEL')), file=sys.stderr)
    gemini_key = api_key or os.getenv("GEMINI_API_KEY")
    gemini_model = model_name or os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

    # Clean approach: prefer direct use of google.genai when a GEMINI API key
    # is provided to avoid any LangChain/provider code paths that may default
    # to other providers or vendored model names.
    if gemini_key:
        try:
            import google.genai as genai

            client = genai.Client(api_key=gemini_key)

            class _GenAIWrapper:
                def __init__(self, client, model, temperature=None):
                    self.client = client
                    self.model = model
                    self.temperature = temperature

                def invoke(self, prompt: str):
                    return self.client.models.generate_content(model=self.model, contents=prompt)

            print(f"DEBUG create_llm final: GEMINI_MODEL={gemini_model} GEMINI_KEY={'set' if bool(gemini_key) else 'unset'}", file=sys.stderr)
            return _GenAIWrapper(client, gemini_model, temperature)
        except Exception:
            # If google.genai isn't available, fall back to LangChain below.
            pass

    # Fallback: try LangChain google_genai provider if available
    try:
        from importlib import util

        if util.find_spec("langchain_google_genai"):
            from langchain_google_genai.chat_models import ChatGoogleGenerativeAI

            kwargs = {"model": gemini_model}
            if temperature is not None:
                kwargs["temperature"] = temperature
            if gemini_key is not None:
                kwargs["api_key"] = gemini_key
            return ChatGoogleGenerativeAI(**kwargs)
    except Exception:
        pass

    try:
        base_kwargs = {}
        if temperature is not None:
            base_kwargs["temperature"] = temperature
        return init_chat_model(model_name=gemini_model, model_provider="google_genai", **base_kwargs)
    except Exception as e:  # pragma: no cover - environment dependent
        raise ImportError(
            "Could not initialize Gemini model. Install google-genai SDK or langchain-google-genai. Original error: "
            + str(e)
        )
