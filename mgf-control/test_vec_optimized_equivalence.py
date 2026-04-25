"""Equivalence checks for vec_optimized strategy entrypoints.

The tests compare optimized entrypoints against their canonical implementations
on deterministic synthetic OHLC data.  They are intentionally small enough to
run before deployment.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

from COMB_001_TREND_V1 import Comb001TrendParams, Comb001TrendStrategy
from COMB_001_TREND_V1_vec_optimized import Comb001TrendVecOptimized
from COMB_002_IMPULSE_V2_adaptive import Comb002ImpulseV2Params, Comb002ImpulseV2Strategy
from COMB_002_IMPULSE_V2_vec_optimized import Comb002ImpulseV2VecOptimized


def build_rows(n: int = 120):
    rows = []
    ts0 = datetime(2024, 1, 2, 9, 0)
    price = 100.0
    for i in range(n):
        wave = math.sin(i / 7.0) * 1.5 + math.cos(i / 17.0) * 0.8
        close = price + wave * 0.2
        high = max(price, close) + 0.9 + (i % 5) * 0.05
        low = min(price, close) - 0.9 - (i % 3) * 0.05
        rows.append(
            {
                "timestamp_utc": (ts0 + timedelta(minutes=5 * i)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "open": f"{price:.6f}",
                "high": f"{high:.6f}",
                "low": f"{low:.6f}",
                "close": f"{close:.6f}",
            }
        )
        price = close + math.sin(i / 13.0) * 0.15
    return rows


def assert_close(name: str, left: float, right: float, tolerance: float = 1e-9) -> None:
    if abs(left - right) > tolerance:
        raise AssertionError(f"{name}: {left} != {right}")


def compare_results(label: str, canonical, optimized) -> None:
    if len(canonical.trades) != len(optimized.trades):
        raise AssertionError(f"{label}: trade count mismatch {len(canonical.trades)} != {len(optimized.trades)}")
    assert_close(f"{label} pf", canonical.profit_factor, optimized.profit_factor, 1e-6)
    assert_close(f"{label} equity", canonical.equity_points, optimized.equity_points, 1e-6)
    assert_close(f"{label} max_dd", canonical.max_drawdown, optimized.max_drawdown, 1e-6)


def main() -> int:
    rows = build_rows()

    p1 = Comb001TrendParams(
        horaire_allowed_hours_utc=list(range(24)),
        trend_enforce_date_kill_switch=False,
    )
    compare_results(
        "COMB_001",
        Comb001TrendStrategy(p1).run(rows),
        Comb001TrendVecOptimized(p1).run(rows),
    )

    p2 = Comb002ImpulseV2Params(
        horaire_allowed_hours_utc=list(range(24)),
        allowed_weekdays=list(range(7)),
    )
    compare_results(
        "COMB_002",
        Comb002ImpulseV2Strategy(p2).run(rows),
        Comb002ImpulseV2VecOptimized(p2).run(rows),
    )

    print("[OK] vec_optimized equivalence checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
