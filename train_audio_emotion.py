#!/usr/bin/env python3
"""Root CLI entrypoint for Audio Emotion Representation Model Training (Slice 3.4)."""
import sys
from backend.ml.training.train_audio_emotion import parse_args, train_audio_emotion

if __name__ == "__main__":
    cli_args = parse_args()
    train_audio_emotion(cli_args)
