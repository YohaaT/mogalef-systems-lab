"""Single-combo timing smoke test for vec_optimized strategies."""

from __future__ import annotations

import time

from COMB_002_IMPULSE_V2_vec_optimized import Comb002ImpulseV2Params, Comb002ImpulseV2VecOptimized
from test_vec_optimized_equivalence import build_rows


def main() -> int:
    rows = build_rows(1000)
    params = Comb002ImpulseV2Params(horaire_allowed_hours_utc=list(range(24)))
    t0 = time.perf_counter()
    result = Comb002ImpulseV2VecOptimized(params).run(rows)
    elapsed = time.perf_counter() - t0
    print(f"elapsed_seconds={elapsed:.4f}")
    print(f"trades={len(result.trades)}")
    print(f"profit_factor={result.profit_factor:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

