"""
V2 Consolidation — Merge Phase 5 results from all asset/TF combinations

Input:  COMB002_V2_phase5_*_final_by_regime.json (4-5 files from BO + TANK)
Output: COMB002_V2_CONSOLIDATED_FINAL_PARAMS.json (all best params by asset/TF/regime)
        COMB002_V2_CONSOLIDATION_REPORT.txt (summary)

Usage:
  python3 consolidate_COMB002_V2_final.py
"""

import json
from pathlib import Path

def consolidate():
    """Merge all Phase 5 final results into consolidated param file."""

    consolidated = {
        "timestamp": "2026-04-25",
        "version": "V2_final",
        "assets": {}
    }

    # Find all Phase 5 final JSONs
    phase5_files = list(Path(".").glob("COMB002_V2_phase5_*_final_by_regime.json"))

    if not phase5_files:
        print("[ERROR] No Phase 5 final results found!")
        return False

    print(f"[OK] Found {len(phase5_files)} Phase 5 final files")

    total_params = 0

    for phase5_file in sorted(phase5_files):
        print(f"  Reading {phase5_file.name}...")

        with open(phase5_file) as f:
            data = json.load(f)

        asset = data.get("asset")
        timeframe = data.get("timeframe")
        key = f"{asset}_{timeframe}"

        if key not in consolidated["assets"]:
            consolidated["assets"][key] = {
                "asset": asset,
                "timeframe": timeframe,
                "regimes": {}
            }

        # Merge regime results
        regimes = data.get("by_regime", {})
        for regime, params in regimes.items():
            if regime not in consolidated["assets"][key]["regimes"]:
                consolidated["assets"][key]["regimes"][regime] = params
                total_params += 1

    # Write consolidated
    out_file = Path("COMB002_V2_CONSOLIDATED_FINAL_PARAMS.json")
    with open(out_file, "w") as f:
        json.dump(consolidated, f, indent=2)

    print(f"\n[OK] {out_file} written ({total_params} params)")

    # Summary report
    report = f"""
V2 CONSOLIDATION REPORT
========================
Timestamp: 2026-04-25

Assets/TF Processed:
{json.dumps(list(consolidated['assets'].keys()), indent=2)}

Total parameter sets: {total_params}
Status: Ready for holdout validation

Next step: validate_COMB002_V2_holdout.py
"""

    with open("COMB002_V2_CONSOLIDATION_REPORT.txt", "w") as f:
        f.write(report)

    print("[OK] COMB002_V2_CONSOLIDATION_REPORT.txt written")
    return True

if __name__ == "__main__":
    print("\n" + "="*80)
    print("V2 CONSOLIDATION — Merging Phase 5 Results")
    print("="*80 + "\n")

    success = consolidate()

    if success:
        print("\n[SUCCESS] Consolidation complete!")
        print("Files ready:")
        print("  - COMB002_V2_CONSOLIDATED_FINAL_PARAMS.json")
        print("  - COMB002_V2_CONSOLIDATION_REPORT.txt")
    else:
        print("\n[FAILED] Check logs above")

    print("\n" + "="*80 + "\n")
