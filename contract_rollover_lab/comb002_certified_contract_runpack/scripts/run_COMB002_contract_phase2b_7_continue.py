"""Continue COMB002 contract-active optimization from Phase 2B to Phase 7.

This runner reuses the certified contract-active datasets plus the saved
Phase 2A results. It does not rerun Phase 0/1/2A. It is meant to be started on
BO/TANK independently with a dataset split so the servers can share load.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
from pathlib import Path
from types import SimpleNamespace

from run_COMB002_contract_phase0_7 import (
    build_dataset,
    phase2b,
    phase3,
    phase4,
    phase5,
    phase6_holdout,
    phase7_consistency,
    write_json,
)


ROOT = Path(__file__).resolve().parents[1]


def load_phase2a_top(phase2a_dir: Path, asset: str, timeframe: str, stem: str) -> list[dict]:
    json_path = phase2a_dir / asset / timeframe / f"{stem}_phase2a_signal_madrid_results.json"
    if not json_path.exists():
        raise FileNotFoundError(f"Missing phase2a results for {asset} {timeframe}: {json_path}")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    top = payload.get("top", [])
    if not top:
        raise ValueError(f"Phase2A top list is empty for {asset} {timeframe}: {json_path}")
    return top


def run_one(job: dict) -> dict:
    args = SimpleNamespace(**job["args"])
    asset = job["asset"]
    timeframe = job["timeframe"]
    out_dir = Path(args.out_dir) / asset / timeframe
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"COMB002_contract_{asset}_{timeframe}_{args.roll_rule}_label_{args.bar_label}"

    phase7_path = out_dir / f"{stem}_phase7_consistency_summary.json"
    if phase7_path.exists():
        return {"asset": asset, "timeframe": timeframe, "status": "SKIP_DONE", "phase7": str(phase7_path)}

    dataset, manifest, dataset_path = build_dataset(args, asset, timeframe, out_dir)
    split_idx = max(1, int(len(dataset.ordered_contracts) * args.train_ratio))
    if split_idx >= len(dataset.ordered_contracts):
        split_idx = len(dataset.ordered_contracts) - 1
    train_contracts = dataset.ordered_contracts[:split_idx]
    holdout_contracts = dataset.ordered_contracts[split_idx:]
    train = dataset.subset(train_contracts)
    holdout = dataset.subset(holdout_contracts)

    p2a_top = load_phase2a_top(Path(args.phase2a_dir), asset, timeframe, stem)
    p2b, thresholds = phase2b(train, out_dir, stem, p2a_top)
    p3 = phase3(train, out_dir, stem, p2b, thresholds)
    p4 = phase4(train, out_dir, stem, p3, thresholds)
    p5 = phase5(train, out_dir, stem, p4, thresholds)
    holdout_rows = phase6_holdout(holdout, out_dir, stem, p5)
    full_rows = phase7_consistency(dataset, out_dir, stem, p5)

    summary = {
        "phase": "contract_phase2b_7_continuation",
        "asset": asset,
        "timeframe": timeframe,
        "roll_rule": args.roll_rule,
        "bar_label": args.bar_label,
        "data_source": str(args.data_dir),
        "dataset_path": str(dataset_path),
        "segment_manifest": manifest,
        "train_contracts": train_contracts,
        "holdout_contracts": holdout_contracts,
        "phase2a_top": p2a_top[:3],
        "phase2b": p2b,
        "phase3": p3,
        "phase4": p4,
        "phase5": p5,
        "phase6_holdout_rows": len(holdout_rows),
        "phase7_full_rows": len(full_rows),
    }
    write_json(out_dir / f"{stem}_phase2b_7_continuation_summary.json", summary)
    return {
        "asset": asset,
        "timeframe": timeframe,
        "status": "OK",
        "phase7": str(phase7_path),
        "train_contracts": len(train_contracts),
        "holdout_contracts": len(holdout_contracts),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Continue COMB002 contract-active phases 2B-7")
    parser.add_argument("--assets", default="ES,FDAX,NQ")
    parser.add_argument("--timeframes", default="15m,10m,5m")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data" / "contracts")
    parser.add_argument("--phase2a-dir", type=Path, default=ROOT / "outputs" / "contract_phase2a_signal_madrid")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "outputs" / "contract_phase2b_7")
    parser.add_argument("--roll-rule", default="friday_to_expiry_week_monday")
    parser.add_argument("--bar-label", default="left")
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--contracts", default="")
    parser.add_argument("--no-saturday", action="store_true", default=True)
    parser.add_argument("--allow-saturday", action="store_false", dest="no_saturday")
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()

    assets = [item.strip() for item in args.assets.split(",") if item.strip()]
    timeframes = [item.strip() for item in args.timeframes.split(",") if item.strip()]
    jobs = [
        {
            "asset": asset,
            "timeframe": timeframe,
            "args": {
                "data_dir": str(args.data_dir),
                "phase2a_dir": str(args.phase2a_dir),
                "out_dir": str(args.out_dir),
                "roll_rule": args.roll_rule,
                "bar_label": args.bar_label,
                "train_ratio": args.train_ratio,
                "contracts": args.contracts,
                "no_saturday": args.no_saturday,
            },
        }
        for timeframe in timeframes
        for asset in assets
    ]

    results: list[dict] = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        future_to_job = {pool.submit(run_one, job): job for job in jobs}
        for future in concurrent.futures.as_completed(future_to_job):
            result = future.result()
            print(
                f"{result['asset']:<5} {result['timeframe']:<4} "
                f"{result['status']}",
                flush=True,
            )
            results.append(result)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.out_dir / "contract_phase2b_7_continuation_summary.json"
    write_json(
        summary_path,
        {
            "phase": "contract_phase2b_7_continuation_summary",
            "assets": assets,
            "timeframes": timeframes,
            "workers": args.workers,
            "results": results,
        },
    )
    print(f"\n[OK] Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
