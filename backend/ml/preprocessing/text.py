"""Text normalization and multilingual Unicode preservation utilities.

Provides modular, reusable text preprocessing routines designed for Indic and
multilingual text processing. Preserves Unicode combining marks, matras, and
essential Indic ligatures (ZWJ/ZWNJ) while removing invisible noise and normalizing
whitespace deterministically.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

from backend.ml.preprocessing.types import NormalizedText, TextQualityMetrics

# Characters that should be cleaned (BOM, zero-width space, bidi controls)
# Note: \u200c (ZWNJ) and \u200d (ZWJ) are intentionally NOT in this set because
# they are linguistically essential in Indic scripts (e.g., Devanagari, Bengali).
INVISIBLE_CHARS_PATTERN = re.compile(
    r"[\ufeff\u200b\u200e\u200f\u202a-\u202e\u2060\u00ad]"
)

# Control characters to remove (C0 and C1 controls, except standard whitespace)
CONTROL_CHARS_PATTERN = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]"
)

# Unicode script ranges for script detection
SCRIPT_RANGES: tuple[tuple[str, int, int], ...] = (
    ("Devanagari", 0x0900, 0x097F),
    ("Bengali", 0x0980, 0x09FF),
    ("Gurmukhi", 0x0A00, 0x0A7F),
    ("Gujarati", 0x0A80, 0x0AFF),
    ("Odia", 0x0B00, 0x0B7F),
    ("Tamil", 0x0B80, 0x0BFF),
    ("Telugu", 0x0C00, 0x0C7F),
    ("Kannada", 0x0C80, 0x0CFF),
    ("Malayalam", 0x0D00, 0x0D7F),
    ("Latin", 0x0041, 0x007A),  # Basic Latin
)


def normalize_unicode(text: str, form: str = "NFKC") -> str:
    """Standardizes Unicode representation to a canonical form (default NFKC).

    Ensures consistent representation of precomposed and decomposed glyphs
    across different platforms and mobile keyboards.
    """
    if not text:
        return ""
    return unicodedata.normalize(form, text)


def clean_invisible_characters(text: str) -> str:
    """Removes BOM, zero-width spaces, directional marks, and control codes.

    Preserves Zero-Width Joiner (ZWJ) and Zero-Width Non-Joiner (ZWNJ) which
    are required for Indic script conjuncts and half-forms.
    """
    if not text:
        return ""
    text = INVISIBLE_CHARS_PATTERN.sub("", text)
    text = CONTROL_CHARS_PATTERN.sub("", text)
    return text


def normalize_whitespace(text: str) -> str:
    """Collapses consecutive whitespace (spaces, tabs, newlines) into single spaces.

    Also normalizes non-breaking spaces and other Unicode spaces to ASCII space.
    """
    if not text:
        return ""
    # Standardize non-breaking and unusual Unicode spaces
    text = text.replace("\u00a0", " ").replace("\u2000", " ").replace("\u2001", " ")
    text = text.replace("\u2002", " ").replace("\u2003", " ").replace("\u3000", " ")
    # Collapse consecutive whitespace characters
    return re.sub(r"\s+", " ", text).strip()


def normalize_casing(text: str, lowercase: bool = True) -> str:
    """Applies Unicode-aware casing transformation.

    In Python, str.lower() is Unicode-aware: Latin/Cyrillic are lowercased while
    non-cased scripts (Devanagari, Bengali, Tamil, etc.) remain intact.
    """
    if not text:
        return ""
    return text.lower() if lowercase else text


def detect_scripts(text: str) -> tuple[str, ...]:
    """Identifies the writing scripts present in the text deterministically."""
    if not text:
        return ()

    detected = set()
    for char in text:
        code = ord(char)
        for script_name, start, end in SCRIPT_RANGES:
            if start <= code <= end:
                detected.add(script_name)
                break

    return tuple(sorted(detected))


def evaluate_text_quality(
    text: str, min_words_threshold: int = 3, min_chars_threshold: int = 10
) -> TextQualityMetrics:
    """Evaluates lexical metrics and quality flags of a text string."""
    if not text or not text.strip():
        return TextQualityMetrics(
            char_count=0,
            word_count=0,
            line_count=0,
            is_empty=True,
            is_very_short=True,
            detected_scripts=(),
            has_multilingual_chars=False,
        )

    clean = text.strip()
    char_count = len(clean)
    words = clean.split()
    word_count = len(words)
    lines = [line for line in text.splitlines() if line.strip()]
    line_count = len(lines)

    scripts = detect_scripts(clean)
    has_non_latin = any(s != "Latin" for s in scripts)

    is_very_short = word_count < min_words_threshold or char_count < min_chars_threshold

    return TextQualityMetrics(
        char_count=char_count,
        word_count=word_count,
        line_count=line_count,
        is_empty=False,
        is_very_short=is_very_short,
        detected_scripts=scripts,
        has_multilingual_chars=has_non_latin,
    )


def preprocess_text(
    text: Optional[str],
    language: Optional[str] = None,
    *,
    lowercase: bool = True,
    unicode_form: str = "NFKC",
) -> Optional[NormalizedText]:
    """Chains all text preprocessing steps deterministically.

    Returns None if the input text is None.
    If input is empty string or only whitespace, returns NormalizedText with clean="".
    """
    if text is None:
        return None

    # Step 1: Unicode canonical normalization
    normalized = normalize_unicode(text, form=unicode_form)

    # Step 2: Remove invisible noise and control characters
    cleaned = clean_invisible_characters(normalized)

    # Step 3: Whitespace normalization
    collapsed = normalize_whitespace(cleaned)

    # Step 4: Casing (Unicode aware)
    final_text = normalize_casing(collapsed, lowercase=lowercase)

    # Step 5: Quality evaluation
    quality = evaluate_text_quality(final_text)

    return NormalizedText(
        raw=text,
        clean=final_text,
        language=language,
        quality=quality,
    )
