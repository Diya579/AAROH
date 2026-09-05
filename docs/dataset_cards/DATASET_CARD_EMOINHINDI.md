# Dataset Card: EmoInHindi

## 1. Source
- **Origin**: EmoInHindi benchmark dataset / translated & annotated Hindi GoEmotions corpus.
- **Repository Location**: `datasets/emoinhindi/` (`emoHi-train.csv`, `emoHi-valid.csv`, `emoHi-test.csv`).
- **Language**: Hindi (`hi`), written in Devanagari script.

## 2. Purpose
Provides auxiliary supervisory signals for understanding nuanced emotional expression in conversational Hindi. Supports downstream multilingual text representation and Hindi distress/emotional indicator calibration in AAROH.

> [!IMPORTANT]
> **Clinical Boundary Disclaimer**:
> This dataset provides auxiliary emotion supervision only. Annotations represent general emotional affect (e.g., sadness, fear, anger, joy) and are **NOT** clinical distress diagnoses, psychiatric assessments, or escalation predictions.

## 3. Labels
Uses the 28-class GoEmotions taxonomy mapped into Hindi:
- Positive: `admiration`, `amusement`, `approval`, `caring`, `desire`, `excitement`, `gratitude`, `joy`, `love`, `optimism`, `pride`, `relief`
- Negative / Distress-Relevant: `anger`, `annoyance`, `disappointment`, `disapproval`, `disgust`, `embarrassment`, `fear`, `grief`, `nervousness`, `remorse`, `sadness`
- Cognitive / Neutral: `confusion`, `curiosity`, `realization`, `surprise`, `neutral`

## 4. Preprocessing Pipeline
- Implemented in `backend/ml/training/preprocessing/preprocess_emoinhindi.py`.
- **Unicode Normalization**: Canonical NFKC normalization preserving Indic scripts, conjuncts, and zero-width joiners (ZWJ/ZWNJ).
- **Whitespace & Noise Removal**: Cleans invisible formatting artifacts (BOM, zero-width spaces, bidi overrides).
- **Multilabel Parsing**: Parses numpy bracketed strings (`[ 8 20]`, `[27]`) into clean integer lists and maps them to standard emotion taxonomy names.
- **Missing Value Handling**: Preserves dialogue metadata when present; if dialogue boundaries or previous turns are missing in the source, preserves `None` without fabricating data.

## 5. Fields Used
| Field | Destination | Description |
| --- | --- | --- |
| `id` | `utterance_id` | Unique utterance identifier |
| `text` | `text` | Cleaned and normalized Hindi text |
| `labels` | `emotion` & `emotion_labels` | Primary emotion and complete multilabel list |
| N/A | `dialogue_id` | Preserved as `null` if not in source |
| N/A | `previous_turns` | Preserved as `[]` if not in source |

## 6. Fields Ignored
- Unnamed pandas index column `''` (stripped).

## 7. Limitations
- Contains social media and conversational utterances translated into Hindi; may have translation artifacts or colloquial variations not representative of rural dialects.
- Does not contain clinical intake interviews or psychiatric crisis calls.

## 8. Contribution to AAROH
Enhances AAROH's multilingual NLP pipeline to detect emotional cues, fear, helplessness, and sadness in Hindi interactions without depending exclusively on English training corpora.
