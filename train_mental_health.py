#!/usr/bin/env python3
"""Root CLI entrypoint for Mental Health Language Representation Model Training (Slice 3.3)."""
import sys
from backend.ml.training.train_mental_health import parse_args, train_mental_health

if __name__ == "__main__":
    cli_args = parse_args()
    train_mental_health(cli_args)
