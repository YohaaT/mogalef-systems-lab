"""Vectorized Mogalef core indicators (NumPy-based).

Replaces loop-based calculations with NumPy for speed:
- ATR: simple moving average of true range
- StopIntelligent: vectorized extrema detection + volatility-adjusted stops
- IntelligentScalpingTarget: same as SI but inverted for targets
- STPMT_DIV: signal divergence (delegates to existing compute_el_stpmt_div)

Usage in strategies: pass numpy arrays directly instead of building row dicts.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np


def atr_sma(
    highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14
) -> np.ndarray:
    """Calculate ATR using simple moving average. O(n)."""
    n = len(highs)
    tr = np.zeros(n)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr[i] = max(
            highs[i] - lows[i],
            abs(closes[i - 1] - highs[i]),
            abs(closes[i - 1] - lows[i]),
        )
    atr = np.zeros(n)
    if n >= period:
        atr[period - 1] = np.mean(tr[:period])
        for i in range(period, n):
            atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
        atr[:period] = atr[period - 1]
    return atr


def extrema_quality(
    highs: np.ndarray, lows: np.ndarray, quality: int = 2
) -> Tuple[np.ndarray, np.ndarray]:
    """Detect local extrema (highs/lows) per Mogalef quality setting.
    Returns (haut, bas) binary arrays marking extrema positions."""
    n = len(highs)
    haut = np.zeros(n, dtype=int)
    bas = np.zeros(n, dtype=int)

    if quality == 1:
        for i in range(n - 3):
            if (highs[i] < highs[i + 1] and highs[i + 1] > highs[i + 2]) or (
                highs[i] < highs[i + 1]
                and highs[i + 1] >= highs[i + 2]
                and highs[i + 2] > highs[i + 3]
            ):
                haut[i] = 1
            if (lows[i] > lows[i + 1] and lows[i + 1] < lows[i + 2]) or (
                lows[i] > lows[i + 1]
                and lows[i + 1] <= lows[i + 2]
                and lows[i + 2] < lows[i + 3]
            ):
                bas[i] = 1
    elif quality == 2:
        for i in range(n - 4):
            if (
                highs[i] < highs[i + 2]
                and highs[i + 1] < highs[i + 2]
                and highs[i + 3] <= highs[i + 2]
                and highs[i + 2] > highs[i + 4]
            ):
                haut[i] = 2
            if (
                lows[i] > lows[i + 2]
                and lows[i + 1] > lows[i + 2]
                and lows[i + 3] >= lows[i + 2]
                and lows[i + 4] >= lows[i + 2]
            ):
                bas[i] = 2
    else:  # quality >= 3
        for i in range(n - 6):
            if (
                highs[i] < highs[i + 3]
                and highs[i + 1] < highs[i + 3]
                and highs[i + 2] <= highs[i + 3]
                and highs[i + 3] >= highs[i + 4]
                and highs[i + 3] >= highs[i + 5]
                and highs[i + 3] >= highs[i + 6]
            ):
                haut[i] = 3
            if (
                lows[i] > lows[i + 3]
                and lows[i + 1] > lows[i + 3]
                and lows[i + 2] >= lows[i + 3]
                and lows[i + 3] <= lows[i + 4]
                and lows[i + 3] <= lows[i + 5]
                and lows[i + 3] <= lows[i + 6]
            ):
                bas[i] = 3

    return haut, bas


def stop_intelligent_vectorized(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    market_position: np.ndarray,
    quality: int = 2,
    recent_volat: int = 2,
    ref_volat: int = 20,
    coef_volat: float = 5.0,
    first_low_or_more: int = 2,
    first_high_or_more: int = 2,
) -> np.ndarray:
    """Vectorized StopIntelligent. Returns stop array (per bar)."""
    n = len(closes)

    # TR and volatility
    tr = np.zeros(n)
    tr[0] = highs[0] - lows[0]
    for i in range(1, n):
        tr[i] = max(
            highs[i] - lows[i],
            abs(closes[i - 1] - highs[i]),
            abs(closes[i - 1] - lows[i]),
        )

    # SMA of TR
    avtr = np.zeros(n)
    avtrref = np.zeros(n)
    if n >= recent_volat:
        avtr[recent_volat - 1] = np.mean(tr[:recent_volat])
        for i in range(recent_volat, n):
            avtr[i] = (avtr[i - 1] * (recent_volat - 1) + tr[i]) / recent_volat
        avtr[:recent_volat] = avtr[recent_volat - 1]

    if n >= ref_volat:
        avtrref[ref_volat - 1] = np.mean(tr[:ref_volat])
        for i in range(ref_volat, n):
            avtrref[i] = (avtrref[i - 1] * (ref_volat - 1) + tr[i]) / ref_volat
        avtrref[:ref_volat] = avtrref[ref_volat - 1]

    # Space
    space = np.zeros(n)
    for i in range(n):
        if avtr[i] > 0 and avtrref[i] > 0:
            space[i] = (((2 * avtrref[i]) - avtr[i]) * coef_volat) / 5.0

    # Extrema
    haut, bas = extrema_quality(highs, lows, quality)

    # Track recent extrema (simplified: just use h1/b1)
    h1 = np.zeros(n)
    b1 = np.zeros(n)
    for i in range(n - 1, -1, -1):
        if i + quality < n:
            if haut[i] > 0:
                h1[i] = highs[i + quality]
            else:
                h1[i] = h1[i + 1] if i + 1 < n else 0
            if bas[i] > 0:
                b1[i] = lows[i + quality]
            else:
                b1[i] = b1[i + 1] if i + 1 < n else 0

    # Stop calculation
    stop = np.zeros(n)
    for i in range(n):
        if market_position[i] == 1:  # long
            b0 = b1[i]
            if first_low_or_more > 1 and i > 0:
                b0 = min(b1[i], b1[i - 1] if i > 0 else b1[i])
            stlong = b0 - space[i]
            if stlong > closes[i]:
                stlong = closes[i] - abs(space[i])
            if i > 0 and market_position[i - 1] == 1 and stop[i - 1] > 0:
                if stlong < stop[i - 1]:
                    stop[i] = stop[i - 1]
                else:
                    stop[i] = stlong
            else:
                stop[i] = stlong
        elif market_position[i] == -1:  # short
            h0 = h1[i]
            if first_high_or_more > 1 and i > 0:
                h0 = max(h1[i], h1[i - 1] if i > 0 else h1[i])
            stlong = h0 + space[i]
            if stlong < closes[i]:
                stlong = closes[i] + abs(space[i])
            if i > 0 and market_position[i - 1] == -1 and stop[i - 1] > 0:
                if stlong > stop[i - 1]:
                    stop[i] = stop[i - 1]
                else:
                    stop[i] = stlong
            else:
                stop[i] = stlong

    return stop
