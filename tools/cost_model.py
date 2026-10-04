#!/usr/bin/env python3
"""Repository entry point; canonical calculator ships inside the skill."""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parents[1] / "skills/cloudflare-cost-review/scripts/cost_model.py"), run_name="__main__")
