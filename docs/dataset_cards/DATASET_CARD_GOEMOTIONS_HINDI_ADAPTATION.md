# Dataset Card: GoEmotions Hindi Adaptation

## 1. Source
- **Origin**: Hindi adaptation/translation of Google Research GoEmotions dataset (`emoHi-train.csv`, `emoHi-valid.csv`, `emoHi-test.csv`).
- **Repository Location**: `datasets/goemotions_hindi_adaptation/`.
- **Language**: Hindi (`hi`), written in Devanagari script.
- **Samples**: 54,263 total samples (43,410 train, 5,426 valid, 5,427 test).
- **Structure**: Single-turn social media comment translations with multi-label emotion annotations.

## 2. Purpose
Provides auxiliary supervisory signals for understanding nuanced emotional expression in translated Hindi text. Supports downstream multilingual text representation and Hindi distress/emotional indicator calibration in AAROH.

> [!IMPORTANT]
> **Clinical Boundary Disclaimer**:
> This dataset provides auxiliary emotion supervision only. Annotations represent general emotional affect (e.g., sadness, fear, anger, joy) and are **NOT** clinical distress diagnoses, psychiatric assessments, or escalation predictions.

## 3. Labels
Uses the 28-class GoEmotions taxonomy mapped into Hindi:
- **Positive**: `admiration`, `amusement`, `approval`, `caring`, `desire`, `excitement`, `gratitude`, `joy`, `love`, `optimism`, `pride`, `relief`
- **Negative / Distress-Relevant**: `anger`, `annoyance`, `disappointment`, `disapproval`, `disgust`, `embarrassment`, `fear`, `grief`, `nervousness`, `remorse`, `sadness`
- **Cognitive / Neutral**: `confusion`, `curiosity`, `realization`, `surprise`, `neutral`

## 4. Preprocessing Pipeline
- Implemented in `backend/ml/training/preprocessing/preprocess_goemotions_hindi_adaptation.py`.
- **Unicode Normalization**: Canonical NFKC normalization preserving Indic scripts, conjuncts, and zero-width joiners (ZWJ/ZWNJ).
- **Whitespace & Noise Removal**: Cleans invisible formatting artifacts (BOM, zero-width spaces, bidi overrides).
- **Multilabel Parsing**: Parses numpy bracketed strings (`[ 8 20]`, `[27]`) into clean integer lists and maps them to standard emotion taxonomy names.
- **Output Identifier**: Emits records with `"dataset": "goemotions_hindi_adaptation"`.
- **Missing Value Handling**: Preserves dialogue metadata as `null` and previous turns as `[]` without fabricating conversational history.

## 5. Fields Used
| Field | Destination | Description |
| --- | --- | --- |
| `id` | `utterance_id` | Unique utterance identifier |
| `text` | `text` | Cleaned and normalized Hindi text |
| `labels` | `emotion` & `emotion_labels` | Primary emotion and complete multilabel list |
| N/A | `dialogue_id` | Preserved as `null` (single-turn dataset) |
| N/A | `previous_turns` | Preserved as `[]` (single-turn dataset) |

## 6. Fields Ignored
- Unnamed pandas index column `''` (stripped).

## 7. Limitations & Distinctions
- **Not Multi-Turn**: Utterances are independent single-turn translated comments; does not contain conversational context or turn ordering.
- **Taxonomy**: Uses the 28-class GoEmotions taxonomy rather than the 16-class conversational emotion taxonomy of the official EmoInHindi benchmark.
- **Translation Artifacts**: Contains social media comments translated into Hindi; may exhibit translation artifacts or colloquial variations not fully representative of rural/regional dialects.
- **Non-Clinical**: Does not contain clinical intake interviews or psychiatric crisis calls.

## 8. Contribution to AAROH
Enhances AAROH's multilingual NLP pipeline to detect emotional cues, fear, helplessness, and sadness in Hindi text without depending exclusively on English training corpora.
