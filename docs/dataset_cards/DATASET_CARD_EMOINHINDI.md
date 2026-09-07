# Dataset Card: EmoInHindi (Official Conversational Benchmark)

> [!NOTE]
> **Dataset Status & Disambiguation**:
> The official multi-turn conversational EmoInHindi dataset is planned for ingestion when the dataset files are placed in the repository.
> The single-turn Hindi-translated GoEmotions dataset formerly placed under `datasets/emoinhindi/` has been renamed to `datasets/goemotions_hindi_adaptation/` and is documented in [DATASET_CARD_GOEMOTIONS_HINDI_ADAPTATION.md](DATASET_CARD_GOEMOTIONS_HINDI_ADAPTATION.md).

## 1. Source & Expected Specification
- **Origin**: Official EmoInHindi conversational emotion benchmark (IIT Patna / ACL/EMNLP community).
- **Target Location**: `datasets/emoinhindi/` or `datasets/real_emoinhindi/`.
- **Language**: Conversational Hindi (`hi`), written in Devanagari script.
- **Expected Structure**:
  - **Dialogues**: ~1,814 multi-turn dialogues.
  - **Utterances**: ~44,247 conversational utterances.
  - **Emotion Classes**: 16 emotion categories.
  - **Dialogue IDs & Turn Ordering**: Explicit dialogue boundaries and sequential turn numbers.
  - **Emotion Intensity**: Explicit intensity annotations per utterance.

## 2. Purpose
When available, this dataset will provide multi-turn conversational emotion supervision in Hindi, capturing conversational context, turn transitions, and emotional intensity shifts in spoken and chat dialogues.

> [!IMPORTANT]
> **Clinical Boundary Disclaimer**:
> This dataset provides conversational emotion supervision only. Annotations represent colloquial emotional affect and are **NOT** psychiatric diagnostic labels, formal clinical assessments, or escalation triggers.

## 3. Expected Emotion Taxonomy (16 Classes)
1. `anger`
2. `anticipation`
3. `disgust`
4. `fear`
5. `joy`
6. `sadness`
7. `surprise`
8. `trust`
9. `neutral`
10. `love`
11. `pride`
12. `relief`
13. `remorse`
14. `shame`
15. `contempt`
16. `enthusiasm`

## 4. Preprocessing & Verification
- Placeholder module: `backend/ml/training/preprocessing/preprocess_real_emoinhindi.py` (raises `NotImplementedError` until dataset files are supplied).
- Verification script: `verify_real_emoinhindi.py` (validates presence, schema, dialogue count, utterance count, 16 classes, and intensity).

## 5. Distinction from GoEmotions Hindi Adaptation
| Attribute | Official EmoInHindi | GoEmotions Hindi Adaptation |
| --- | --- | --- |
| **Data Structure** | Multi-turn conversational dialogues | Single-turn social media comments |
| **Dialogue Count** | ~1,814 dialogues | None (independent comments) |
| **Utterance Count** | ~44,247 utterances | 54,263 comments |
| **Taxonomy** | 16 emotion classes | 28 GoEmotions emotion classes |
| **Context** | Conversational turn history & speaker turns | Isolated single utterances |
| **Intensity** | Emotion intensity scores | Binary multi-hot labels |
| **Current Status** | Awaiting dataset placement | Preprocessed in `datasets/goemotions_hindi_adaptation/` |
