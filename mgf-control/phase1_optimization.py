"""Phase 1 Optimization: Signal Component (EL_STPMT_DIV)

Lock: Contexto, Exits, Stops at defaults
Vary: stpmt_smooth_h, stpmt_smooth_b, stpmt_distance_max_h, stpmt_distance_max_l
Test: Phase A, validate Phase B
Output: Optimization log + best params
"""

import csv
import json
from pathlib import Path
from COMB_001_TREND_V1 import Comb001TrendStrategy, Comb001TrendParams, load_ohlc_csv

# Load data
print("Loading Phase A and Phase B data...")
phase_a_rows = load_ohlc_csv("YM_phase_A_clean.csv")
phase_b_rows = load_ohlc_csv("YM_phase_B_clean.csv")
print(f"Phase A: {len(phase_a_rows)} rows")
print(f"Phase B: {len(phase_b_rows)} rows")

# Parameter ranges
smooth_h_range = [1, 2, 3, 4, 5]
smooth_b_range = [1, 2, 3, 4, 5]
distance_max_h_range = [50, 100, 150, 200, 300]
distance_max_l_range = [50, 100, 150, 200, 300]

total_combos = len(smooth_h_range) * len(smooth_b_range) * len(distance_max_h_range) * len(distance_max_l_range)
print(f"\nTotal combos to test: {total_combos}")

# Storage for results
results = []
best_robustness = 0
best_params = None
combo_num = 0

# Test all combinations
for smooth_h in smooth_h_range:
    for smooth_b in smooth_b_range:
        for dist_max_h in distance_max_h_range:
            for dist_max_l in distance_max_l_range:
                combo_num += 1

                # Create params (lock other components to defaults)
                params = Comb001TrendParams(
                    # Signal (VARIED)
                    stpmt_smooth_h=smooth_h,
                    stpmt_smooth_b=smooth_b,
                    stpmt_distance_max_h=dist_max_h,
                    stpmt_distance_max_l=dist_max_l,
                    # Contexto (DEFAULT)
                    trend_r1=1,
                    trend_r2=90,
                    trend_r3=150,
                    horaire_allowed_hours_utc=list(range(9, 16)),
                    volatility_atr_min=0.0,
                    volatility_atr_max=500.0,
                    # Exits (DEFAULT)
                    target_atr_multiplier=10.0,
                    timescan_bars=30,
                    # Stops (DEFAULT)
                    stop_intelligent_quality=2,
                    stop_intelligent_recent_volat=2,
                    stop_intelligent_ref_volat=20,
                    stop_intelligent_coef_volat=5.0,
                )

                # Run Phase A
                strategy = Comb001TrendStrategy(params)
                result_a = strategy.run(phase_a_rows)

                # Run Phase B
                result_b = strategy.run(phase_b_rows)

                # Calculate robustness
                robustness = result_b.profit_factor / result_a.profit_factor if result_a.profit_factor > 0 else 0

                # Store result
                results.append({
                    "combo": combo_num,
                    "smooth_h": smooth_h,
                    "smooth_b": smooth_b,
                    "dist_max_h": dist_max_h,
                    "dist_max_l": dist_max_l,
                    "phase_a_pf": round(result_a.profit_factor, 4),
                    "phase_a_wr": round(result_a.win_rate, 4),
                    "phase_a_trades": len(result_a.trades),
                    "phase_a_equity": round(result_a.equity_points, 2),
                    "phase_b_pf": round(result_b.profit_factor, 4),
                    "phase_b_wr": round(result_b.win_rate, 4),
                    "phase_b_trades": len(result_b.trades),
                    "phase_b_equity": round(result_b.equity_points, 2),
                    "robustness": round(robustness, 4),
                })

                # Track best
                if robustness > best_robustness:
                    best_robustness = robustness
                    best_params = params
                    print(f"[{combo_num}/{total_combos}] NEW BEST: smooth_h={smooth_h}, smooth_b={smooth_b}, dist={dist_max_h}/{dist_max_l} -> Robustness={robustness:.4f}")

                # Progress every 100 combos
                if combo_num % 100 == 0:
                    print(f"Progress: {combo_num}/{total_combos}")

# Sort by robustness
results.sort(key=lambda x: x["robustness"], reverse=True)

# Export full log
with open("phase1_optimization_full_log.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

print(f"\n[OK] phase1_optimization_full_log.csv")

# Export top 10
top_10 = results[:10]
with open("phase1_optimization_top10.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=top_10[0].keys())
    writer.writeheader()
    writer.writerows(top_10)

print(f"[OK] phase1_optimization_top10.csv")

# Print summary
print("\n" + "="*80)
print("PHASE 1 OPTIMIZATION SUMMARY")
print("="*80)
print(f"\nTop 10 Combos (sorted by Robustness):\n")
print(f"{'Rank':<5} {'smooth_h':<10} {'smooth_b':<10} {'dist_h':<8} {'dist_l':<8} {'Phase A PF':<12} {'Phase B PF':<12} {'Robustness':<12}")
print("-" * 80)

for i, combo in enumerate(top_10, 1):
    print(f"{i:<5} {combo['smooth_h']:<10} {combo['smooth_b']:<10} {combo['dist_max_h']:<8} {combo['dist_max_l']:<8} {combo['phase_a_pf']:<12} {combo['phase_b_pf']:<12} {combo['robustness']:<12.4f}")

print("\n" + "="*80)
print("BEST COMBO SELECTED:")
print("="*80)
print(f"smooth_h: {best_params.stpmt_smooth_h}")
print(f"smooth_b: {best_params.stpmt_smooth_b}")
print(f"distance_max_h: {best_params.stpmt_distance_max_h}")
print(f"distance_max_l: {best_params.stpmt_distance_max_l}")
print(f"Robustness: {best_robustness:.4f}")

# Save best params
best_params_dict = {
    "stpmt_smooth_h": best_params.stpmt_smooth_h,
    "stpmt_smooth_b": best_params.stpmt_smooth_b,
    "stpmt_distance_max_h": best_params.stpmt_distance_max_h,
    "stpmt_distance_max_l": best_params.stpmt_distance_max_l,
    "robustness": best_robustness,
}

with open("phase1_best_params.json", "w") as f:
    json.dump(best_params_dict, f, indent=2)

print("\n[OK] phase1_best_params.json")
print("\nPhase 1 Optimization Complete!")
