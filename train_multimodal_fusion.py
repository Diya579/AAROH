"""Root entry point for training Multimodal Feature Fusion Model (Slice 3.5)."""

import sys
from pathlib import Path

# Ensure workspace root is in path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.ml.training.train_multimodal_fusion import parse_args, train_fusion_model

if __name__ == "__main__":
    args = parse_args()
    train_fusion_model(args)
