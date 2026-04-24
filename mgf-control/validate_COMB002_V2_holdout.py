"""
COMB_002_IMPULSE V2 — Hold-out Phase C Validator

Corre los params OK/DEGRADED de V2 sobre data Phase C (NUNCA vista en
optimización walk-forward). Por régimen.

Input : COMB002_V2_FINAL_PARAMS.json
        {ASSET}_phase_C_{TF}.csv (opcional — si falta, skip para ese asset/TF)
Output: COMB002_V2_holdout_results.csv
        COMB002_V2_holdout_report.md

Criterio de drift: |reported_min_pf - holdout_pf| / reported_min_pf ≤ 15%

Uso:
  python3 validate_COMB002_V2_holdout.py
"""

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

_here = Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

from COMB_002_IMPULSE_V1 import Comb002ImpulseStrategy, Comb002ImpulseParams, load_ohlc_csv
from COMB_002_IMPULSE_V2_walkforward import (
    filter_rows_by_regime, REGIME_LABELS, RegimeThresholds,
)


def build_params(p: dict) -> Comb002ImpulseParams:
    return Comb002ImpulseParams(
        stpmt_smooth_h=p["smooth_h"], stpmt_smooth_b=p["smooth_b"],
        stpmt_distance_max_h=p["dist_max_h"], stpmt_distance_max_l=p["dist_max_l"],
        horaire_allowed_hours_utc=p["horaire_hours"],
        volatility_atr_min=p["atr_min"], volatility_atr_max=p["atr_max"],
        scalping_target_quality=2,
        scalping_target_recent_volat=2,
        scalping_target_ref_volat=20,
        scalping_target_coef_volat=p["scalp_coef"],
        timescan_bars=p["timescan"],
        superstop_quality=p["superstop_quality"],
        superstop_coef_volat=p["superstop_coef_volat"],
    )


def main():
    parser = argparse.ArgumentParser(description="V2 Phase C Hold-out Validator")
    parser.add_argument("--final", type=Path, default=Path("COMB002_V2_FINAL_PARAMS.json"))
    parser.add_argument("--data-dir", type=Path, default=Path("."))
    parser.add_argument("--holdout-suffix", type=str, default="phase_C")
    parser.add_argument("--drift-alert", type=float, default=0.15)
    parser.add_argument("--regime-window", type=int, default=500)
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    if not args.final.exists():
        print(f"[ERROR] {args.final} not found.")
        sys.exit(1)

    with open(args.final) as fh:
        final = json.load(fh)

    print(f"\n=== V2 Hold-out Validator ===")
    print(f"Drift alert: {args.drift_alert*100:.0f}%\n")

    results = []
    alerts = []

    for key, entry in final["entries"].items():
        asset, tf = entry.get("asset"), entry.get("timeframe")
        if not asset or not tf:
            continue

        hfile = args.data_dir / f"{asset}_{args.holdout_suffix}_{tf}.csv"
        if not hfile.exists():
            print(f"  [{key}] no holdout file → skip")
            continue

        holdout_rows = load_ohlc_csv(str(hfile))
        th_data = entry.get("atr_thresholds", {})
        thresholds = RegimeThresholds(atr_low=th_data.get("low", 0),
                                      atr_high=th_data.get("high", 0))

        for regime in REGIME_LABELS:
            rdata = entry.get("regimes", {}).get(regime, {})
            status = rdata.get("status", "NO_PARAMS")
            if status not in ("OK", "DEGRADED"):
                continue

            params_dict = rdata.get("params", {})
            if not params_dict:
                continue

            regime_rows = filter_rows_by_regime(holdout_rows, thresholds, regime,
                                                window_size=args.regime_window)
            if not regime_rows:
                results.append({
                    "asset": asset, "timeframe": tf, "regime": regime,
                    "status": status, "note": "no holdout rows in this regime",
                })
                continue

            params = build_params(params_dict)
            strategy = Comb002ImpulseStrategy(params)
            r = strategy.run(regime_rows)
            holdout_pf = round(r.profit_factor, 4)
            holdout_trades = len(r.trades)

            reported = rdata.get("native_score", {}).get("min_pf", 0)
            drift = None
            drift_str = "N/A"
            if reported and reported > 0:
                drift = (holdout_pf - reported) / reported
                drift_str = f"{drift*100:+.1f}%"
                if abs(drift) > args.drift_alert:
                    alerts.append(f"{asset}_{tf} {regime}: reported={reported:.3f} holdout={holdout_pf:.3f} drift={drift_str}")

            flag = "⚠️" if (drift is not None and abs(drift) > args.drift_alert) else "✅"
            print(f"  [{asset:<4} {tf:<4} {regime:<9}] {flag} holdout_pf={holdout_pf:.3f} "
                  f"(reported {reported:.3f}, drift {drift_str}, trades={holdout_trades})")

            results.append({
                "asset": asset, "timeframe": tf, "regime": regime,
                "status": status,
                "reported_min_pf": reported,
                "holdout_pf": holdout_pf,
                "holdout_trades": holdout_trades,
                "drift_pct": round(drift*100, 2) if drift is not None else None,
                "drift_alert": (drift is not None and abs(drift) > args.drift_alert),
            })

    csv_file = args.out_dir / "COMB002_V2_holdout_results.csv"
    fields = ["asset", "timeframe", "regime", "status",
              "reported_min_pf", "holdout_pf", "holdout_trades",
              "drift_pct", "drift_alert", "note"]
    with open(csv_file, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    print(f"\n[OK] {csv_file}")

    md = [
        f"# COMB_002 V2 — Hold-out (Phase C) Report",
        f"",
        f"- **Fecha:** {date.today().strftime('%Y-%m-%d')}",
        f"- **Drift threshold:** {args.drift_alert*100:.0f}%",
        f"- **Alertas:** {len(alerts)}",
        f"",
    ]
    if alerts:
        md += ["## ⚠️ Alertas de drift", ""]
        md += [f"- {a}" for a in alerts]
    else:
        md += ["## ✅ Sin alertas", "",
               "_Todos los regímenes OK/DEGRADED reproducen dentro del threshold._"]
    md.append("")
    md += ["## Tabla completa", "",
           "| Asset | TF | Régimen | Status | Reported min_PF | Holdout PF | Drift% | Trades |",
           "|-------|-----|---------|--------|-----------------|------------|--------|--------|"]
    for r in results:
        md.append(
            f"| {r.get('asset')} | {r.get('timeframe')} | {r.get('regime')} | "
            f"{r.get('status')} | {r.get('reported_min_pf', 'N/A')} | "
            f"{r.get('holdout_pf', 'N/A')} | {r.get('drift_pct', 'N/A')} | "
            f"{r.get('holdout_trades', 'N/A')} |"
        )

    md_file = args.out_dir / "COMB002_V2_holdout_report.md"
    md_file.write_text("\n".join(md), encoding="utf-8")
    print(f"[OK] {md_file}")


if __name__ == "__main__":
    main()
