"""
COMB_002_IMPULSE V2 — Consolidador Final (por régimen)

Lee los 12 archivos COMB002_V2_phase5_*_final_by_regime.json
y produce un JSON maestro unificado con params deployables por (asset, TF, régimen).

Genera también:
  - CSV de decisiones (auditoría)
  - Resumen con conteos por status

Uso:
  python3 consolidate_COMB002_V2_final.py
  python3 consolidate_COMB002_V2_final.py --output-dir ./final/
"""

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

ASSETS     = ["ES", "MNQ", "YM", "FDAX"]
TIMEFRAMES = ["5m", "10m", "15m"]
REGIMES    = ["low_vol", "med_vol", "high_vol"]


def main():
    parser = argparse.ArgumentParser(description="V2 Final Consolidator")
    parser.add_argument("--input-dir", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    in_dir = args.input_dir.resolve()
    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*80}")
    print(f"COMB_002 V2 — Final Consolidator (per regime)")
    print(f"{'='*80}\n")

    master = {
        "strategy": "COMB_002_IMPULSE_V2",
        "consolidation_date": date.today().strftime("%Y-%m-%d"),
        "method": "walkforward_regime_aware",
        "n_regimes": 3,
        "entries": {},
    }
    decisions = []
    counts = {"OK": 0, "DEGRADED": 0, "REJECTED": 0, "NO_PARAMS": 0, "MISSING_FILE": 0}

    for asset in ASSETS:
        for tf in TIMEFRAMES:
            key = f"{asset}_{tf}"
            src = in_dir / f"COMB002_V2_phase5_{asset}_{tf}_final_by_regime.json"

            if not src.exists():
                master["entries"][key] = {"status": "MISSING_FILE", "regimes": {}}
                counts["MISSING_FILE"] += 3
                print(f"  [{asset} {tf}] MISSING {src.name}")
                continue

            with open(src) as fh:
                p5 = json.load(fh)

            entry = {
                "asset": asset, "timeframe": tf,
                "atr_thresholds": p5.get("atr_thresholds", {}),
                "regimes": {},
            }

            for regime in REGIMES:
                rdata = p5.get("final_by_regime", {}).get(regime, {})
                status = rdata.get("status", "NO_PARAMS")
                counts[status] = counts.get(status, 0) + 1

                entry["regimes"][regime] = rdata

                decisions.append({
                    "asset": asset, "timeframe": tf, "regime": regime,
                    "status": status,
                    "reason": rdata.get("reason", ""),
                    "native_min_pf": rdata.get("native_score", {}).get("min_pf"),
                    "native_cv": rdata.get("native_score", {}).get("cv"),
                    "native_min_trades": rdata.get("native_score", {}).get("min_trades"),
                    "cross_min_pf": rdata.get("cross_regime_score", {}).get("min_pf"),
                    "cross_max_pf": rdata.get("cross_regime_score", {}).get("max_pf"),
                })

                icon = {"OK": "✅", "DEGRADED": "⚠️", "REJECTED": "❌", "NO_PARAMS": "❌"}.get(status, "?")
                print(f"  [{asset:<4} {tf:<4} {regime:<9}] {icon} {status}")

            master["entries"][key] = entry

    master_file = out_dir / "COMB002_V2_FINAL_PARAMS.json"
    with open(master_file, "w") as fh:
        json.dump(master, fh, indent=2)
    print(f"\n[OK] {master_file}")

    csv_file = out_dir / "COMB002_V2_FINAL_decisions.csv"
    fields = ["asset", "timeframe", "regime", "status", "reason",
              "native_min_pf", "native_cv", "native_min_trades",
              "cross_min_pf", "cross_max_pf"]
    with open(csv_file, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(decisions)
    print(f"[OK] {csv_file}")

    total_slots = len(ASSETS) * len(TIMEFRAMES) * len(REGIMES)
    print(f"\n{'='*80}")
    print(f"SUMMARY ({total_slots} slots = 4 assets × 3 TFs × 3 regímenes):")
    for s, n in counts.items():
        print(f"  {s:<15}: {n}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
