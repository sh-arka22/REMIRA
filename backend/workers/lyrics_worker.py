# backend/workers/lyrics_worker.py

import re
from typing import List

from .summary_worker import _call_llmstudio

_NON_ASCII_RE = re.compile(r"[^\x09\x0A\x0D\x20-\x7E]")
_STOPWORDS = {
    "the",
    "and",
    "with",
    "from",
    "that",
    "this",
    "those",
    "these",
    "into",
    "about",
    "their",
    "there",
    "they",
    "them",
    "we",
    "our",
    "ours",
    "your",
    "yours",
    "over",
    "under",
    "around",
    "were",
    "been",
    "have",
    "has",
    "had",
    "you",
    "for",
    "just",
    "like",
    "through",
}


def _looks_like_valid_lyrics(text: str) -> bool:
    if not text:
        return False

    if "[Verse" not in text or "[Chorus]" not in text:
        return False

    if _NON_ASCII_RE.search(text):
        return False

    words = text.split()
    if len(words) < 20:
        return False

    return True


def _extract_keywords(summary: str, limit: int = 12) -> List[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z'-]*", summary)
    keywords = []
    for token in tokens:
        lowered = token.lower()
        if len(token) < 3 or lowered in _STOPWORDS:
            continue
        if token not in keywords:
            keywords.append(token)
        if len(keywords) >= limit:
            break
    return keywords


def _make_fallback_lines(
    base_lines: List[str],
    target_count: int,
    keywords: List[str],
    mood: str,
) -> List[str]:
    if not keywords:
        keywords = ["memories", "family", "laughter", "home"]

    lines: List[str] = []
    idx = 0
    for line in base_lines:
        if len(lines) >= target_count:
            break
        lines.append(line)

    while len(lines) < target_count:
        keyword = keywords[idx % len(keywords)]
        lines.append(f"{keyword.capitalize()} in {mood.lower()} light we keep.")
        idx += 1

    return lines[:target_count]


def _fallback_lyrics(
    summary: str,
    genre: str,
    mood: str,
    lines_per_verse: int,
    num_verses: int,
) -> str:
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", summary.strip())
        if sentence.strip()
    ]
    if not sentences:
        sentences = [
            "We gather together, sharing the stories that make this family ours."
        ]

    keywords = _extract_keywords(summary)

    verses = []
    for idx in range(num_verses):
        sentence = sentences[idx % len(sentences)]
        base_lines = [
            sentence.rstrip("."),
            f"{mood.capitalize()} echoes in a {genre.lower()} sway.",
            f"{' and '.join(keywords[:2]) or 'Family memories'} dance in the frame.",
            "Holding to the quiet light of home.",
        ]
        verse_lines = _make_fallback_lines(base_lines, lines_per_verse, keywords, mood)
        verses.append(f"[Verse {idx + 1}]\n" + "\n".join(verse_lines))

    chorus_base = [
        f"Hold on to this {mood.lower()} glow tonight.",
        f"Family hearts beating in a {genre.lower()} song.",
        "Every laugh and tear we treasure tight.",
        "Love keeps the rhythm, steady and strong.",
    ]
    chorus_lines = _make_fallback_lines(
        chorus_base,
        max(4, min(6, lines_per_verse)),
        keywords,
        mood,
    )

    lyrics_sections: List[str] = []
    for idx, verse in enumerate(verses):
        lyrics_sections.append(verse)
        if idx == 0:
            lyrics_sections.append("[Chorus]\n" + "\n".join(chorus_lines))

    lyrics_sections.append("[Chorus]\n" + "\n".join(chorus_lines))

    return "\n\n".join(lyrics_sections)


def generate_lyrics(
    summary: str,
    genre: str,
    mood: str,
    lines_per_verse: int = 4,
    num_verses: int = 2,
) -> str:
    """
    Turn a narrative summary into structured song lyrics using your local LLMStudio model.
    """
    try:
        system_prompt = (
            "You are a professional songwriter. You write structured, singable lyrics "
            "with clear verses and choruses, suitable for modern music."
        )

        user_prompt = f"""
I have this story summary of some family photos:

{summary}

Write song lyrics based on this story.

Constraints:
- Genre feel: {genre}
- Mood: {mood}
- Structure: {num_verses} verses + 1 chorus that repeats
- Around {lines_per_verse} lines per verse, 4–6 lines for the chorus
- Make it nostalgic, specific, and visual, referencing scenes from the story
- Avoid profanity, keep it family-friendly

Format EXACTLY like this:

[Verse 1]
...

[Chorus]
...

[Verse 2]
...

Don't add explanations before or after the lyrics.
"""

        lyrics = _call_llmstudio(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_new_tokens=800,
            temperature=0.9,
        )
        if not _looks_like_valid_lyrics(lyrics):
            raise ValueError("LLM returned low-quality lyrics")

        return lyrics
    except Exception as e:
        print(f"LLMStudio unavailable, using fallback lyrics: {e}")
        return _fallback_lyrics(
            summary=summary,
            genre=genre,
            mood=mood,
            lines_per_verse=lines_per_verse,
            num_verses=num_verses,
        )
