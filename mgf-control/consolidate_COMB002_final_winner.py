"""
COMB_002_IMPULSE — Consolidador final (Cross vs Sequential)

Para cada (ASSET, TIMEFRAME) compara:
  - Sequential master : COMB002_phase4_{ASSET}_{TF}_best_params.json
  - Cross validation  : COMB002_phase5_{ASSET}_{TF}_best_params.json

Decide el ganador con criterio multicapa:
  1. Ambos deben tener robustness_pass (Rob >= 0.80). Si solo uno pasa → ese gana.
  2. Ambos deben tener min_trades_pass (Phase A >= 30 trades). Si solo uno pasa → ese gana.
  3. Si ambos pasan filtros: elige el de mayor robustness.
  4. Tie-breaker (delta < 0.05): prefiere sequential (más simple, menos riesgo de overfit).

Genera:
  - COMB002_FINAL_PARAMS.json   : 12 entradas (4 assets x 3 TFs) con params ganadores
  - COMB002_FINAL_decisions.csv : auditoría de decisiones (qué ganó y por qué)

Uso:
  python3 consolidate_COMB002_final_winner.py
  python3 consolidate_COMB002_final_winner.py --output-dir ./final/
"""

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

ASSETS     = ["ES", "MNQ", "YM", "FDAX"]
TIMEFRAMES = ["5m", "10m", "15m"]

ROBUSTNESS_THRESHOLD = 0.80
MIN_TRADES           = 30
TIE_DELTA            = 0.05  # Si |rob_cross - rob_seq| < TIE_DELTA → empate

# Parámetros que definen la estrategia completa
STRATEGY_PARAMS = [
    "stpmt_smooth_h", "stpmt_smooth_b",
    "stpmt_distance_max_h", "stpmt_distance_max_l",
    "horaire_label", "horaire_allowed_hours_utc",
    "volatility_label", "volatility_atr_min", "volatility_atr_max",
    "scalping_target_coef_volat", "timescan_bars",
    "superstop_quality", "superstop_coef_volat",
]


def load_json_safe(path: Path):
    if not path.exists():
        return None
    try:
        with open(path) as fh:
            return json.load(fh)
    except json.JSONDecodeError:
        return None


def passes_filters(params: dict) -> tuple[bool, bool]:
    """Returns (rob_pass, trades_pass)."""
    if params is None:
        return (False, False)
    rob_pass = params.get("robustness_pass", False)
    trades_pass = params.get("min_trades_pass", False)
    # Fallback si los flags no están presentes
    if "robustness" in params and not rob_pass:
        rob_pass = params["robustness"] >= ROBUSTNESS_THRESHOLD
    if "phase_a_trades" in params and not trades_pass:
        trades_pass = params["phase_a_trades"] >= MIN_TRADES
    return (rob_pass, trades_pass)


def decide_winner(seq: dict, cross: dict) -> tuple[str, str]:
    """
    Decide ganador. Returns (winner: "sequential"|"cross"|"none", reason).
    """
    seq_rob_ok, seq_tr_ok = passes_filters(seq)
    crs_rob_ok, crs_tr_ok = passes_filters(cross)

    seq_ok = seq is not None and seq_rob_ok and seq_tr_ok
    crs_ok = cross is not None and crs_rob_ok and crs_tr_ok

    # Ninguno pasa → reporta el mejor disponible para informar
    if not seq_ok and not crs_ok:
        if seq is None and cross is None:
            return ("none", "no params available")
        seq_rob = seq.get("robustness", 0) if seq else 0
        crs_rob = cross.get("robustness", 0) if cross else 0
        if seq_rob >= crs_rob and seq is not None:
            return ("sequential", f"neither passes filters, sequential has higher rob ({seq_rob:.4f} vs {crs_rob:.4f})")
        elif cross is not None:
            return ("cross", f"neither passes filters, cross has higher rob ({crs_rob:.4f} vs {seq_rob:.4f})")
        return ("sequential", "neither passes, no cross data")

    # Solo uno pasa → ese gana
    if seq_ok and not crs_ok:
        return ("sequential", "only sequential passes all filters")
    if crs_ok and not seq_ok:
        return ("cross", "only cross passes all filters")

    # Ambos pasan → compara robustness
    seq_rob = seq["robustness"]
    crs_rob = cross["robustness"]
    delta = crs_rob - seq_rob

    if abs(delta) < TIE_DELTA:
        return ("sequential", f"tie (|delta|={abs(delta):.4f} < {TIE_DELTA}), prefer sequential (Occam)")

    if crs_rob > seq_rob:
        return ("cross", f"cross wins by {delta:+.4f} robustness")
    return ("sequential", f"sequential wins by {-delta:+.4f} robustness")


def build_final_entry(asset: str, tf: str, winner: str, reason: str,
                      seq: dict, cross: dict) -> dict:
    source = seq if winner == "sequential" else cross
    if source is None:
        return {
            "asset": asset, "timeframe": tf,
            "winner_approach": winner, "decision_reason": reason,
            "status": "NO_PARAMS",
        }

    entry = {
        "asset":            asset,
        "timeframe":        tf,
        "winner_approach":  winner,          # "sequential" | "cross"
        "decision_reason":  reason,
        "optimization_id":  source.get("optimization_id", "N/A"),
        "robustness":       source.get("robustness", 0),
        "phase_a_pf":       source.get("phase_a_pf", 0),
        "phase_b_pf":       source.get("phase_b_pf", 0),
        "phase_a_trades":   source.get("phase_a_trades", 0),
        "phase_b_trades":   source.get("phase_b_trades", 0),
        "robustness_pass":  source.get("robustness_pass", False),
        "min_trades_pass":  source.get("min_trades_pass", False),
        "status":           "OK" if (source.get("robustness_pass") and source.get("min_trades_pass")) else "DEGRADED",
    }
    for p in STRATEGY_PARAMS:
        if p in source:
            entry[p] = source[p]

    # Snapshot comparativo
    entry["comparison"] = {
        "sequential_rob":  seq["robustness"]   if seq   else None,
        "cross_rob":       cross["robustness"] if cross else None,
        "delta":           round((cross["robustness"] if cross else 0) - (seq["robustness"] if seq else 0), 4)
                           if (seq and cross) else None,
    }
    return entry


def main():
    parser = argparse.ArgumentParser(
        description="COMB_002 IMPULSE — Consolida Phase 4 (sequential) vs Phase 5 (cross) → FINAL_PARAMS"
    )
    parser.add_argument("--input-dir",  type=Path, default=Path("."),
                        help="Directorio con los JSONs phase4/phase5 (default: actual)")
    parser.add_argument("--output-dir", type=Path, default=Path("."),
                        help="Directorio de salida (default: actual)")
    args = parser.parse_args()

    in_dir  = args.input_dir.resolve()
    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*80}")
    print(f"COMB_002 IMPULSE — Final Consolidator (Sequential vs Cross)")
    print(f"{'='*80}")
    print(f"Input dir : {in_dir}")
    print(f"Output dir: {out_dir}\n")

    final_params = {
        "strategy":           "COMB_002_IMPULSE",
        "consolidation_date": date.today().strftime("%Y-%m-%d"),
        "method":             "sequential_vs_cross_validation",
        "thresholds": {
            "robustness_min": ROBUSTNESS_THRESHOLD,
            "trades_min":     MIN_TRADES,
            "tie_delta":      TIE_DELTA,
        },
        "entries": {},
    }

    decisions = []
    summary_counts = {"sequential": 0, "cross": 0, "none": 0, "ok": 0, "degraded": 0, "missing": 0}

    for asset in ASSETS:
        for tf in TIMEFRAMES:
            seq_file  = in_dir / f"COMB002_phase4_{asset}_{tf}_best_params.json"
            cross_file = in_dir / f"COMB002_phase5_{asset}_{tf}_best_params.json"
            seq   = load_json_safe(seq_file)
            cross = load_json_safe(cross_file)

            winner, reason = decide_winner(seq, cross)
            summary_counts[winner] = summary_counts.get(winner, 0) + 1

            entry = build_final_entry(asset, tf, winner, reason, seq, cross)
            final_params["entries"][f"{asset}_{tf}"] = entry

            status = entry.get("status", "NO_PARAMS")
            if status == "OK":
                summary_counts["ok"] += 1
            elif status == "DEGRADED":
                summary_counts["degraded"] += 1
            else:
                summary_counts["missing"] += 1

            rob_str = f"{entry.get('robustness', 0):.4f}" if entry.get("robustness") is not None else "N/A"
            print(f"  [{asset:<4} {tf:<4}] winner={winner:<10} rob={rob_str} status={status} | {reason}")

            decisions.append({
                "asset":          asset,
                "timeframe":      tf,
                "winner":         winner,
                "reason":         reason,
                "sequential_rob": seq["robustness"]   if seq   else None,
                "cross_rob":      cross["robustness"] if cross else None,
                "delta":          entry.get("comparison", {}).get("delta"),
                "final_rob":      entry.get("robustness"),
                "final_pf_a":     entry.get("phase_a_pf"),
                "final_pf_b":     entry.get("phase_b_pf"),
                "final_trades_a": entry.get("phase_a_trades"),
                "final_trades_b": entry.get("phase_b_trades"),
                "status":         status,
            })

    # Guardar FINAL_PARAMS
    final_file = out_dir / "COMB002_FINAL_PARAMS.json"
    with open(final_file, "w") as fh:
        json.dump(final_params, fh, indent=2)
    print(f"\n[OK] {final_file}")

    # Guardar CSV auditoría
    csv_file = out_dir / "COMB002_FINAL_decisions.csv"
    fields = ["asset", "timeframe", "winner", "reason",
              "sequential_rob", "cross_rob", "delta",
              "final_rob", "final_pf_a", "final_pf_b",
              "final_trades_a", "final_trades_b", "status"]
    with open(csv_file, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(decisions)
    print(f"[OK] {csv_file}")

    # Resumen
    print(f"\n{'='*80}")
    print(f"SUMMARY:")
    print(f"  Winners: sequential={summary_counts['sequential']} | cross={summary_counts['cross']} | none={summary_counts['none']}")
    print(f"  Status : OK={summary_counts['ok']} | DEGRADED={summary_counts['degraded']} | MISSING={summary_counts['missing']}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
