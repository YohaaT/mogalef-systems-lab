"""Optimized vectorized entrypoint for COMB_001 Trend V1.

This module is intentionally a compatibility layer over the existing
``COMB_001_TREND_V1_vectorized`` implementation.  The plan requires a stable
``*_vec_optimized`` import target for TANK VEC+POOL scripts while keeping the
original strategy file untouched.
"""

from __future__ import annotations

from COMB_001_TREND_V1_vectorized import (
    Comb001TrendParams,
    Comb001TrendResult,
    Comb001TrendVectorized,
    Trade,
    _calc_atr_numpy as vectorized_atr,
    export_results_csv,
    load_ohlc_csv,
    run_optimization_pool,
)


class Comb001TrendVecOptimized(Comb001TrendVectorized):
    """Named optimized strategy class used by the VEC+POOL phase scripts."""

    def __init__(self, params: Comb001TrendParams | None = None) -> None:
        if params is not None and not hasattr(params, "contexto_blocked_weekdays"):
            setattr(params, "contexto_blocked_weekdays", [])
        super().__init__(params)


# Drop-in aliases expected by the existing phase scripts.
Comb001TrendStrategy = Comb001TrendVecOptimized
