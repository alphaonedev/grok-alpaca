"""Lookback string parsing helpers."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

_PATTERN = re.compile(r"^\s*(\d+)\s*(min|h|d|w|mo|y)\s*$", re.IGNORECASE)
_UNITS = {
    "min": ("minutes", 1),
    "h": ("hours", 1),
    "d": ("days", 1),
    "w": ("days", 7),
    "mo": ("days", 30),
    "y": ("days", 365),
}


def parse_lookback(s: str) -> timedelta:
    """Parse strings like '30d', '6mo', '1y', '5y', '90d', '12h', '15min' into a timedelta."""
    m = _PATTERN.match(s)
    if not m:
        raise ValueError(f"unrecognized lookback {s!r}; use '30d', '6mo', '1y', etc.")
    n = int(m.group(1))
    unit = m.group(2).lower()
    kind, mult = _UNITS[unit]
    return timedelta(**{kind: n * mult})


def resolve_window(
    lookback: str | None,
    start: datetime | None,
    end: datetime | None,
) -> tuple[datetime, datetime]:
    """Resolve a (start, end) UTC window from either lookback or explicit dates."""
    now = datetime.now(timezone.utc)
    if start and end:
        return start, end
    if lookback:
        delta = parse_lookback(lookback)
        return now - delta, now
    return now - timedelta(days=30), now
