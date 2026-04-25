"""Optimized vectorized entrypoint for COMB_002 Impulse V2.

COMB_002 already routes ATR through ``vec_mogalef_core`` when available and
keeps the stateful trade loop sequential.  This module provides the explicit
``*_vec_optimized`` import target required by the TANK plan without mutating
the validated adaptive implementation.
"""

from __future__ import annotations

import numpy as np

from COMB_002_IMPULSE_V2_adaptive import (
    Comb002ImpulseV2Params,
    Comb002ImpulseV2Result,
    Comb002ImpulseV2Strategy,
    Trade,
    load_ohlc_csv,
)


def vectorized_atr_sma(highs, lows, closes, period: int = 14):
    """Return the same ATR SMA series used by the optimized COMB_002 strategy."""
    try:
        from vec_mogalef_core import atr_sma

        return atr_sma(
            np.asarray(highs, dtype=float),
            np.asarray(lows, dtype=float),
            np.asarray(closes, dtype=float),
            period,
        )
    except ImportError:
        return np.asarray(
            Comb002ImpulseV2Strategy._atr_sma(
                list(map(float, highs)),
                list(map(float, lows)),
                list(map(float, closes)),
                period,
            ),
            dtype=float,
        )


class Comb002ImpulseV2VecOptimized(Comb002ImpulseV2Strategy):
    """Named optimized strategy class used by the VEC+POOL phase scripts."""


# Drop-in alias expected by wrapper-injected phase scripts.
Comb002ImpulseV2Strategy = Comb002ImpulseV2VecOptimized

