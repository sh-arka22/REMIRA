# backend/workers/summary_worker.py

from typing import List
import os
import requests
import re


def _call_llmstudio(
    system_prompt: str,
    user_prompt: str,
    max_new_tokens: int = 512,
    temperature: float = 0.7,
) -> str:
    """
    Call a local LLMStudio / LM Studio server via an OpenAI-compatible HTTP API.

    Because this backend runs on Modal in the cloud, your local LLMStudio
    must be reachable via a public URL (for example using ngrok or Cloudflare
    tunnel). Set:

      LLMSTUDIO_API_URL    = "https://<your-ngrok-domain>/v1/chat/completions"
      LLMSTUDIO_MODEL_NAME = "<your-model-name>"
      LLMSTUDIO_API_KEY    = "<optional, if your server expects it>"
    """
    base_url = os.environ.get("LLMSTUDIO_API_URL")
    model_name = os.environ.get("LLMSTUDIO_MODEL_NAME", "local-model")

    if not base_url:
        raise RuntimeError(
            "LLMSTUDIO_API_URL is not set. "
            "Set it to your LLMStudio/LM Studio chat completions endpoint "
            "(e.g. https://<your-ngrok-domain>/v1/chat/completions)."
        )

    url = base_url.rstrip("/")
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_new_tokens,
        "stream": False,
    }

    headers = {"Content-Type": "application/json"}
    api_key = os.environ.get("LLMSTUDIO_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        # Fallback if LLMStudio is not available
        print(f"Warning: LLMStudio not accessible ({e}). Using fallback response.")
        return f"Generated response for: {user_prompt[:100]}..."


_NON_ASCII_RE = re.compile(r"[^\x09\x0A\x0D\x20-\x7E]")


def _looks_like_valid_summary(text: str) -> bool:
    if not text:
        return False

    alpha_ratio = sum(ch.isalpha() for ch in text) / max(len(text), 1)
    if alpha_ratio < 0.4:
        return False

    if _NON_ASCII_RE.search(text):
        return False

    if len(text.split()) < 8:
        return False

    return True


def _fallback_summary(captions: List[str]) -> str:
    if len(captions) == 1:
        summary = (
            f"This image shows {captions[0]}. "
            "A precious moment capturing the warmth and connection of family memories."
        )
    elif len(captions) == 2:
        summary = (
            f"These images capture {captions[0]} and {captions[1]}. "
            "Together they tell a story of family bonds and cherished moments."
        )
    else:
        first_captions = captions[:2]
        summary = (
            f"These photos show {', '.join(first_captions)}, and more beautiful moments. "
            "Each image captures the love, joy, and connection that define these precious family memories."
        )

    return summary


def summarize_captions(captions: List[str]) -> str:
    """
    Given a list of image captions, produce a single narrative summary
    using your local LLMStudio model.
    """
    captions_text = "\n".join(f"- {c}" for c in captions)
    
    # Try using LLMStudio, fallback to simple summary if unavailable
    try:
        system_prompt = (
            "You are a storyteller. Given a list of photo captions, "
            "write a short, cohesive narrative summarizing the scene, people, "
            "and emotions that connect these images."
        )

        user_prompt = f"""
Here are the captions for some family photos:

{captions_text}

Write a 2–3 sentence narrative summary that captures the key moments, 
people, and feelings. Make it personal and evocative.
"""

        summary = _call_llmstudio(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_new_tokens=256,
            temperature=0.7,
        )
        if not _looks_like_valid_summary(summary):
            raise ValueError("LLM returned a low-quality summary")

        return summary
    except Exception as e:
        print(f"LLMStudio unavailable, using fallback summary: {e}")
        return _fallback_summary(captions)
