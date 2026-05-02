"""Compute yearly PF for COMB002 forward/independent result artifacts.

The optimizer scores by contract folds. This report reruns selected parameter
rows on the full contract-active dataset and groups completed trades by exit
year, so we can inspect annual stability.
"""

from __future__ import annotations

import argparse
import ast
import csv
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "mgf-control", ROOT / "contract_rollover_lab" / "scripts", ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from run_COMB002_contract_phase0_7 import build_dataset, result_metrics, run_params_on_dataset
from run_COMB002_contract_phase2a_forward_dual import params_from_row, write_csv


def as_float(row: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, "") or default)
    except ValueError:
        return default


def parse_asset_timeframe(path: Path) -> tuple[str, str]:
    parts = path.parts
    for idx, part in enumerate(parts):
        if part in {"ES", "FDAX", "NQ"} and idx + 1 < len(parts):
            return part, parts[idx + 1]
    stem = path.name
    pieces = stem.split("_")
    if len(pieces) >= 4:
        return pieces[2], pieces[3]
    raise ValueError(f"Cannot infer asset/timeframe from {path}")


def read_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def select_candidate(rows: list[dict]) -> dict | None:
    if not rows:
        return None
    ranked = list(rows)
    ranked.sort(
        key=lambda row: (
            row.get("passes_filters") == "True",
            as_float(row, "min_pf"),
            -as_float(row, "cv", 999.0),
            as_float(row, "mean_pf"),
            as_float(row, "min_trades"),
        ),
        reverse=True,
    )
    return ranked[0]


def normalize_candidate(row: dict) -> dict:
    out = dict(row)
    for key in ("windows_hhmm", "blocked_weekdays"):
        value = out.get(key)
        if isinstance(value, str):
            try:
                out[key] = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                out[key] = [] if key == "windows_hhmm" else []
    return out


def phase_from_name(path: Path) -> str:
    name = path.name
    if "_phase2b_" in name:
        return "phase2b"
    if "_phase3_" in name:
        return "phase3"
    if "_phase4_" in name:
        return "phase4"
    if "_phase2a_" in name:
        return "phase2a"
    return "unknown"


def lane_from_path(path: Path) -> str:
    text = str(path).replace("\\", "/")
    if "/independent_from_phase2a/" in text:
        return "independent_from_phase1"
    if "/accumulated/" in text:
        return "accumulated"
    return "unknown"


def trade_year(timestamp: str) -> int:
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).year


def annual_rows_for_candidate(path: Path, candidate: dict, args: argparse.Namespace, dataset_cache: dict) -> list[dict]:
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
    candidate = normalize_candidate(candidate)
    params = params_from_row(candidate)
    trades = run_params_on_dataset(params, dataset)

    by_year: dict[int, list] = defaultdict(list)
    for trade in trades:
        by_year[trade_year(trade.exit_timestamp)].append(trade)

    rows: list[dict] = []
    common = {
        "asset": asset,
        "timeframe": timeframe,
        "lane": lane_from_path(path),
        "phase": phase_from_name(path),
        "source_file": str(path.relative_to(ROOT)),
        "candidate_passes_filters": candidate.get("passes_filters"),
        "candidate_reject_reason": candidate.get("reject_reason"),
        "candidate_min_pf": candidate.get("min_pf"),
        "candidate_mean_pf": candidate.get("mean_pf"),
        "candidate_cv": candidate.get("cv"),
        "smooth_h": candidate.get("smooth_h"),
        "smooth_b": candidate.get("smooth_b"),
        "dist_max_h": candidate.get("dist_max_h"),
        "dist_max_l": candidate.get("dist_max_l"),
        "atr_min": candidate.get("atr_min", "0.0"),
        "atr_max": candidate.get("atr_max", "500.0"),
        "scalp_coef": candidate.get("scalp_coef", "3.0"),
        "timescan": candidate.get("timescan", "15"),
        "superstop_quality": candidate.get("superstop_quality", "2"),
        "superstop_coef_volat": candidate.get("superstop_coef_volat", "3.0"),
        "phase1_horario": candidate.get("phase1_horario"),
        "phase1_filtro": candidate.get("phase1_filtro"),
    }
    overall = result_metrics(trades)
    rows.append({**common, "year": "ALL", **overall})
    for year in sorted(by_year):
        rows.append({**common, "year": year, **result_metrics(by_year[year])})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Build yearly PF report from COMB002 result CSVs")
    parser.add_argument("--results-dir", type=Path, default=ROOT / "outputs" / "contract_phase2a_forward_dual")
    parser.add_argument("--out", type=Path, default=ROOT / "outputs" / "annual_pf" / "COMB002_forward_best_candidates_annual_pf.csv")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data" / "contracts")
    parser.add_argument("--work-dir", type=Path, default=ROOT / "outputs" / "annual_pf" / "datasets")
    parser.add_argument("--roll-rule", default="friday_to_expiry_week_monday")
    parser.add_argument("--bar-label", default="left")
    parser.add_argument("--contracts", default="")
    parser.add_argument("--no-saturday", action="store_true", default=True)
    parser.add_argument("--allow-saturday", action="store_false", dest="no_saturday")
    parser.add_argument("--include-accumulated", action="store_true")
    args = parser.parse_args()

    result_files = sorted(args.results_dir.glob("*/*/**/*results.csv"))
    if not args.include_accumulated:
        result_files = [path for path in result_files if "from_phase1" in path.name]
    rows: list[dict] = []
    dataset_cache: dict = {}
    for path in result_files:
        candidate = select_candidate(read_rows(path))
        if not candidate:
            continue
        rows.extend(annual_rows_for_candidate(path, candidate, args, dataset_cache))

    write_csv(args.out, rows)
    print(f"wrote {len(rows)} rows: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
