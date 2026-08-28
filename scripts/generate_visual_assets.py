#!/usr/bin/env python3
"""Regenerate deterministic local visual assets used by the profile."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_qr.py")], check=True)
print("Local profile assets are ready.")
