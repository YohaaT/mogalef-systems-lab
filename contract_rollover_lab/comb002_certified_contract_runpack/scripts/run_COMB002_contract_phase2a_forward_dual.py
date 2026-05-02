"""Run COMB002 optimization forward from certified Phase 2A.

This runner preserves the Phase 1 context embedded in Phase 2A results:
Madrid timezone, allowed windows and blocked weekdays. It writes two lanes:

- accumulated: Phase2A -> Phase2B -> Phase3 -> Phase4 -> Phase5/6/7
- independent_from_phase2a: Phase2B, Phase3 and Phase4 each start from Phase2A

Indicators are still computed by the strategy on full contract bars. Context,
ATR, exits and stops are applied as strategy parameters, not by pre-cutting the
OHLC series.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
MGF_CONTROL = ROOT / "mgf-control"
ROLL_SCRIPTS = ROOT / "contract_rollover_lab" / "scripts"
for path in (MGF_CONTROL, ROLL_SCRIPTS, ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from COMB_002_IMPULSE_V1 import Comb002ImpulseParams
from run_COMB002_contract_phase0_7 import (
    build_dataset,
    eval_params,
    score_params_by_contract_folds,
    write_json,
)


ATR_MIN_RANGE = [0.0, 5.0, 10.0, 20.0]
ATR_MAX_RANGE = [50.0, 100.0, 200.0, 500.0]
SCALP_COEF_RANGE = [2.0, 2.5, 3.0, 3.5, 4.0, 5.0]
TIMESCAN_RANGE = [10, 15, 20, 30, 45]
SUPERSTOP_QUALITY_RANGE = [1, 2, 3, 4]
SUPERSTOP_COEF_RANGE = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0]


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def select_top(rows: list[dict], n: int = 5) -> list[dict]:
    passed = [row for row in rows if row.get("passes_filters")]
    passed.sort(key=lambda row: (row["min_pf"], -row["cv"], row["mean_pf"]), reverse=True)
    return passed[:n]


def load_phase2a_top(phase2a_dir: Path, asset: str, timeframe: str, stem: str) -> list[dict]:
    json_path = phase2a_dir / asset / timeframe / f"{stem}_phase2a_signal_madrid_results.json"
    if not json_path.exists():
        raise FileNotFoundError(f"Missing Phase 2A results: {json_path}")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    top = payload.get("top", [])
    if top:
        return top

    # Independent lanes must not be blocked by a failed Phase 2A gate. When no
    # strict Phase 2A candidate passed, continue from the best scored rows and
    # keep the fallback explicit in downstream artifacts.
    fallback = list(payload.get("results", []))
    fallback.sort(
        key=lambda row: (
            float(row.get("min_pf", 0.0)),
            -float(row.get("cv", 999.0)),
            float(row.get("mean_pf", 0.0)),
            int(row.get("min_trades", 0)),
        ),
        reverse=True,
    )
    for row in fallback[:5]:
        row["phase2a_fallback_from_failed_gate"] = True
    return fallback[:5]


def params_from_row(row: dict) -> Comb002ImpulseParams:
    return Comb002ImpulseParams(
        stpmt_smooth_h=int(row["smooth_h"]),
        stpmt_smooth_b=int(row["smooth_b"]),
        stpmt_distance_max_h=float(row["dist_max_h"]),
        stpmt_distance_max_l=float(row["dist_max_l"]),
        horaire_timezone=str(row.get("timezone", "Europe/Madrid")),
        horaire_windows_hhmm=row.get("windows_hhmm", []),
        blocked_weekdays=row.get("blocked_weekdays", []),
        volatility_atr_min=float(row.get("atr_min", 0.0)),
        volatility_atr_max=float(row.get("atr_max", 500.0)),
        scalping_target_quality=2,
        scalping_target_recent_volat=2,
        scalping_target_ref_volat=20,
        scalping_target_coef_volat=float(row.get("scalp_coef", 3.0)),
        timescan_bars=int(row.get("timescan", 15)),
        superstop_quality=int(row.get("superstop_quality", 2)),
        superstop_coef_volat=float(row.get("superstop_coef_volat", 3.0)),
    )


def row_from_params(params: Comb002ImpulseParams, source: dict, extra: dict | None = None) -> dict:
    row = {
        "asset": source.get("asset"),
        "timeframe": source.get("timeframe"),
        "smooth_h": params.stpmt_smooth_h,
        "smooth_b": params.stpmt_smooth_b,
        "dist_max_h": params.stpmt_distance_max_h,
        "dist_max_l": params.stpmt_distance_max_l,
        "phase1_horario": source.get("phase1_horario"),
        "phase1_filtro": source.get("phase1_filtro"),
        "timezone": params.horaire_timezone,
        "windows_hhmm": params.horaire_windows_hhmm,
        "blocked_weekdays": params.blocked_weekdays,
        "atr_min": params.volatility_atr_min,
        "atr_max": params.volatility_atr_max,
        "scalp_coef": params.scalping_target_coef_volat,
        "timescan": params.timescan_bars,
        "superstop_quality": params.superstop_quality,
        "superstop_coef_volat": params.superstop_coef_volat,
    }
    if extra:
        row.update(extra)
    return row


def grid_atr(base: list[dict], dataset) -> list[dict]:
    rows: list[dict] = []
    for base_idx, item in enumerate(base):
        for atr_min, atr_max in product(ATR_MIN_RANGE, ATR_MAX_RANGE):
            if atr_min >= atr_max:
                continue
            params = params_from_row({**item, "atr_min": atr_min, "atr_max": atr_max})
            score = score_params_by_contract_folds(params, dataset)
            rows.append({**row_from_params(params, item, {"base_idx": base_idx}), **score})
    return rows


def grid_exits(base: list[dict], dataset) -> list[dict]:
    rows: list[dict] = []
    for base_idx, item in enumerate(base):
        for scalp_coef, timescan in product(SCALP_COEF_RANGE, TIMESCAN_RANGE):
            params = params_from_row({**item, "scalp_coef": scalp_coef, "timescan": timescan})
            score = score_params_by_contract_folds(params, dataset)
            rows.append({**row_from_params(params, item, {"base_idx": base_idx}), **score})
    return rows


def grid_stops(base: list[dict], dataset) -> list[dict]:
    rows: list[dict] = []
    for base_idx, item in enumerate(base):
        for ss_q, ss_c in product(SUPERSTOP_QUALITY_RANGE, SUPERSTOP_COEF_RANGE):
            params = params_from_row({**item, "superstop_quality": ss_q, "superstop_coef_volat": ss_c})
            score = score_params_by_contract_folds(params, dataset)
            rows.append({**row_from_params(params, item, {"base_idx": base_idx}), **score})
    return rows


def write_grid(out_dir: Path, stem: str, phase: str, rows: list[dict]) -> list[dict]:
    rows.sort(key=lambda row: (row.get("passes_filters", False), row.get("min_pf", 0.0), -row.get("cv", 999.0), row.get("mean_pf", 0.0)), reverse=True)
    top = select_top(rows)
    write_csv(out_dir / f"{stem}_{phase}_results.csv", rows)
    write_json(
        out_dir / f"{stem}_{phase}_top_params.json",
        {"phase": phase, "n_combos": len(rows), "n_passed": len([r for r in rows if r.get("passes_filters")]), "top": top},
    )
    return top


def validate_final(out_dir: Path, stem: str, top: list[dict], train, holdout, full) -> dict:
    if not top:
        payload = {"status": "NO_PARAMS", "reason": "phase4 produced no passing params"}
        write_json(out_dir / f"{stem}_phase5_accumulated_validation.json", payload)
        return payload
    best = top[0]
    params = params_from_row(best)
    train_score = score_params_by_contract_folds(params, train)
    holdout_metrics = eval_params(params, holdout)
    full_metrics = eval_params(params, full)
    payload = {
        "status": "OK" if train_score.get("passes_filters") else "REVIEW",
        "params": best,
        "phase5_train_score": train_score,
        "phase6_holdout": holdout_metrics,
        "phase7_full_history": full_metrics,
    }
    write_json(out_dir / f"{stem}_phase5_accumulated_validation.json", payload)
    return payload


def run_one(job: dict) -> dict:
    args = SimpleNamespace(**job["args"])
    args.data_dir = Path(args.data_dir)
    args.phase2a_dir = Path(args.phase2a_dir)
    args.out_dir = Path(args.out_dir)
    asset = job["asset"]
    timeframe = job["timeframe"]
    lanes = set(job["lanes"])
    independent_timeframes = set(job["independent_timeframes"])
    end_phase = job["end_phase"]
    run_accumulated = "accumulated" in lanes
    run_independent = "independent" in lanes and timeframe in independent_timeframes
    out_dir = args.out_dir / asset / timeframe
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"COMB002_contract_{asset}_{timeframe}_{args.roll_rule}_label_{args.bar_label}"

    accumulated_done = out_dir / "accumulated" / f"{stem}_phase5_accumulated_validation.json"
    independent_done = out_dir / "independent_from_phase2a" / f"{stem}_phase4_from_phase2a_stops_top_params.json"
    if end_phase == "phase2b":
        accumulated_done = out_dir / "accumulated" / f"{stem}_phase2b_accumulated_atr_top_params.json"
        independent_done = out_dir / "independent_from_phase2a" / f"{stem}_phase2b_from_phase2a_atr_top_params.json"
    elif end_phase == "phase3":
        accumulated_done = out_dir / "accumulated" / f"{stem}_phase3_accumulated_exits_top_params.json"
        independent_done = out_dir / "independent_from_phase2a" / f"{stem}_phase3_from_phase2a_exits_top_params.json"
    if (not run_accumulated or accumulated_done.exists()) and (not run_independent or independent_done.exists()):
        return {"asset": asset, "timeframe": timeframe, "status": "SKIP_DONE"}

    dataset, manifest, dataset_path = build_dataset(args, asset, timeframe, out_dir)
    split_idx = max(1, int(len(dataset.ordered_contracts) * args.train_ratio))
    if split_idx >= len(dataset.ordered_contracts):
        split_idx = len(dataset.ordered_contracts) - 1
    train_contracts = dataset.ordered_contracts[:split_idx]
    holdout_contracts = dataset.ordered_contracts[split_idx:]
    train = dataset.subset(train_contracts)
    holdout = dataset.subset(holdout_contracts)

    phase2a_top = load_phase2a_top(args.phase2a_dir, asset, timeframe, stem)
    if not phase2a_top:
        return {"asset": asset, "timeframe": timeframe, "status": "SKIP_NO_PHASE2A_PASS"}

    acc_dir = out_dir / "accumulated"
    independent_dir = out_dir / "independent_from_phase2a"
    write_json(
        out_dir / f"{stem}_phase2a_forward_manifest.json",
        {
            "asset": asset,
            "timeframe": timeframe,
            "methodology": "phase1_context_preserved_indicators_full_contract_entries_filtered_by_params",
            "dataset_path": str(dataset_path),
            "segment_manifest": manifest,
            "train_contracts": train_contracts,
            "holdout_contracts": holdout_contracts,
            "phase2a_top": phase2a_top,
        },
    )

    final = {"status": "SKIPPED"}
    p2b_top: list[dict] = []
    p3_top: list[dict] = []
    p4_top: list[dict] = []
    if run_accumulated:
        p2b_rows = grid_atr(phase2a_top, train)
        p2b_top = write_grid(acc_dir, stem, "phase2b_accumulated_atr", p2b_rows)
        if end_phase in {"phase3", "phase4"}:
            p3_rows = grid_exits(p2b_top, train)
            p3_top = write_grid(acc_dir, stem, "phase3_accumulated_exits", p3_rows)
        if end_phase == "phase4":
            p4_rows = grid_stops(p3_top, train)
            p4_top = write_grid(acc_dir, stem, "phase4_accumulated_stops", p4_rows)
            final = validate_final(acc_dir, stem, p4_top, train, holdout, dataset)
        elif end_phase == "phase3":
            final = {"status": "STOPPED_AT_PHASE3"}
        else:
            final = {"status": "STOPPED_AT_PHASE2B"}

    ind_p2b_top: list[dict] = []
    ind_p3_top: list[dict] = []
    ind_p4_top: list[dict] = []
    if run_independent:
        ind_p2b_top = write_grid(independent_dir, stem, "phase2b_from_phase2a_atr", grid_atr(phase2a_top, train))
        if end_phase in {"phase3", "phase4"}:
            ind_p3_top = write_grid(independent_dir, stem, "phase3_from_phase2a_exits", grid_exits(phase2a_top, train))
        if end_phase == "phase4":
            ind_p4_top = write_grid(independent_dir, stem, "phase4_from_phase2a_stops", grid_stops(phase2a_top, train))

    return {
        "asset": asset,
        "timeframe": timeframe,
        "status": "OK",
        "lanes": sorted(lanes),
        "end_phase": end_phase,
        "independent_enabled": run_independent,
        "accumulated_status": final.get("status"),
        "accumulated_phase2b_passed": len(p2b_top),
        "accumulated_phase3_passed": len(p3_top),
        "accumulated_phase4_passed": len(p4_top),
        "independent_phase2b_passed": len(ind_p2b_top),
        "independent_phase3_passed": len(ind_p3_top),
        "independent_phase4_passed": len(ind_p4_top),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="COMB002 dual-lane optimization from Phase 2A")
    parser.add_argument("--assets", default="ES,FDAX,NQ")
    parser.add_argument("--timeframes", default="15m,10m,5m")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data" / "contracts")
    parser.add_argument("--phase2a-dir", type=Path, default=ROOT / "outputs" / "contract_phase2a_signal_madrid")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "outputs" / "contract_phase2a_forward_dual")
    parser.add_argument("--roll-rule", default="friday_to_expiry_week_monday")
    parser.add_argument("--bar-label", default="left")
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--contracts", default="")
    parser.add_argument("--no-saturday", action="store_true", default=True)
    parser.add_argument("--allow-saturday", action="store_false", dest="no_saturday")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--lanes", default="accumulated,independent")
    parser.add_argument("--independent-timeframes", default="")
    parser.add_argument("--end-phase", choices=["phase2b", "phase3", "phase4"], default="phase4")
    args = parser.parse_args()

    assets = [item.strip() for item in args.assets.split(",") if item.strip()]
    timeframes = [item.strip() for item in args.timeframes.split(",") if item.strip()]
    lanes = [item.strip() for item in args.lanes.split(",") if item.strip()]
    independent_timeframes = [
        item.strip()
        for item in (args.independent_timeframes or args.timeframes).split(",")
        if item.strip()
    ]
    jobs = [
        {
            "asset": asset,
            "timeframe": timeframe,
            "lanes": lanes,
            "independent_timeframes": independent_timeframes,
            "end_phase": args.end_phase,
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
            job = future_to_job[future]
            try:
                result = future.result()
            except FileNotFoundError as exc:
                result = {"asset": job["asset"], "timeframe": job["timeframe"], "status": "SKIP_MISSING_PHASE2A", "reason": str(exc)}
            except Exception as exc:
                result = {"asset": job["asset"], "timeframe": job["timeframe"], "status": "FAIL", "reason": repr(exc)}
            print(f"{result['asset']:<5} {result['timeframe']:<4} {result['status']}", flush=True)
            results.append(result)

    done = [row for row in results if row.get("status") in {"OK", "SKIP_DONE"}]
    missing_or_blocked = [row for row in results if row.get("status") not in {"OK", "SKIP_DONE"}]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        args.out_dir / "contract_phase2a_forward_dual_summary.json",
        {
            "phase": "contract_phase2a_forward_dual_summary",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "workers": args.workers,
            "assets": assets,
            "timeframes": timeframes,
            "lanes": lanes,
            "independent_timeframes": independent_timeframes,
            "end_phase": args.end_phase,
            "done_count": len(done),
            "missing_or_blocked_count": len(missing_or_blocked),
            "missing_or_blocked": missing_or_blocked,
            "results": results,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
