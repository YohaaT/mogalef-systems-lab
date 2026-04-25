"""POOL smoke benchmark for vec_optimized Phase 1 wrapper."""

from __future__ import annotations

import itertools
import time
from multiprocessing import Pool

from COMB_002_IMPULSE_V2_vec_optimized import Comb002ImpulseV2Params, Comb002ImpulseV2VecOptimized
from test_vec_optimized_equivalence import build_rows


_DATA = None


def init_worker(rows):
    global _DATA
    _DATA = rows


def run_combo(combo):
    sh, sb, dmh, dml = combo
    params = Comb002ImpulseV2Params(
        stpmt_smooth_h=sh,
        stpmt_smooth_b=sb,
        stpmt_distance_max_h=dmh,
        stpmt_distance_max_l=dml,
        horaire_allowed_hours_utc=list(range(24)),
    )
    result = Comb002ImpulseV2VecOptimized(params).run(_DATA)
    return len(result.trades), result.profit_factor


def main() -> int:
    rows = build_rows(1000)
    combos = list(itertools.product([2, 3, 4, 5], [2, 3, 4, 5], [75, 125, 175], [75, 125, 175]))[:100]
    t0 = time.perf_counter()
    with Pool(processes=2, initializer=init_worker, initargs=(rows,)) as pool:
        results = pool.map(run_combo, combos)
    elapsed = time.perf_counter() - t0
    print(f"elapsed_seconds={elapsed:.4f}")
    print(f"combos={len(results)}")
    print(f"best_pf={max((pf for _, pf in results), default=0.0):.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

