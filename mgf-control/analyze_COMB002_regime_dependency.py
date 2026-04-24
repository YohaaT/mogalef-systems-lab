"""
COMB_002_IMPULSE — Análisis de Dependencia de Régimen

Objetivo: Detectar si los FINAL_PARAMS ganadores funcionan por RÉGIMEN DE MERCADO
(ej: bien en 2024-03 pero mal en 2023), no por ventaja estructural robusta.

Metodología:
  1. Divide Phase A (60%) en 3 sub-períodos iguales (T1, T2, T3)
  2. Corre los FINAL_PARAMS en cada T1, T2, T3, y Phase B
  3. Compara PF y Trades → identifica saltos > 50%
  4. Flags "RÉGIMEN DEPENDIENTE" si hay inconsistencia
  5. Propone re-optimización con criterio de consistencia multi-período

Salida:
  - COMB002_REGIME_ANALYSIS.csv : PF por período (A1/A2/A3/B)
  - COMB002_REGIME_FLAGS.csv    : combos con dependencia de régimen
  - COMB002_REGIME_REPORT.md    : recomendaciones

Uso:
  python3 analyze_COMB002_regime_dependency.py
  python3 analyze_COMB002_regime_dependency.py --final COMB002_FINAL_PARAMS.json
"""

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

_here = Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))

from COMB_002_IMPULSE_V1 import Comb002ImpulseStrategy, Comb002ImpulseParams, load_ohlc_csv

ASSETS     = ["ES", "MNQ", "YM", "FDAX"]
TIMEFRAMES = ["5m", "10m", "15m"]

PF_CONSISTENCY_THRESHOLD = 0.50  # Flag si delta > 50%
MIN_TRADES_SUBPERIOD = 10


def split_phase_a_into_thirds(rows: list) -> Tuple[list, list, list]:
    """Divide Phase A en 3 sub-períodos de igual tamaño."""
    third = len(rows) // 3
    a1 = rows[:third]
    a2 = rows[third:2*third]
    a3 = rows[2*third:]
    return a1, a2, a3


def build_params(entry: dict) -> Comb002ImpulseParams:
    """Construir params desde entry JSON."""
    return Comb002ImpulseParams(
        stpmt_smooth_h=entry["stpmt_smooth_h"],
        stpmt_smooth_b=entry["stpmt_smooth_b"],
        stpmt_distance_max_h=entry["stpmt_distance_max_h"],
        stpmt_distance_max_l=entry["stpmt_distance_max_l"],
        horaire_allowed_hours_utc=entry.get("horaire_allowed_hours_utc", list(range(24))),
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


def run_backtest(strategy: Comb002ImpulseStrategy, rows: list) -> dict:
    """Ejecutar backtest y retornar métricas."""
    if not rows:
        return {"pf": 0.0, "wr": 0.0, "trades": 0, "equity": 0.0}
    result = strategy.run(rows)
    return {
        "pf": round(result.profit_factor, 4),
        "wr": round(result.win_rate, 4),
        "trades": len(result.trades),
        "equity": round(result.equity_points, 2),
    }


def analyze_regime_dependency(entry: dict, asset: str, tf: str,
                               phase_a_rows: list, phase_b_rows: list) -> dict:
    """Analizar si params dependen del régimen."""

    a1, a2, a3 = split_phase_a_into_thirds(phase_a_rows)

    params = build_params(entry)
    strategy = Comb002ImpulseStrategy(params)

    # Corre en cada sub-período
    r_a1 = run_backtest(strategy, a1)
    r_a2 = run_backtest(strategy, a2)
    r_a3 = run_backtest(strategy, a3)
    r_b  = run_backtest(strategy, phase_b_rows)

    # Detecta inconsistencia
    pfs = [r_a1["pf"], r_a2["pf"], r_a3["pf"], r_b["pf"]]
    max_pf = max(pfs) if max(pfs) > 0 else 1
    min_pf = min(pfs) if min(pfs) > 0 else 0.1
    delta = (max_pf - min_pf) / min_pf if min_pf > 0 else 0

    # Flag régimen dependiente
    regime_flag = delta > PF_CONSISTENCY_THRESHOLD

    # Consistency score (menor es mejor)
    consistency = 1.0 - (delta / (delta + 1))

    return {
        "asset": asset,
        "timeframe": tf,
        "winner": entry.get("winner_approach", "N/A"),
        "overall_rob": entry.get("robustness", 0),
        "pf_a1": r_a1["pf"],
        "pf_a2": r_a2["pf"],
        "pf_a3": r_a3["pf"],
        "pf_b": r_b["pf"],
        "trades_a1": r_a1["trades"],
        "trades_a2": r_a2["trades"],
        "trades_a3": r_a3["trades"],
        "trades_b": r_b["trades"],
        "pf_max": round(max_pf, 4),
        "pf_min": round(min_pf, 4),
        "pf_delta_pct": round(delta * 100, 1),
        "regime_dependent": regime_flag,
        "consistency_score": round(consistency, 4),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Analiza dependencia de régimen en COMB_002 FINAL_PARAMS"
    )
    parser.add_argument("--final",     type=Path, default=Path("COMB002_FINAL_PARAMS.json"))
    parser.add_argument("--data-dir",  type=Path, default=Path("."))
    parser.add_argument("--out-dir",   type=Path, default=Path("."))
    args = parser.parse_args()

    if not args.final.exists():
        print(f"[ERROR] {args.final} not found.")
        sys.exit(1)

    with open(args.final) as fh:
        final = json.load(fh)

    entries = final.get("entries", {})

    print(f"\n{'='*80}")
    print(f"COMB_002 IMPULSE — Régimen Dependency Analysis")
    print(f"{'='*80}")
    print(f"FINAL_PARAMS: {args.final}")
    print(f"Threshold:    PF delta > {PF_CONSISTENCY_THRESHOLD*100:.0f}% → RÉGIMEN DEPENDIENTE\n")

    results = []
    regime_flags = []

    for asset in ASSETS:
        for tf in TIMEFRAMES:
            key = f"{asset}_{tf}"
            entry = entries.get(key)

            if not entry or entry.get("status") == "NO_PARAMS":
                print(f"  [{asset} {tf}] skipped — no params")
                continue

            phase_a_file = args.data_dir / f"{asset}_phase_A_{tf}.csv"
            phase_b_file = args.data_dir / f"{asset}_phase_B_{tf}.csv"

            if not phase_a_file.exists() or not phase_b_file.exists():
                print(f"  [{asset} {tf}] skipped — missing phase CSV")
                continue

            phase_a_rows = load_ohlc_csv(str(phase_a_file))
            phase_b_rows = load_ohlc_csv(str(phase_b_file))

            result = analyze_regime_dependency(entry, asset, tf, phase_a_rows, phase_b_rows)
            results.append(result)

            flag_icon = "🚨" if result["regime_dependent"] else "✅"
            print(f"  [{asset} {tf}] {flag_icon} consistency={result['consistency_score']:.3f} | "
                  f"PF: A1={result['pf_a1']:.2f} A2={result['pf_a2']:.2f} A3={result['pf_a3']:.2f} B={result['pf_b']:.2f} | "
                  f"Δ={result['pf_delta_pct']:.0f}%")

            if result["regime_dependent"]:
                regime_flags.append(result)

    # CSV: análisis completo
    fields = ["asset", "timeframe", "winner", "overall_rob",
              "pf_a1", "pf_a2", "pf_a3", "pf_b",
              "trades_a1", "trades_a2", "trades_a3", "trades_b",
              "pf_max", "pf_min", "pf_delta_pct",
              "regime_dependent", "consistency_score"]

    csv_file = args.out_dir / "COMB002_REGIME_ANALYSIS.csv"
    with open(csv_file, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)
    print(f"\n[OK] {csv_file}")

    # CSV: flags de régimen
    if regime_flags:
        flag_file = args.out_dir / "COMB002_REGIME_FLAGS.csv"
        with open(flag_file, "w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(regime_flags)
        print(f"[OK] {flag_file}")

    # MD report
    md = [
        f"# COMB_002 IMPULSE — Régimen Dependency Report",
        f"",
        f"- **Fecha análisis:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **Threshold:** PF delta > {PF_CONSISTENCY_THRESHOLD*100:.0f}%",
        f"- **Régimen dependientes:** {len(regime_flags)}/12",
        f"",
    ]

    if regime_flags:
        md += [
            "## 🚨 Combos con Dependencia de Régimen",
            "",
            "| Asset | TF | PF_A1 | PF_A2 | PF_A3 | PF_B | Δ% | Patrón |",
            "|-------|-----|-------|-------|-------|-------|-----|--------|",
        ]
        for r in regime_flags:
            pattern = ""
            if r["pf_a1"] < 0.5 and r["pf_b"] > 1.5:
                pattern = "Mal en A, excelente en B (pure recency)"
            elif r["pf_a1"] > r["pf_b"]:
                pattern = "Mejor en A antiguo (regime shift)"
            else:
                pattern = "Volatile across periods"

            md.append(
                f"| {r['asset']} | {r['timeframe']} | {r['pf_a1']:.2f} | {r['pf_a2']:.2f} | "
                f"{r['pf_a3']:.2f} | {r['pf_b']:.2f} | {r['pf_delta_pct']:.0f}% | {pattern} |"
            )
        md.append("")
    else:
        md += ["## ✅ Sin Dependencia de Régimen", "", "_Todos los params muestran consistencia en A1/A2/A3/B._", ""]

    md += [
        "## Recomendaciones",
        "",
        "### Para combos con 🚨 Régimen Dependencia:",
        "",
        "1. **NO deployar directamente en live** — esperan Phase C (datos post-Mar24) para validar",
        "2. **Re-optimizar con criterio de consistencia:**",
        "   - En lugar de max(PF_B), usar min(PF_A1, PF_A2, PF_A3, PF_B) ≥ 1.0",
        "   - Esto prioriza robustez multi-período sobre peak performance",
        "3. **Añadir filtro de régimen en Phase 2:**",
        "   - Volatility regime: low/medium/high (ATR percentiles)",
        "   - Trend vs Chop: RSI o ADX",
        "   - Optimizar params DISTINTOS por régimen",
        "",
        "### Para combos con ✅ Consistencia:",
        "",
        "- Candidatos principales para live deployment",
        "- Aún así, validar en Phase C antes de tamaño real",
        "",
    ]

    md_file = args.out_dir / "COMB002_REGIME_REPORT.md"
    md_file.write_text("\n".join(md), encoding="utf-8")
    print(f"[OK] {md_file}")

    print(f"\n{'='*80}")
    print(f"RESUMEN: {len(regime_flags)}/12 muestran dependencia de régimen")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
