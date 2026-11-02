"""Gemini LLM client utility using LangChain's GooglePalm (API key).

This helper constructs a LangChain `GooglePalm` chat model using an
API key from the `GEMINI_API_KEY` environment variable.
"""

import os
import sys
from typing import Any, Optional, Protocol

from ..core.config import settings

# Lazy import - only import when needed to avoid errors if langchain structure changed
# from langchain.chat_models import init_chat_model

# DEBUG: snapshot at import time
print(
    "DEBUG import: os.environ GEMINI_MODEL =",
    repr(os.environ.get("GEMINI_MODEL")),
    file=sys.stderr,
)

try:
    _HAS_GOOGLE_PALM = True
except Exception:
    _HAS_GOOGLE_PALM = False


# Protocol for LLM interface
class LLMProtocol(Protocol):
    """Protocol for LLM interface."""

    def invoke(self, prompt: str) -> Any:
        """Invoke the LLM with a prompt."""
        ...


def create_llm(
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    api_key: Optional[str] = None,
) -> LLMProtocol:
    # DEBUG: snapshot at function entry
    print(
        "DEBUG create_llm entry: os.environ GEMINI_MODEL =",
        repr(os.environ.get("GEMINI_MODEL")),
        file=sys.stderr,
    )
    # Prefer explicit argument, then settings (which reads .env), then raw env var
    gemini_key = api_key or settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
    gemini_model = (
        model_name
        or settings.GEMINI_MODEL
        or os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    )

    # Clean approach: prefer direct use of google-genai ONLY.
    # We intentionally avoid any LangChain fallbacks here to sidestep
    # pydantic / version incompatibilities.
    if not gemini_key:
        raise ImportError(
            "GEMINI_API_KEY is not set. Please add it to your .env for Gemini support."
        )

    try:
        import google.genai as genai
        from google.genai import types
        from langchain_core.runnables import RunnableLambda

        client = genai.Client(api_key=gemini_key)

        def _invoke_gemini(prompt: Any) -> str:
            """Invoke Gemini model with LangChain-compatible interface."""
            # ChatPromptTemplate outputs a dict with "messages" key
            if isinstance(prompt, dict) and "messages" in prompt:
                messages = prompt["messages"]
                # Build conversation context from messages
                conversation_parts = []
                for msg in messages:
                    if hasattr(msg, "content"):
                        role = "user" if hasattr(msg, "type") and msg.type == "human" else "assistant"
                        conversation_parts.append(f"{role}: {msg.content}")
                    elif isinstance(msg, dict):
                        role = msg.get("role", "user")
                        content = msg.get("content", str(msg))
                        conversation_parts.append(f"{role}: {content}")
                    else:
                        conversation_parts.append(str(msg))
                content = "\n".join(conversation_parts)
            elif isinstance(prompt, str):
                content = prompt
            elif hasattr(prompt, "content"):
                content = prompt.content
            else:
                content = str(prompt)

            # Build config with temperature if provided
            config = None
            if temperature is not None:
                config = types.GenerateContentConfig(temperature=temperature)

            result = client.models.generate_content(
                model=gemini_model,
                contents=content,
                config=config,
            )
            
            # Extract text from Gemini response
            if hasattr(result, "text"):
                return result.text
            elif hasattr(result, "candidates") and result.candidates:
                candidate = result.candidates[0]
                if hasattr(candidate, "content"):
                    if hasattr(candidate.content, "parts"):
                        return "".join(
                            part.text for part in candidate.content.parts 
                            if hasattr(part, "text") and part.text
                        )
                    elif hasattr(candidate.content, "text"):
                        return candidate.content.text
            return str(result)

        # Wrap in RunnableLambda to make it compatible with LangChain's pipe operator
        runnable_llm = RunnableLambda(_invoke_gemini)

        print(
            f"DEBUG create_llm final: GEMINI_MODEL={gemini_model} GEMINI_KEY={'set' if bool(gemini_key) else 'unset'}",
            file=sys.stderr,
        )
        return runnable_llm
    except Exception as e:  # pragma: no cover - environment dependent
        raise ImportError(
            "Could not initialize Gemini model using google-genai. "
            "Ensure google-genai is installed in the venv and GEMINI_API_KEY is valid. "
            f"Original error: {e}"
        )
