from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend.voice.vad import VADResult


@dataclass
class SpeechRateResult:
    speech_rate: Optional[float]
    estimated_syllables: Optional[int]
    speech_duration_seconds: Optional[float]
    reason: Optional[str] = None


# ---------------------------------------------------------
# Devanagari
# ---------------------------------------------------------

DEVANAGARI_INDEPENDENT_VOWELS = set(
    "अआइईउऊऋएऐओऔ"
)

DEVANAGARI_VOWEL_SIGNS = set(
    "ािीुूृेैोौॅॉॆॊ"
)


# ---------------------------------------------------------
# Gujarati
# ---------------------------------------------------------

GUJARATI_INDEPENDENT_VOWELS = set(
    "અઆઇઈઉઊઋએઐઓઔ"
)

GUJARATI_VOWEL_SIGNS = set(
    "ાિીુૂૃેૈોૌૅૉ"
)

GUJARATI_CONSONANTS = set(
    "કખગઘઙચછજઝઞ"
    "ટઠડઢણ"
    "તથદધન"
    "પફબભમ"
    "યરલવ"
    "શષસહળ"
)

GUJARATI_VIRAMA = "્"


def _estimate_syllables_from_transcription(transcription: str) -> int:
    """
    Estimate syllable count from a transcription.

    This is intentionally a lightweight multilingual heuristic.
    It is an operational speech-rate estimate, not a clinical measure.
    """

    if not transcription or not transcription.strip():
        return 0

    text = transcription.strip()
    syllables = 0

    # ---------------------------------------------------------
    # Latin-script estimation
    # ---------------------------------------------------------
    latin_vowels = set("aeiouy")
    in_vowel_group = False

    for char in text.lower():
        if char in latin_vowels:
            if not in_vowel_group:
                syllables += 1
                in_vowel_group = True
        else:
            in_vowel_group = False

    # ---------------------------------------------------------
    # Devanagari estimation
    # ---------------------------------------------------------
    for char in text:
        if char in DEVANAGARI_INDEPENDENT_VOWELS:
            syllables += 1
        elif char in DEVANAGARI_VOWEL_SIGNS:
            syllables += 1

    # ---------------------------------------------------------
    # Gujarati estimation
    # ---------------------------------------------------------
    #
    # Gujarati has inherent vowels in consonants.
    #
    # Example:
    #   બ = "ba"
    #
    # But:
    #   બા = "baa"
    #
    # And:
    #   બ્ = consonant without an inherent vowel
    #
    # Therefore:
    #   consonant + vowel sign -> count the vowel sign
    #   consonant + virama     -> no syllable from the consonant
    #   bare consonant         -> inherent vowel -> one syllable
    #
    i = 0

    while i < len(text):
        char = text[i]

        # Independent Gujarati vowel.
        if char in GUJARATI_INDEPENDENT_VOWELS:
            syllables += 1

        # Gujarati consonant.
        elif char in GUJARATI_CONSONANTS:
            next_char = text[i + 1] if i + 1 < len(text) else ""

            # Consonant + virama:
            # no inherent vowel.
            if next_char == GUJARATI_VIRAMA:
                i += 1

            # Consonant + dependent vowel sign:
            # the vowel sign itself will be counted below.
            elif next_char in GUJARATI_VOWEL_SIGNS:
                pass

            # Bare consonant:
            # Gujarati inherent "a" vowel.
            else:
                syllables += 1

        # Gujarati dependent vowel sign.
        elif char in GUJARATI_VOWEL_SIGNS:
            syllables += 1

        i += 1

    return syllables


def calculate_speech_rate(
    vad_result: VADResult,
    transcription: Optional[str],
) -> SpeechRateResult:
    """
    Estimate spoken syllables per second using VAD-derived speech duration.

    NULL is returned when speech duration or transcription is unavailable.
    """

    if not vad_result.usable:
        return SpeechRateResult(
            speech_rate=None,
            estimated_syllables=None,
            speech_duration_seconds=None,
            reason="VAD_UNUSABLE",
        )

    if not vad_result.speech_segments:
        return SpeechRateResult(
            speech_rate=None,
            estimated_syllables=None,
            speech_duration_seconds=None,
            reason="NO_SPEECH_DETECTED",
        )

    if not transcription or not transcription.strip():
        return SpeechRateResult(
            speech_rate=None,
            estimated_syllables=None,
            speech_duration_seconds=vad_result.speech_duration_seconds,
            reason="TRANSCRIPTION_UNAVAILABLE",
        )

    speech_duration = vad_result.speech_duration_seconds

    if speech_duration is None or speech_duration <= 0:
        return SpeechRateResult(
            speech_rate=None,
            estimated_syllables=None,
            speech_duration_seconds=None,
            reason="INVALID_SPEECH_DURATION",
        )

    estimated_syllables = _estimate_syllables_from_transcription(
        transcription
    )

    if estimated_syllables <= 0:
        return SpeechRateResult(
            speech_rate=None,
            estimated_syllables=0,
            speech_duration_seconds=speech_duration,
            reason="SYLLABLE_ESTIMATION_FAILED",
        )

    speech_rate = estimated_syllables / speech_duration

    return SpeechRateResult(
        speech_rate=speech_rate,
        estimated_syllables=estimated_syllables,
        speech_duration_seconds=speech_duration,
        reason=None,
    )