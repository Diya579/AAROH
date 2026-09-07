#!/usr/bin/env python3
"""Root CLI entrypoint for Text Representation Models Evaluation Suite (Slice 3.3)."""
import sys
from backend.ml.training.evaluate_text_models import evaluate_all, parse_args

if __name__ == "__main__":
    cli_args = parse_args()
    evaluate_all(
        data_dir=cli_args.data_dir,
        models_dir=cli_args.models_dir,
        model_type=cli_args.model_type,
        output_file=cli_args.output_file,
    )
