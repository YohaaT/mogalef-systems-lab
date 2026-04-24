"""Phase 4 (5m) Consolidation - Merge Block 1 + Block 2, select best (Mogalef-Strict version)"""

import json
from pathlib import Path

def consolidate():
    print("="*70)
    print("PHASE 4 (5m) STOPS CONSOLIDATION (MOGALEF-STRICT)")
    print("="*70)

    # Try to load Block 1 (TANK)
    try:
        with open("phase4_5m_stops_block_1_best_params.json") as f:
            b1 = json.load(f)
        print("\n[BLOCK 1 / TANK]  quality=%d, recent=%d, ref_vol=%d, coef=%.1f" % (
            b1["quality"], b1["recent"], b1["ref_vol"], b1["coef"]))
        print("  A_PF=%.4f  B_PF=%.4f  Robustness=%.4f" % (b1["phase_a_pf"], b1["phase_b_pf"], b1["robustness"]))
    except FileNotFoundError:
        b1 = None
        print("\n[BLOCK 1 / TANK]  Not found")

    # Try to load Block 2 (VPS)
    try:
        with open("phase4_5m_stops_block_2_best_params.json") as f:
            b2 = json.load(f)
        print("\n[BLOCK 2 / VPS]   quality=%d, recent=%d, ref_vol=%d, coef=%.1f" % (
            b2["quality"], b2["recent"], b2["ref_vol"], b2["coef"]))
        print("  A_PF=%.4f  B_PF=%.4f  Robustness=%.4f" % (b2["phase_a_pf"], b2["phase_b_pf"], b2["robustness"]))
    except FileNotFoundError:
        b2 = None
        print("\n[BLOCK 2 / VPS]   Not found")

    # Try single block (if run as single)
    try:
        with open("phase4_5m_stops_best_params.json") as f:
            single = json.load(f)
        print("\n[SINGLE RUN]      quality=%d, recent=%d, ref_vol=%d, coef=%.1f" % (
            single["quality"], single["recent"], single["ref_vol"], single["coef"]))
        print("  A_PF=%.4f  B_PF=%.4f  Robustness=%.4f" % (single["phase_a_pf"], single["phase_b_pf"], single["robustness"]))
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

    print("\n[BEST] Selected from %s:" % source)
    print("  quality=%d, recent=%d, ref_vol=%d, coef=%.1f" % (best["quality"], best["recent"], best["ref_vol"], best["coef"]))
    print("  Robustness=%.4f  A_PF=%.4f  B_PF=%.4f" % (best["robustness"], best["phase_a_pf"], best["phase_b_pf"]))

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

    with open("phase4_5m_best_params_mogalef_strict.json", "w") as f:
        json.dump(consolidated, f, indent=2)
    print("\n[OK] phase4_5m_best_params_mogalef_strict.json")

    print("\n" + "="*70)
    print("PHASE 4 (5m) CONSOLIDATION COMPLETE")
    print("="*70)

if __name__ == "__main__":
    consolidate()
