# Dataset Card: Dreaddit

## 1. Source
- **Origin**: Dreaddit Reddit Dataset for Stress Analysis in Social Media (Turcan & McKeown, EMNLP 2019).
- **Repository Location**: `datasets/dreaddit/` (`dreaddit.csv`).
- **Language**: English (`en`).

## 2. Purpose
Provides binary psychological stress annotations across domain-specific online support communities (e.g. PTSD, anxiety, financial stress, abusive relationships). Serves as auxiliary supervision for learning stress-related linguistic markers.

> [!IMPORTANT]
> **Clinical Boundary Disclaimer**:
> Dreaddit annotations capture layman crowd-sourced perceptions of acute stress in social media posts. They are **NOT** validated DSM-5 clinical diagnoses, clinician-rated psychiatric scores, or suicide/escalation flags.

## 3. Labels
Binary stress classification:
- `0`: Unstressed / Neutral
- `1`: Stressed

## 4. Preprocessing Pipeline
- Implemented in `backend/ml/training/preprocessing/preprocess_dreaddit.py`.
- **Dynamic File & Column Detection**: Automatically detects CSV files and maps column headers (`text`, `label`, `subreddit`).
- **Privacy Filtering**: Strictly filters out author identities, user handles, post timestamps, and karma scores.
- **Unicode Normalization**: Cleans curly quotes, irregular dashes, invisible formatting, and collapses whitespace.
- **Deterministic Export**: Generates `datasets/processed/dreaddit.jsonl` sorted deterministically by source subreddit and text.

## 5. Fields Used
| Field | Destination | Description |
| --- | --- | --- |
| `text` | `text` | Text segment from the Reddit post |
| `label` | `stress_label` | Binary stress indicator (`0` or `1`) |
| `subreddit` | `source_subreddit` | Community domain (`ptsd`, `anxiety`, `relationships`, etc.) |

## 6. Fields Ignored (Privacy & Non-ML Fields)
- `post_id`, `id`: Social media identifiers.
- `social_timestamp`, `social_karma`, `social_upvote_ratio`, `social_num_comments`: Platform engagement metrics.
- 100+ pre-calculated lexical LIWC and DAL features (LIWC, syntax_ari, etc.) are ignored; AAROH extracts features natively using its deterministic feature pipeline.

## 7. Limitations
- Crowd-annotated text from self-selected Reddit support forums.
- Long-tail self-disclosure texts that may contain graphic descriptions or unstructured narratives.

## 8. Contribution to AAROH
Assists AAROH's linguistic models in learning acute vs chronic stress phrasing, interpersonal conflict language, and trauma-related distress markers in informal English text.
