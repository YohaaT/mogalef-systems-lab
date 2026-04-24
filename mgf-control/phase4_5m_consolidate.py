"""Phase 4 (5m) Consolidation — Merge Block 1 + Block 2 results, select best Stop Intelligent params."""

import json
from pathlib import Path


def consolidate():
    print("=" * 70)
    print("PHASE 4 (5m) STOPS CONSOLIDATION")
    print("=" * 70)

    # Try to load Block 1 (TANK)
    try:
        with open("phase4_5m_stops_block_1_best_params.json") as f:
            b1 = json.load(f)
        print(f"\n[BLOCK 1 / TANK]  quality={b1['quality']}, recent={b1['recent']}, "
              f"ref_vol={b1['ref_vol']}, coef={b1['coef']:.1f}")
        print(f"  A_PF={b1['phase_a_pf']:.4f}  B_PF={b1['phase_b_pf']:.4f}  Robustness={b1['robustness']:.4f}")
    except FileNotFoundError:
        b1 = None
        print("\n[BLOCK 1 / TANK]  Not found")

    # Try to load Block 2 (VPS)
    try:
        with open("phase4_5m_stops_block_2_best_params.json") as f:
            b2 = json.load(f)
        print(f"\n[BLOCK 2 / VPS]   quality={b2['quality']}, recent={b2['recent']}, "
              f"ref_vol={b2['ref_vol']}, coef={b2['coef']:.1f}")
        print(f"  A_PF={b2['phase_a_pf']:.4f}  B_PF={b2['phase_b_pf']:.4f}  Robustness={b2['robustness']:.4f}")
    except FileNotFoundError:
        b2 = None
        print("\n[BLOCK 2 / VPS]   Not found")

    # Try single block (if run as single)
    try:
        with open("phase4_5m_stops_best_params.json") as f:
            single = json.load(f)
        print(f"\n[SINGLE RUN]      quality={single['quality']}, recent={single['recent']}, "
              f"ref_vol={single['ref_vol']}, coef={single['coef']:.1f}")
        print(f"  A_PF={single['phase_a_pf']:.4f}  B_PF={single['phase_b_pf']:.4f}  Robustness={single['robustness']:.4f}")
        # Use single if blocks not found
        if not b1 and not b2:
            b1 = single
            print("\n[Using SINGLE RUN result]")
    except FileNotFoundError:
        if not b1 and not b2:
            raise FileNotFoundError("No Phase 4 results found!")

    # Select best by robustness
    if b1 and b2:
        best = b1 if b1["robustness"] >= b2["robustness"] else b2
        source = "BLOCK 1 (TANK)" if best is b1 else "BLOCK 2 (VPS)"
    else:
        best = b1 or b2
        source = "BLOCK 1 (TANK)" if b1 else "BLOCK 2 (VPS)" if b2 else "SINGLE RUN"

    print(f"\n[BEST] Selected from {source}:")
    print(f"  quality={best['quality']}, recent={best['recent']}, "
          f"ref_vol={best['ref_vol']}, coef={best['coef']:.1f}")
    print(f"  Robustness={best['robustness']:.4f}  A_PF={best['phase_a_pf']:.4f}  B_PF={best['phase_b_pf']:.4f}")

    consolidated = {
        "phase": 4,
        "stops_best": {
            "stop_intelligent_quality": best["quality"],
            "stop_intelligent_recent_volat": best["recent"],
            "stop_intelligent_ref_volat": best["ref_vol"],
            "stop_intelligent_coef_volat": best["coef"],
            "phase4_robustness": best["robustness"],
        },
        "phase_a_pf": best["phase_a_pf"],
        "phase_b_pf": best["phase_b_pf"],
    }

    with open("phase4_5m_best_params.json", "w") as f:
        json.dump(consolidated, f, indent=2)
    print("\n[OK] phase4_5m_best_params.json")

    print("\n" + "=" * 70)
    print("PHASE 4 (5m) CONSOLIDATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    consolidate()
