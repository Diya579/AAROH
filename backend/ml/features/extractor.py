"""Text feature extraction orchestrator (Slice 2.2).

Consumes PreprocessedInteraction from Slice 2.1 to generate structured, immutable
TextFeatures. Preserves the `None != 0` invariant for absent text and collects
matched terms for explainability.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from backend.ml.features.distress import extract_distress_indicators
from backend.ml.features.help_seeking import extract_help_seeking_indicators
from backend.ml.features.lexical import extract_lexical_metrics
from backend.ml.features.safety import extract_safety_indicators
from backend.ml.features.types import (
    ExplanationEvidence,
    TextFeatures,
    TextQualityMetadata,
)
from backend.ml.preprocessing import (
    PreprocessedInteraction,
    preprocess_interaction,
)


class TextFeatureExtractor:
    """Extracts structured text features from a preprocessed interaction.

    Guarantees:
    - Pure, deterministic feature extraction.
    - Preserves `None != 0`: absent or empty text produces `text_available=False`
      with all indicator blocks set to None.
    - Never accepts un-preprocessed raw text directly into `extract()`.
    - Captures matched terms in `evidence` for explainability without affecting scores.
    """

    def extract(self, interaction: PreprocessedInteraction) -> TextFeatures:
        """Extracts text features from a PreprocessedInteraction record."""
        if not isinstance(interaction, PreprocessedInteraction):
            raise TypeError(
                "extract() requires a PreprocessedInteraction instance. "
                "Raw text or unvalidated mappings must be routed through "
                "preprocess_interaction() or use extract_from_raw()."
            )

        # Check if text is present and usable
        text_obj = interaction.text
        if (
            text_obj is None
            or text_obj.quality.is_empty
            or interaction.missingness.is_text_missing
            or not text_obj.clean.strip()
        ):
            # Safe missing value handling: Never fabricate 0.0 scores for absent text
            quality_meta = (
                TextQualityMetadata(
                    language=interaction.language,
                    detected_scripts=(),
                    has_multilingual_chars=False,
                    is_empty=True,
                    is_very_short=True,
                )
                if text_obj is None
                else TextQualityMetadata(
                    language=interaction.language,
                    detected_scripts=text_obj.quality.detected_scripts,
                    has_multilingual_chars=text_obj.quality.has_multilingual_chars,
                    is_empty=True,
                    is_very_short=True,
                )
            )

            return TextFeatures(
                text_available=False,
                lexical=None,
                distress=None,
                help_seeking=None,
                safety=None,
                quality=quality_meta,
                evidence=None,
            )

        clean_text = text_obj.clean
        raw_text = text_obj.raw

        # 1. Lexical metrics
        lexical = extract_lexical_metrics(clean_text, raw_text=raw_text)

        # 2. Distress indicators
        distress, distress_ev = extract_distress_indicators(clean_text)

        # 3. Help-seeking indicators
        help_seeking, hs_ev = extract_help_seeking_indicators(clean_text)

        # 4. Safety indicators
        safety, safety_ev = extract_safety_indicators(clean_text)

        # 5. Centralized explainability evidence
        combined_evidence: dict[str, tuple[str, ...]] = {}
        combined_evidence.update(distress_ev)
        combined_evidence.update(hs_ev)
        combined_evidence.update(safety_ev)

        all_terms_set: set[str] = set()
        for terms in combined_evidence.values():
            all_terms_set.update(terms)

        evidence = ExplanationEvidence(
            matched_terms_by_category=combined_evidence,
            all_matched_terms=tuple(sorted(all_terms_set)),
        )

        # 6. Reused quality metadata (from Slice 2.1)
        quality = TextQualityMetadata(
            language=interaction.language,
            detected_scripts=text_obj.quality.detected_scripts,
            has_multilingual_chars=text_obj.quality.has_multilingual_chars,
            is_empty=text_obj.quality.is_empty,
            is_very_short=text_obj.quality.is_very_short,
        )

        return TextFeatures(
            text_available=True,
            lexical=lexical,
            distress=distress,
            help_seeking=help_seeking,
            safety=safety,
            quality=quality,
            evidence=evidence,
        )

    def extract_from_raw(self, raw_input: Mapping[str, Any]) -> TextFeatures:
        """Convenience helper that pre-processes raw interaction input first."""
        preprocessed = preprocess_interaction(raw_input)
        return self.extract(preprocessed)

    def extract_batch(
        self, interactions: Iterable[PreprocessedInteraction]
    ) -> list[TextFeatures]:
        """Extracts text features for an iterable of PreprocessedInteraction records."""
        return [self.extract(item) for item in interactions]


_DEFAULT_EXTRACTOR = TextFeatureExtractor()


def extract_text_features(
    interaction: PreprocessedInteraction,
    extractor: Optional[TextFeatureExtractor] = None,
) -> TextFeatures:
    """Convenience function to extract text features from a PreprocessedInteraction."""
    e = extractor or _DEFAULT_EXTRACTOR
    return e.extract(interaction)


def extract_text_features_batch(
    interactions: Iterable[PreprocessedInteraction],
    extractor: Optional[TextFeatureExtractor] = None,
) -> list[TextFeatures]:
    """Convenience function to extract text features for multiple interactions."""
    e = extractor or _DEFAULT_EXTRACTOR
    return e.extract_batch(interactions)
