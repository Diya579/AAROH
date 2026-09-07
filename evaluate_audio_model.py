#!/usr/bin/env python3
"""Root CLI entrypoint for Audio Emotion Model Evaluation Suite (Slice 3.4)."""
import sys
from backend.ml.training.evaluate_audio_model import evaluate_audio_emotion, parse_args

if __name__ == "__main__":
    cli_args = parse_args()
    evaluate_audio_emotion(
        data_dir=cli_args.data_dir,
        models_dir=cli_args.models_dir,
        seed=cli_args.seed,
        output_file=cli_args.output_file,
    )
