# Dataset Card: RAVDESS

## 1. Source
- **Origin**: Ryerson Audio-Visual Database of Emotional Speech and Song (Livingstone & Russo, PLOS ONE 2018).
- **Repository Location**: `datasets/ravdess/Actor_{01..24}/`.
- **Modality**: Audio (`.wav`, 16-bit, 48kHz).
- **Language**: English (`en`).

## 2. Purpose
Provides controlled, professional vocal emotional recordings across 24 professional actors (12 male, 12 female). Serves as auxiliary supervision for acoustic emotional affect recognition.

> [!IMPORTANT]
> **Clinical Boundary Disclaimer**:
> RAVDESS consists of acted emotional statements recorded in studio settings. It is **NOT** clinical speech from patients experiencing real-world mental health crises or trauma. Acoustic features derived from RAVDESS must never be treated as clinical diagnostic tools.

## 3. Labels
- **Emotions (8 classes)**: `neutral` (01), `calm` (02), `happy` (03), `sad` (04), `angry` (05), `fearful` (06), `disgust` (07), `surprised` (08).
- **Emotional Intensity**: `normal` (01), `strong` (02) (*Note: neutral is normal only*).
- **Statements**:
  - `01`: "Kids are talking by the door"
  - `02`: "Dogs are sitting by the door"
- **Repetitions**: `1st repetition` (01), `2nd repetition` (02).
- **Actors**: 24 professional actors (`Actor_01` to `Actor_24`). Odd numbers are male, even numbers are female.

## 4. Preprocessing Pipeline
- Implemented in `backend/ml/training/preprocessing/preprocess_ravdess.py`.
- **Dynamic Actor Folder Discovery**: Automatically traverses `datasets/ravdess/` to locate all actor directories.
- **Filename Specification Parser**: Decodes official 7-part hyphen-delimited codes (`03-01-01-01-01-01-01.wav`).
- **Acoustic Boundaries**: Purely maps metadata; **no MFCCs, spectrograms, or audio feature extractions are computed** at this stage.
- **Deterministic Export**: Output saved to `datasets/processed/ravdess.jsonl` sorted deterministically by actor ID and audio path.

## 5. Fields Used
| Field | Destination | Description |
| --- | --- | --- |
| File path | `audio_path` | Normalized relative path to audio file |
| Code 7 | `actor` | Actor identifier (`01` to `24`) |
| Code 3 | `emotion` | Mapped emotion category |
| Code 4 | `intensity` | Emotional intensity level (`normal`, `strong`) |
| Code 5 | `statement` | Utterance statement text |
| Code 6 | `repetition` | Repetition sequence number |
| Code 2 | `modality` | Audio channel (`speech`) |

## 6. Fields Ignored
- Video channel streams (only audio recordings are parsed).

## 7. Limitations
- Studio-recorded acted speech with scripted sentences; lacks the natural acoustic variability, background noise, and hesitation of real-world helpline or IVRS calls.

## 8. Contribution to AAROH
Provides standardized, balanced acoustic benchmarks for calibrating vocal feature bounds (pitch variability, pause ratios, speech rate) before connecting to AAROH's Voice→ML handoff contract.
