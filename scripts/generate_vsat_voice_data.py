#!/usr/bin/env python3
"""
Standalone utility to generate VSAT_VOICE sessions and corresponding billing_records for 2025.
Usage:
  python scripts/generate_vsat_voice_data.py
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from modules.core.database import generate_vsat_voice_sample_sessions


def main() -> int:
    inserted, err = generate_vsat_voice_sample_sessions()
    if err:
        print(f"Error: {err}")
        return 1
    print(f"Inserted VSAT_VOICE rows: {inserted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


