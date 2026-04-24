"""
COMB_002_IMPULSE — Validación final en Hold-out / Re-ejecución sanity

Objetivo:
  1. Re-ejecutar los FINAL_PARAMS sobre Phase A + Phase B (sanity check — debe coincidir
     con las métricas reportadas; si no, hay bug o data corrupto).
  2. Si existe un archivo hold-out (ej: {ASSET}_phase_C_{TF}.csv con datos NO vistos),
     correr los FINAL_PARAMS ahí y reportar métricas out-of-sample reales.

Salida:
  - COMB002_FINAL_holdout_results.csv : métricas por combo (sanity vs holdout)
  - COMB002_FINAL_holdout_report.md   : resumen con flags si hay desviación > 10%

Uso:
  python3 validate_COMB002_FINAL_holdout.py
  python3 validate_COMB002_FINAL_holdout.py --holdout-suffix phase_C --deviation-alert 0.15
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

ASSETS     = ["ES", "MNQ", "YM", "FDAX"]
TIMEFRAMES = ["5m", "10m", "15m"]


def build_params(entry: dict) -> Comb002ImpulseParams:
    return Comb002ImpulseParams(
        stpmt_smooth_h=entry["stpmt_smooth_h"],
        stpmt_smooth_b=entry["stpmt_smooth_b"],
        stpmt_distance_max_h=entry["stpmt_distance_max_h"],
        stpmt_distance_max_l=entry["stpmt_distance_max_l"],
        horaire_allowed_hours_utc=entry["horaire_allowed_hours_utc"],
        volatility_atr_min=entry["volatility_atr_min"],
        volatility_atr_max=entry["volatility_atr_max"],
        scalping_target_coef_volat=entry["scalping_target_coef_volat"],
        timescan_bars=entry["timescan_bars"],
        superstop_quality=entry["superstop_quality"],
        superstop_coef_volat=entry["superstop_coef_volat"],
        scalping_target_quality=2,
        scalping_target_recent_volat=2,
        scalping_target_ref_volat=20,
    )


def run_backtest(strategy: Comb002ImpulseStrategy, rows):
    result = strategy.run(rows)
    return {
        "pf":     round(result.profit_factor, 4),
        "wr":     round(result.win_rate, 4),
        "trades": len(result.trades),
        "equity": round(result.equity_points, 2),
    }


def pct_diff(a, b):
    if a is None or b is None or a == 0:
        return None
    return round((b - a) / abs(a), 4)


def main():
    parser = argparse.ArgumentParser(description="Sanity + Hold-out re-ejecución de FINAL_PARAMS")
    parser.add_argument("--final",           type=Path, default=Path("COMB002_FINAL_PARAMS.json"))
    parser.add_argument("--data-dir",        type=Path, default=Path("."),
                        help="Directorio con CSVs {ASSET}_phase_A_{TF}.csv etc.")
    parser.add_argument("--holdout-suffix",  type=str,  default="phase_C",
                        help="Sufijo para data hold-out: {ASSET}_{suffix}_{TF}.csv (default: phase_C)")
    parser.add_argument("--deviation-alert", type=float, default=0.10,
                        help="Alerta si |sanity_pf - reported_pf| / reported_pf > este valor (default: 0.10)")
    parser.add_argument("--out-dir",         type=Path, default=Path("."))
    args = parser.parse_args()

    if not args.final.exists():
        print(f"[ERROR] {args.final} not found. Corre antes: consolidate_COMB002_final_winner.py")
        sys.exit(1)

    with open(args.final) as fh:
        final = json.load(fh)

    entries = final.get("entries", {})
    print(f"\n{'='*80}")
    print(f"COMB_002 IMPULSE — Hold-out / Sanity Validator")
    print(f"{'='*80}")
    print(f"FINAL_PARAMS : {args.final}")
    print(f"Data dir     : {args.data_dir.resolve()}")
    print(f"Hold-out tag : {args.holdout_suffix}")
    print(f"Alert thresh : {args.deviation_alert*100:.0f}% deviation\n")

    rows_results = []
    alerts = []

    for asset in ASSETS:
        for tf in TIMEFRAMES:
            key = f"{asset}_{tf}"
            entry = entries.get(key)
            if entry is None or entry.get("status") == "NO_PARAMS":
                print(f"  [{asset:<4} {tf:<4}] skipped — no FINAL params")
                rows_results.append({"asset": asset, "timeframe": tf, "note": "no_params"})
                continue

            # Verifica que el entry tenga todos los campos necesarios
            required = ["stpmt_smooth_h", "horaire_allowed_hours_utc",
                        "volatility_atr_min", "scalping_target_coef_volat",
                        "superstop_quality"]
            if not all(k in entry for k in required):
                print(f"  [{asset:<4} {tf:<4}] skipped — entry incomplete")
                rows_results.append({"asset": asset, "timeframe": tf, "note": "incomplete"})
                continue

            params = build_params(entry)
            strategy = Comb002ImpulseStrategy(params)

            phase_a_file = args.data_dir / f"{asset}_phase_A_{tf}.csv"
            phase_b_file = args.data_dir / f"{asset}_phase_B_{tf}.csv"
            holdout_file = args.data_dir / f"{asset}_{args.holdout_suffix}_{tf}.csv"

            row = {
                "asset":          asset,
                "timeframe":      tf,
                "winner":         entry.get("winner_approach"),
                "reported_rob":   entry.get("robustness"),
                "reported_pf_a":  entry.get("phase_a_pf"),
                "reported_pf_b":  entry.get("phase_b_pf"),
                "reported_tr_a":  entry.get("phase_a_trades"),
                "reported_tr_b":  entry.get("phase_b_trades"),
            }

            # Sanity re-run
            if phase_a_file.exists() and phase_b_file.exists():
                a_rows = load_ohlc_csv(str(phase_a_file))
                b_rows = load_ohlc_csv(str(phase_b_file))
                sa = run_backtest(strategy, a_rows)
                sb = run_backtest(strategy, b_rows)
                sanity_rob = round(sb["pf"] / sa["pf"], 4) if sa["pf"] > 0 else 0
                row.update({
                    "sanity_pf_a":  sa["pf"],
                    "sanity_pf_b":  sb["pf"],
                    "sanity_tr_a":  sa["trades"],
                    "sanity_tr_b":  sb["trades"],
                    "sanity_rob":   sanity_rob,
                    "pf_a_drift":   pct_diff(entry.get("phase_a_pf"), sa["pf"]),
                    "pf_b_drift":   pct_diff(entry.get("phase_b_pf"), sb["pf"]),
                })
                drift_a = row["pf_a_drift"]
                drift_b = row["pf_b_drift"]
                flag = ""
                if (drift_a is not None and abs(drift_a) > args.deviation_alert) or \
                   (drift_b is not None and abs(drift_b) > args.deviation_alert):
                    flag = " ⚠️ DRIFT"
                    alerts.append(f"{key}: PF_A drift={drift_a} · PF_B drift={drift_b}")
                print(f"  [{asset:<4} {tf:<4}] sanity: PF_A={sa['pf']:.4f} (reported {entry.get('phase_a_pf')}) "
                      f"PF_B={sb['pf']:.4f} (reported {entry.get('phase_b_pf')}) "
                      f"Rob={sanity_rob:.4f}{flag}")
            else:
                row.update({"sanity_note": "missing_phase_AB_csv"})
                print(f"  [{asset:<4} {tf:<4}] sanity: skipped (no phase_A/B csv)")

            # Hold-out (phase C)
            if holdout_file.exists():
                h_rows = load_ohlc_csv(str(holdout_file))
                sh = run_backtest(strategy, h_rows)
                row.update({
                    "holdout_pf":     sh["pf"],
                    "holdout_wr":     sh["wr"],
                    "holdout_trades": sh["trades"],
                    "holdout_equity": sh["equity"],
                    "holdout_rob_vs_a": round(sh["pf"] / row.get("reported_pf_a"), 4)
                                         if row.get("reported_pf_a", 0) > 0 else None,
                })
                print(f"       holdout : PF={sh['pf']:.4f} WR={sh['wr']:.4f} Trades={sh['trades']}")
            else:
                row["holdout_note"] = "missing_phase_C_csv"

            rows_results.append(row)

    # CSV
    fields = ["asset", "timeframe", "winner",
              "reported_rob", "reported_pf_a", "reported_pf_b", "reported_tr_a", "reported_tr_b",
              "sanity_pf_a", "sanity_pf_b", "sanity_tr_a", "sanity_tr_b", "sanity_rob",
              "pf_a_drift", "pf_b_drift",
              "holdout_pf", "holdout_wr", "holdout_trades", "holdout_equity", "holdout_rob_vs_a",
              "sanity_note", "holdout_note", "note"]

    csv_file = args.out_dir / "COMB002_FINAL_holdout_results.csv"
    with open(csv_file, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows_results)
    print(f"\n[OK] {csv_file}")

    # MD
    md = [
        f"# COMB_002 IMPULSE — Hold-out / Sanity Report",
        f"",
        f"- **Fecha:** {date.today().strftime('%Y-%m-%d')}",
        f"- **Alert threshold:** {args.deviation_alert*100:.0f}% PF deviation",
        f"- **Alertas totales:** {len(alerts)}",
        f"",
    ]
    if alerts:
        md += ["## ⚠️ Alertas de drift", ""]
        md += [f"- {a}" for a in alerts]
        md += [""]
    else:
        md += ["## ✅ Sin alertas de drift", "",
               "_Todas las re-ejecuciones reproducen las métricas reportadas dentro del threshold._", ""]

    md += ["## Resultados por combo", "",
           "| Asset | TF | Winner | Reported PF_B | Sanity PF_B | PF_B drift | Hold-out PF |",
           "|-------|-----|--------|---------------|-------------|------------|-------------|"]
    for r in rows_results:
        if not r.get("reported_pf_b"):
            continue
        drift = r.get("pf_b_drift")
        drift_str = f"{drift*100:+.1f}%" if drift is not None else "N/A"
        md.append(
            f"| {r['asset']} | {r['timeframe']} | {r.get('winner', 'N/A')} | "
            f"{r.get('reported_pf_b', 'N/A')} | {r.get('sanity_pf_b', 'N/A')} | "
            f"{drift_str} | {r.get('holdout_pf', 'N/A')} |"
        )
    md.append("")

    md_file = args.out_dir / "COMB002_FINAL_holdout_report.md"
    md_file.write_text("\n".join(md), encoding="utf-8")
    print(f"[OK] {md_file}")


if __name__ == "__main__":
    main()
