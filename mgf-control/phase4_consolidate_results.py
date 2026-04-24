"""Phase 4 Consolidation - Merge Block 1 + Block 2 results and select best."""

import json
from pathlib import Path

def consolidate_phase4():
    """Load Phase 4 best params from both blocks, consolidate."""

    print("=" * 80)
    print("PHASE 4 CONSOLIDATION")
    print("=" * 80)

    # Try to load from Block 1 (TANK)
    try:
        with open("phase4_stops_optimization_block_1_best_params.json") as f:
            block1_result = json.load(f)
        print(f"\n[BLOCK 1] Loaded Phase 4 result:")
        print(f"  quality={block1_result['quality']}, recent={block1_result['recent']}, ref={block1_result['ref_vol']}, coef={block1_result['coef']}")
        print(f"  Robustness={block1_result['robustness']:.4f}")
    except FileNotFoundError:
        block1_result = None
        print("\n[BLOCK 1] No Phase 4 results found")

    # Try to load from Block 2 (VPS)
    try:
        with open("bo_phase4_stops_optimization_block_2_best_params.json") as f:
            block2_result = json.load(f)
        print(f"\n[BLOCK 2] Loaded Phase 4 result:")
        print(f"  quality={block2_result['quality']}, recent={block2_result['recent']}, ref={block2_result['ref_vol']}, coef={block2_result['coef']}")
        print(f"  Robustness={block2_result['robustness']:.4f}")
    except FileNotFoundError:
        block2_result = None
        print("\n[BLOCK 2] No Phase 4 results found")

    # Select best (by robustness)
    if block1_result and block2_result:
        if block1_result['robustness'] >= block2_result['robustness']:
            best = block1_result
            source = "BLOCK 1 (TANK)"
        else:
            best = block2_result
            source = "BLOCK 2 (VPS)"
    elif block1_result:
        best = block1_result
        source = "BLOCK 1 (TANK)"
    elif block2_result:
        best = block2_result
        source = "BLOCK 2 (VPS)"
    else:
        raise FileNotFoundError("No Phase 4 results found from either block!")

    print(f"\n[BEST] Selected from {source}:")
    print(f"  quality={best['quality']}")
    print(f"  recent={best['recent']}")
    print(f"  ref_vol={best['ref_vol']}")
    print(f"  coef={best['coef']}")
    print(f"  Robustness={best['robustness']:.4f}")

    # Write consolidated result
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

    with open("phase4_best_params.json", "w") as f:
        json.dump(consolidated, f, indent=2)
    print(f"\n[OK] phase4_best_params.json")

    print("\n" + "=" * 80)
    print("PHASE 4 CONSOLIDATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    consolidate_phase4()
