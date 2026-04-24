"""Generate NT8 C# COMB001_TREND.cs from optimized parameters JSON

Reads COMB_001_TREND_5m_FINAL_PARAMS.json and generates updated COMB001_TREND.cs
with all optimized default parameters pre-configured.
"""

import json
import re
from pathlib import Path


TEMPLATE_DEFAULTS = """
        [Parameter("STPMT Smooth H", Order = 1, MinValue = 1, MaxValue = 10)]
        public int StpmtSmoothH { get; set; } = {stpmt_smooth_h};

        [Parameter("STPMT Smooth B", Order = 2, MinValue = 1, MaxValue = 10)]
        public int StpmtSmoothB { get; set; } = {stpmt_smooth_b};

        [Parameter("STPMT Distance Max H", Order = 3, MinValue = 10, MaxValue = 200)]
        public int StpmtDistanceMaxH { get; set; } = {stpmt_distance_max_h};

        [Parameter("STPMT Distance Max L", Order = 4, MinValue = 10, MaxValue = 200)]
        public int StpmtDistanceMaxL { get; set; } = {stpmt_distance_max_l};

        [Parameter("Trend R1", Order = 5, MinValue = 1, MaxValue = 10)]
        public int TrendR1 { get; set; } = {trend_r1};

        [Parameter("Trend R2", Order = 6, MinValue = 20, MaxValue = 200)]
        public int TrendR2 { get; set; } = {trend_r2};

        [Parameter("Trend R3", Order = 7, MinValue = 50, MaxValue = 500)]
        public int TrendR3 { get; set; } = {trend_r3};

        [Parameter("Horaire Start Hour UTC", Order = 8, MinValue = 0, MaxValue = 23)]
        public int HoraireStartHour { get; set; } = {horaire_start};

        [Parameter("Horaire End Hour UTC", Order = 9, MinValue = 0, MaxValue = 23)]
        public int HoraireEndHour { get; set; } = {horaire_end};

        [Parameter("Volatility ATR Min", Order = 10, MinValue = 0, MaxValue = 500)]
        public double VolatilityAtrMin { get; set; } = {atr_min};

        [Parameter("Volatility ATR Max", Order = 11, MinValue = 0, MaxValue = 500)]
        public double VolatilityAtrMax { get; set; } = {atr_max};

        [Parameter("Target ATR Multiplier", Order = 12, MinValue = 1, MaxValue = 20)]
        public double TargetAtrMultiplier { get; set; } = {target_atr};

        [Parameter("TimeStop Bars", Order = 13, MinValue = 5, MaxValue = 100)]
        public int TimescanBars { get; set; } = {timescan};

        [Parameter("Stop Intelligent Quality", Order = 14, MinValue = 1, MaxValue = 5)]
        public int StopIntQuality { get; set; } = {stop_quality};

        [Parameter("Stop Intelligent Recent Volatility", Order = 15, MinValue = 1, MaxValue = 5)]
        public int StopIntRecent { get; set; } = {stop_recent};

        [Parameter("Stop Intelligent Ref Volatility", Order = 16, MinValue = 5, MaxValue = 100)]
        public int StopIntRefVolat { get; set; } = {stop_ref};

        [Parameter("Stop Intelligent Coef Volatility", Order = 17, MinValue = 1, MaxValue = 10)]
        public double StopIntCoefVolat { get; set; } = {stop_coef};
"""


def generate_nt8():
    print("=" * 70)
    print("GENERATE NT8 COMB001_TREND.cs FROM OPTIMIZED PARAMETERS")
    print("=" * 70)

    # Load final parameters
    with open("COMB_001_TREND_5m_FINAL_PARAMS.json") as f:
        params = json.load(f)

    p = params["parameters"]

    # Determine horaire hours (pick first and last from list)
    hours = p["contexto"]["horaire"]["allowed_hours_utc"]
    horaire_start = min(hours) if hours else 9
    horaire_end = max(hours) if hours else 16

    # Build defaults string
    defaults = TEMPLATE_DEFAULTS.format(
        stpmt_smooth_h=p["signal"]["stpmt_smooth_h"],
        stpmt_smooth_b=p["signal"]["stpmt_smooth_b"],
        stpmt_distance_max_h=p["signal"]["stpmt_distance_max_h"],
        stpmt_distance_max_l=p["signal"]["stpmt_distance_max_l"],
        trend_r1=p["contexto"]["trend_filter"]["trend_r1"],
        trend_r2=p["contexto"]["trend_filter"]["trend_r2"],
        trend_r3=p["contexto"]["trend_filter"]["trend_r3"],
        horaire_start=horaire_start,
        horaire_end=horaire_end,
        atr_min=p["contexto"]["volatility"]["atr_min"],
        atr_max=p["contexto"]["volatility"]["atr_max"],
        target_atr=p["exits"]["target_atr_multiplier"],
        timescan=p["exits"]["timescan_bars"],
        stop_quality=p["stops"]["stop_intelligent_quality"],
        stop_recent=p["stops"]["stop_intelligent_recent_volat"],
        stop_ref=p["stops"]["stop_intelligent_ref_volat"],
        stop_coef=p["stops"]["stop_intelligent_coef_volat"],
    )

    print("\n[Generated Parameters]")
    print(f"  Signal: smooth_h={p['signal']['stpmt_smooth_h']}, "
          f"smooth_b={p['signal']['stpmt_smooth_b']}")
    print(f"  Trend: r1={p['contexto']['trend_filter']['trend_r1']}, "
          f"r2={p['contexto']['trend_filter']['trend_r2']}, "
          f"r3={p['contexto']['trend_filter']['trend_r3']}")
    print(f"  Horaire: {horaire_start}-{horaire_end} UTC")
    print(f"  Volatility: ATR {p['contexto']['volatility']['atr_min']}-"
          f"{p['contexto']['volatility']['atr_max']}")
    print(f"  Exits: target={p['exits']['target_atr_multiplier']} ATR, "
          f"timescan={p['exits']['timescan_bars']} bars")
    print(f"  Stops: quality={p['stops']['stop_intelligent_quality']}, "
          f"recent={p['stops']['stop_intelligent_recent_volat']}, "
          f"ref={p['stops']['stop_intelligent_ref_volat']}, "
          f"coef={p['stops']['stop_intelligent_coef_volat']}")

    # Read current COMB001_TREND.cs (if exists) and inject defaults
    cs_path = Path("../nt8-port/COMB001_TREND.cs")
    if cs_path.exists():
        with open(cs_path) as f:
            cs_content = f.read()

        # Find and replace parameter section (simplified — assumes template structure)
        # This is a basic replacement; a more robust version would parse C#
        print(f"\n[Updating] {cs_path}")
        print("  Note: Manual review recommended after generation")
        print("  Parameters marked with 'get; set; } = ' are updateable")

        # Generate a report file instead of modifying directly (safer)
        report_path = Path("COMB001_TREND_PARAMETER_UPDATES.txt")
        with open(report_path, "w") as f:
            f.write("# COMB001_TREND.cs Parameter Updates\n\n")
            f.write("Copy the following parameter declarations to replace the existing ones:\n\n")
            f.write(defaults)
            f.write("\n\n# Validation Metrics\n")
            f.write(f"Phase A PF: {params['validation']['phase_a_pf']:.4f}\n")
            f.write(f"Phase B PF: {params['validation']['phase_b_pf']:.4f}\n")
            f.write(f"Robustness: {params['validation']['final_robustness']:.4f}\n")
        print(f"\n[OK] {report_path} — parameter updates ready for manual merge")
    else:
        print(f"\n[SKIP] {cs_path} not found")
        print("  Generate this file manually or run from correct directory")

    print("\n" + "=" * 70)
    print("NT8 Parameter generation complete")
    print("=" * 70)


if __name__ == "__main__":
    generate_nt8()
