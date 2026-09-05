# Dataset Card: GoEmotions

## 1. Source
- **Origin**: Google Research GoEmotions dataset (Demszky et al., ACL 2020).
- **Repository Location**: `datasets/goemotions/` (`train.tsv`, `dev.tsv`, `test.tsv`, `emotions.txt`).
- **Language**: English (`en`).

## 2. Purpose
Provides fine-grained, multilabel emotional annotations on Reddit comments. Serves as auxiliary supervision for learning emotional nuance, empathy, and affective cues in textual communications.

> [!IMPORTANT]
> **Clinical Boundary Disclaimer**:
> GoEmotions labels represent conversational affect and social emotions. They are **NOT** psychiatric diagnoses, depression/anxiety scales, or clinical escalation indicators.

## 3. Labels
28 fine-grained emotion categories defined in `emotions.txt`:
- `admiration` (0), `amusement` (1), `anger` (2), `annoyance` (3), `approval` (4), `caring` (5), `confusion` (6), `curiosity` (7), `desire` (8), `disappointment` (9), `disapproval` (10), `disgust` (11), `embarrassment` (12), `excitement` (13), `fear` (14), `gratitude` (15), `grief` (16), `joy` (17), `love` (18), `nervousness` (19), `optimism` (20), `pride` (21), `realization` (22), `relief` (23), `remorse` (24), `sadness` (25), `surprise` (26), `neutral` (27).

## 4. Preprocessing Pipeline
- Implemented in `backend/ml/training/preprocessing/preprocess_goemotions.py`.
- **Headerless TSV Parsing**: Automatically parses 3-column TSVs (`text \t label_ids \t id`).
- **Taxonomy Loading**: Dynamically reads `emotions.txt` from the dataset directory.
- **Multilabel Normalization**: Converts comma-delimited strings (e.g. `"4,27"`) into integer ID arrays (`[4, 27]`) and mapped human-readable label arrays (`["approval", "neutral"]`).
- **Text Normalization**: Unicode NFKC cleanup, invisible character stripping, and whitespace normalization.

## 5. Fields Used
| Field | Destination | Description |
| --- | --- | --- |
| Column 0 | `text` | Cleaned comment text |
| Column 1 | `label_ids` & `emotion_labels` | Multilabel integer indices and mapped string categories |
| Column 2 | `id` | Unique comment identifier |

## 6. Fields Ignored
- None; all 3 columns of the official TSV release are utilized.

## 7. Limitations
- Sourced from Reddit communities; demographic skews towards young, male, English-speaking social media users.
- Some utterances reflect informal internet sarcasm, slang, or emojis that differ from formal mental-health monitoring dialogue.

## 8. Contribution to AAROH
Supplies rich auxiliary supervision for AAROH's text feature representation, helping distinguish nuanced emotions (e.g. grief vs sadness, nervousness vs fear) before evaluating clinical distress trajectories.
