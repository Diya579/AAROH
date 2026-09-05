#!/usr/bin/env python3
"""Root-level wrapper for evaluating the Longitudinal Trajectory Model (Slice 3.7)."""

import sys
from pathlib import Path

# Ensure repository root is on sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.ml.training.evaluate_trajectory_model import main

if __name__ == "__main__":
    main()
