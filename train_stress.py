#!/usr/bin/env python3
"""Root CLI entrypoint for Stress Model Training (Slice 3.3)."""
import sys
from backend.ml.training.train_stress import parse_args, train_stress

if __name__ == "__main__":
    cli_args = parse_args()
    train_stress(cli_args)
