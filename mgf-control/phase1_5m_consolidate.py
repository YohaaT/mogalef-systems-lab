"""Phase 1 (5m) Consolidation — Merge Block 1 (TANK) + Block 2 (VPS), select best signal."""

import json
from pathlib import Path


def consolidate():
    print("=" * 70)
    print("PHASE 1 (5m) SIGNAL CONSOLIDATION")
    print("=" * 70)

    # Load Block 1 (TANK)
    try:
        with open("phase1_5m_signal_block_1_best_params.json") as f:
            b1 = json.load(f)
        print(f"\n[BLOCK 1 / TANK]  smooth_h={b1['smooth_h']}, smooth_b={b1['smooth_b']}, "
              f"dist_h={b1['dist_h']}, dist_l={b1['dist_l']}")
        print(f"  A_PF={b1['phase_a_pf']:.4f}  B_PF={b1['phase_b_pf']:.4f}  Robustness={b1['robustness']:.4f}")
    except FileNotFoundError:
        b1 = None
        print("\n[BLOCK 1 / TANK]  Not found")

    # Load Block 2 (VPS)
    try:
        with open("bo_phase1_5m_signal_block_2_best_params.json") as f:
            b2 = json.load(f)
        print(f"\n[BLOCK 2 / VPS]   smooth_h={b2['smooth_h']}, smooth_b={b2['smooth_b']}, "
              f"dist_h={b2['dist_h']}, dist_l={b2['dist_l']}")
        print(f"  A_PF={b2['phase_a_pf']:.4f}  B_PF={b2['phase_b_pf']:.4f}  Robustness={b2['robustness']:.4f}")
    except FileNotFoundError:
        b2 = None
        print("\n[BLOCK 2 / VPS]   Not found")

    if not b1 and not b2:
        raise FileNotFoundError("No Phase 1 (5m) results found from either block!")

    if b1 and b2:
        best = b1 if b1["robustness"] >= b2["robustness"] else b2
        source = "BLOCK 1 (TANK)" if best is b1 else "BLOCK 2 (VPS)"
    else:
        best = b1 or b2
        source = "BLOCK 1 (TANK)" if b1 else "BLOCK 2 (VPS)"

    print(f"\n[BEST] Selected from {source}:")
    print(f"  smooth_h={best['smooth_h']}, smooth_b={best['smooth_b']}, "
          f"dist_h={best['dist_h']}, dist_l={best['dist_l']}")
    print(f"  Robustness={best['robustness']:.4f}  A_PF={best['phase_a_pf']:.4f}  B_PF={best['phase_b_pf']:.4f}")

    consolidated = {
        "phase": 1,
        "timeframe": "5m",
        "signal_best": {
            "stpmt_smooth_h":        best["smooth_h"],
            "stpmt_smooth_b":        best["smooth_b"],
            "stpmt_distance_max_h":  best["dist_h"],
            "stpmt_distance_max_l":  best["dist_l"],
            "phase1_robustness":     best["robustness"],
        },
        "phase_a_pf": best["phase_a_pf"],
        "phase_b_pf": best["phase_b_pf"],
    }

    with open("phase1_5m_best_params.json", "w") as f:
        json.dump(consolidated, f, indent=2)
    print("\n[OK] phase1_5m_best_params.json written")

    print("\n" + "=" * 70)
    print("PHASE 1 (5m) CONSOLIDATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    consolidate()
