#!/usr/bin/env python3
"""Root CLI entrypoint for Text Emotion Model Training (Slice 3.3)."""
import sys
from backend.ml.training.train_text_emotion import parse_args, train_text_emotion

if __name__ == "__main__":
    cli_args = parse_args()
    train_text_emotion(cli_args)
