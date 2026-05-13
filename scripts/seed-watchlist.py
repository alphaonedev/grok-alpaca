#!/usr/bin/env python3
"""Seed the default watchlist file if missing."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

DEFAULT = {
    "name": "Default",
    "symbols": ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "AMD", "META", "GOOGL", "AMZN", "TSLA"],
}


def main() -> int:
    data_dir = Path(os.environ.get("DATA_DIR", "~/.grok-alpaca")).expanduser()
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / "watchlist.json"
    if path.exists():
        print(f"already exists: {path}")
        return 0
    path.write_text(json.dumps([DEFAULT], indent=2))
    print(f"wrote: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
