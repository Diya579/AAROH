"""Lexical metrics extraction from normalized text (Slice 2.2).

Extracts basic statistical and structural text properties deterministically.
"""

from __future__ import annotations

import re
import string
from typing import Optional

from backend.ml.features.types import LexicalMetrics

# Sentence terminators including Latin and Indic dandas (।, ॥)
SENTENCE_TERMINATORS_PATTERN = re.compile(r"[.!?\n\u0964\u0965]+")

# Indic and Latin punctuation set
PUNCTUATION_CHARS = frozenset(
    set(string.punctuation).union({"\u0964", "\u0965", "¿", "¡", "…", "—", "–", "“", "”", "‘", "’"})
)


def extract_lexical_metrics(
    clean_text: str, raw_text: Optional[str] = None
) -> LexicalMetrics:
    """Computes lexical statistics from clean text and optional raw text.

    Deterministic and handles zero/minimal tokens safely without dividing by zero.
    """
    if not clean_text or not clean_text.strip():
        return LexicalMetrics(
            word_count=0,
            character_count=0,
            sentence_count=0,
            average_word_length=0.0,
            uppercase_ratio=0.0,
            punctuation_ratio=0.0,
        )

    words = clean_text.strip().split()
    word_count = len(words)
    char_count = len(clean_text)

    # Sentence count
    raw_sentences = SENTENCE_TERMINATORS_PATTERN.split(clean_text)
    sentence_count = len([s for s in raw_sentences if s.strip()])
    if sentence_count == 0 and word_count > 0:
        sentence_count = 1

    # Average word length
    total_word_chars = sum(len(w) for w in words)
    avg_word_length = round(total_word_chars / max(1, word_count), 3)

    # Uppercase ratio (computed from raw_text if provided)
    source_for_casing = raw_text if raw_text is not None else clean_text
    alpha_chars = [c for c in source_for_casing if c.isalpha()]
    if alpha_chars:
        upper_chars = [c for c in alpha_chars if c.isupper()]
        uppercase_ratio = round(len(upper_chars) / len(alpha_chars), 3)
    else:
        uppercase_ratio = 0.0

    # Punctuation ratio
    source_for_punct = raw_text if raw_text is not None else clean_text
    punct_count = sum(1 for c in source_for_punct if c in PUNCTUATION_CHARS)
    punctuation_ratio = round(punct_count / max(1, len(source_for_punct)), 3)

    return LexicalMetrics(
        word_count=word_count,
        character_count=char_count,
        sentence_count=sentence_count,
        average_word_length=avg_word_length,
        uppercase_ratio=uppercase_ratio,
        punctuation_ratio=punctuation_ratio,
    )
