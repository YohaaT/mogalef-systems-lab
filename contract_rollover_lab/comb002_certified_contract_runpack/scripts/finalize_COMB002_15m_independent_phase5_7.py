"""Finalize COMB002 15m independent candidates through Phase 5/6/7.

Independent optimization means each family of parameters starts from the
Phase 1 context/baseline, not from the previous phase. This script takes the
best available candidate from each independent Phase2B/3/4 result CSV and
validates it on:

- Phase 5: train contracts
- Phase 6: holdout contracts
- Phase 7: full contract-active history
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "mgf-control", ROOT / "contract_rollover_lab" / "scripts", ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from annual_pf_from_forward_results import (
    lane_from_path,
    normalize_candidate,
    parse_asset_timeframe,
    phase_from_name,
    read_rows,
    select_candidate,
)
from run_COMB002_contract_phase0_7 import build_dataset, result_metrics, run_params_on_dataset, write_json
from run_COMB002_contract_phase2a_forward_dual import params_from_row, write_csv


def trade_year(timestamp: str) -> int:
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).year


def annual_metrics(trades: list) -> dict[str, dict]:
    by_year: dict[int, list] = defaultdict(list)
    for trade in trades:
        by_year[trade_year(trade.exit_timestamp)].append(trade)
    return {str(year): result_metrics(items) for year, items in sorted(by_year.items())}


def flatten_metrics(prefix: str, metrics: dict) -> dict:
    return {
        f"{prefix}_trades": metrics.get("trades"),
        f"{prefix}_pf": metrics.get("profit_factor"),
        f"{prefix}_equity_points": metrics.get("equity_points"),
        f"{prefix}_max_dd": metrics.get("max_drawdown"),
        f"{prefix}_win_rate": metrics.get("win_rate"),
    }


def finalize_one(path: Path, args: argparse.Namespace, dataset_cache: dict) -> dict:
    candidate = select_candidate(read_rows(path))
    if not candidate:
        raise ValueError(f"No candidate rows in {path}")
    candidate = normalize_candidate(candidate)
    asset, timeframe = parse_asset_timeframe(path)

    cache_key = (asset, timeframe)
    if cache_key not in dataset_cache:
        dataset_args = SimpleNamespace(
            data_dir=args.data_dir,
            roll_rule=args.roll_rule,
            bar_label=args.bar_label,
            contracts=args.contracts,
            no_saturday=args.no_saturday,
        )
        dataset_cache[cache_key] = build_dataset(dataset_args, asset, timeframe, args.work_dir / asset / timeframe)[0]
    dataset = dataset_cache[cache_key]

    split_idx = max(1, int(len(dataset.ordered_contracts) * args.train_ratio))
    if split_idx >= len(dataset.ordered_contracts):
        split_idx = len(dataset.ordered_contracts) - 1
    train_contracts = dataset.ordered_contracts[:split_idx]
    holdout_contracts = dataset.ordered_contracts[split_idx:]
    train = dataset.subset(train_contracts)
    holdout = dataset.subset(holdout_contracts)

    params = params_from_row(candidate)
    train_trades = run_params_on_dataset(params, train)
    holdout_trades = run_params_on_dataset(params, holdout)
    full_trades = run_params_on_dataset(params, dataset)

    payload = {
        "asset": asset,
        "timeframe": timeframe,
        "lane": lane_from_path(path),
        "source_phase": phase_from_name(path),
        "source_file": str(path.relative_to(ROOT)),
        "train_contracts": train_contracts,
        "holdout_contracts": holdout_contracts,
        "candidate": candidate,
        "phase5_train": result_metrics(train_trades),
        "phase6_holdout": result_metrics(holdout_trades),
        "phase7_full_history": result_metrics(full_trades),
        "phase7_by_year": annual_metrics(full_trades),
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Finalize COMB002 15m independent Phase5/6/7")
    parser.add_argument("--assets", default="ES,FDAX,NQ")
    parser.add_argument("--timeframe", default="15m")
    parser.add_argument("--results-dir", type=Path, default=ROOT / "outputs" / "contract_phase2a_forward_dual")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "outputs" / "independent_phase5_7")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data" / "contracts")
    parser.add_argument("--work-dir", type=Path, default=ROOT / "outputs" / "independent_phase5_7" / "datasets")
    parser.add_argument("--roll-rule", default="friday_to_expiry_week_monday")
    parser.add_argument("--bar-label", default="left")
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--contracts", default="")
    parser.add_argument("--no-saturday", action="store_true", default=True)
    parser.add_argument("--allow-saturday", action="store_false", dest="no_saturday")
    args = parser.parse_args()

    assets = {item.strip() for item in args.assets.split(",") if item.strip()}
    result_files = [
        path
        for path in sorted(args.results_dir.glob(f"*/{args.timeframe}/independent_from_phase2a/*from_phase1*results.csv"))
        if parse_asset_timeframe(path)[0] in assets
    ]

    dataset_cache: dict = {}
    payloads = [finalize_one(path, args, dataset_cache) for path in result_files]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / f"COMB002_{args.timeframe}_independent_from_phase1_phase5_7_summary.json"
    csv_path = args.out_dir / f"COMB002_{args.timeframe}_independent_from_phase1_phase5_7_summary.csv"

    write_json(json_path, {"phase": "independent_phase5_6_7", "results": payloads})

    rows: list[dict] = []
    for item in payloads:
        row = {
            "asset": item["asset"],
            "timeframe": item["timeframe"],
            "lane": item["lane"],
            "source_phase": item["source_phase"],
            "source_file": item["source_file"],
            "candidate_passes_filters": item["candidate"].get("passes_filters"),
            "candidate_min_pf": item["candidate"].get("min_pf"),
            "candidate_mean_pf": item["candidate"].get("mean_pf"),
            "candidate_reject_reason": item["candidate"].get("reject_reason"),
            "atr_min": item["candidate"].get("atr_min", "0.0"),
            "atr_max": item["candidate"].get("atr_max", "500.0"),
            "scalp_coef": item["candidate"].get("scalp_coef", "3.0"),
            "timescan": item["candidate"].get("timescan", "15"),
            "superstop_quality": item["candidate"].get("superstop_quality", "2"),
            "superstop_coef_volat": item["candidate"].get("superstop_coef_volat", "3.0"),
        }
        row.update(flatten_metrics("phase5_train", item["phase5_train"]))
        row.update(flatten_metrics("phase6_holdout", item["phase6_holdout"]))
        row.update(flatten_metrics("phase7_full", item["phase7_full_history"]))
        rows.append(row)
    write_csv(csv_path, rows)
    print(f"wrote {len(rows)} summaries: {csv_path}")
    print(f"wrote details: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
