"""
Phase 2 RE-OPTIMIZED (Mogalef-Strict)

Previous Phase 2 deviated from Mogalef PDF recommendations:
- Horaire: optimized to [12-16 UTC] instead of [8-16] + [19-21] UTC (Mogalef)
- Weekday: Phase 2d never executed (no Mon/Tue filter per Mogalef)

This corrected version follows Mogalef PDF strictly:
1. Phase 2a: Trend Filter (150 combos) — fully optional, can vary
2. Phase 2b: Horaire locked to Mogalef defaults, test small variants only
3. Phase 2c: Volatility (5 profiles)
4. Phase 2d: Weekday Filter (4 combos) ← REQUIRED per Mogalef
"""

MOGALEF_RECOMMENDATIONS = {
    "horaire": {
        "primary": "9h-17h CET",       # [8-16] UTC in winter
        "secondary": "20h-22h CET",    # [19-21] UTC in winter
        "combined": [8, 9, 10, 11, 12, 13, 14, 15, 16, 19, 20, 21],  # UTC combined
        "note": "IMPERATIVO - à garder"
    },
    "weekday": {
        "no_tuesday": True,   # MAXIMUM priority
        "no_monday": True,    # SECOND priority  
        "note": "À garder - elimina 1-2 días sin riesgo de sobreoptimización"
    },
    "volatility": {
        "use_atr_filter": True,
        "note": "Dobla trade medio, reduce 25% número de trades, aumenta regularidad"
    },
    "trend_filter": {
        "note": "Opcional para COMB_001, leve mejora"
    }
}

# Phase 2b Profiles - MOGALEF STRICT
PHASE_2B_PROFILES_MOGALEF = {
    "profile_1": {
        "name": "Mogalef Strict (9-17 + 20-22 CET)",
        "hours_utc": [8, 9, 10, 11, 12, 13, 14, 15, 16, 19, 20, 21],
        "description": "PDF recommendation exactly"
    },
    "profile_2": {
        "name": "EU Morning + US Session (8-17 CET)",
        "hours_utc": [7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
        "description": "Variant: morning extended"
    },
    "profile_3": {
        "name": "US Prime (10-17 + 20-22 CET)",
        "hours_utc": [9, 10, 11, 12, 13, 14, 15, 16, 19, 20, 21],
        "description": "Variant: core US hours only"
    }
    # Remove overly restrictive profiles like [12-15] UTC
}

# Phase 2d Profiles - MOGALEF WEEKDAY FILTER (REQUIRED)
PHASE_2D_PROFILES = {
    "all_days": [],
    "no_tuesday": [1],      # Skip Tuesday (0=Mon, 1=Tue...)
    "no_monday": [0],       # Skip Monday
    "no_monday_tuesday": [0, 1]  # Skip both
}

print("="*80)
print("PHASE 2 CORRECTED PLAN (Mogalef-Strict)")
print("="*80)
print("\nKey Changes from Previous Phase 2:")
print("  - Horaire locked to Mogalef [9-17 + 20-22 CET] as primary")
print("  - Only test variants around Mogalef default, not arbitrary ranges")
print("  - Phase 2d MUST execute: Weekday filter (no Mon/Tue)")
print("  - Volatility: keep as is (ATR filter is beneficial)")
print("\nExpected Timeline:")
print("  Phase 2a: 150 combos ~15-20 min")
print("  Phase 2b: 3 profiles (Mogalef-strict + 2 variants) ~5 min")
print("  Phase 2c: 5 profiles ~2 min")
print("  Phase 2d: 4 combos (weekday filter) ~2 min  <-- ADDED")
print("  Consolidate: ~1 min")
print("  Total Phase 2 corrected: ~25-30 min")
print("="*80)
