#!/usr/bin/env python3
"""
DictCreator - Vocabulary Learning & Review
Main entry point for Linux, macOS, Windows, and iOS (iSH).
"""
import sys
from pathlib import Path

# Add project root to sys.path so 'src' can always be imported
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.__main__ import main

if __name__ == "__main__":
    main()
