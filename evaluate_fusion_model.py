"""Root entry point for evaluating Multimodal Feature Fusion Model (Slice 3.5)."""

import sys
from pathlib import Path

# Ensure workspace root is in path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.ml.training.evaluate_fusion_model import evaluate_fusion_model, parse_args

if __name__ == "__main__":
    args = parse_args()
    evaluate_fusion_model(
        model_dir=args.model_dir,
        data_dir=args.data_dir,
        output_file=args.output_file,
        seed=args.seed,
    )
