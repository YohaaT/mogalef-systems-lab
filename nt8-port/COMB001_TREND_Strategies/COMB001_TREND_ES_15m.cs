// =============================================================================
// Strategy : COMB001_TREND_ES_15m
// Asset    : ES (E-mini S&P 500 Futures)
// Timeframe: 15m bars
// Phase B PF: 2.81
// Generated : 2026-04-23
// Description:
//   Ports the Python COMB_001_TREND strategy to NinjaTrader 8.
//   Combines:
//     1. STPMT Divergence signal (EL_STPMT_DIV)
//     2. Mogalef Trend Filter V2  (always passes — matches Python blocked_cases=[])
//     3. ATR range filter
//     4. Horaire (UTC hour) filter
//     5. Weekday filter
//     6. Stop Intelligent trailing stop
//     7. Fixed ATR-multiple profit target
// =============================================================================

#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.Strategies;
#endregion

namespace NinjaTrader.NinjaScript.Strategies
{
    public class COMB001_TREND_ES_15m : Strategy
    {
        // =====================================================================
        // PARAMETERS
        // =====================================================================

        #region STPMT Parameters
        [NinjaScriptProperty]
        [Range(1, 50)]
        [Display(Name = "STPMT Smooth H", GroupName = "STPMT Divergence", Order = 1,
            Description = "Pivot smoothing window for STPMT highs")]
        public int StpmtSmoothH { get; set; }

        [NinjaScriptProperty]
        [Range(1, 50)]
        [Display(Name = "STPMT Smooth B", GroupName = "STPMT Divergence", Order = 2,
            Description = "Pivot smoothing window for STPMT lows")]
        public int StpmtSmoothB { get; set; }

        [NinjaScriptProperty]
        [Range(1, 200)]
        [Display(Name = "STPMT Dist Max H", GroupName = "STPMT Divergence", Order = 3,
            Description = "Max bars between bearish divergence pivots")]
        public int StpmtDistMaxH { get; set; }

        [NinjaScriptProperty]
        [Range(1, 200)]
        [Display(Name = "STPMT Dist Max L", GroupName = "STPMT Divergence", Order = 4,
            Description = "Max bars between bullish divergence pivots")]
        public int StpmtDistMaxL { get; set; }
        #endregion

        #region Trend Filter Parameters
        [NinjaScriptProperty]
        [Range(1, 500)]
        [Display(Name = "Trend R1", GroupName = "Mogalef Trend Filter", Order = 1,
            Description = "Repulse R1 period multiplier")]
        public int TrendR1 { get; set; }

        [NinjaScriptProperty]
        [Range(1, 500)]
        [Display(Name = "Trend R2", GroupName = "Mogalef Trend Filter", Order = 2,
            Description = "Repulse R2 period multiplier")]
        public int TrendR2 { get; set; }

        [NinjaScriptProperty]
        [Range(1, 500)]
        [Display(Name = "Trend R3", GroupName = "Mogalef Trend Filter", Order = 3,
            Description = "Repulse R3 period multiplier")]
        public int TrendR3 { get; set; }
        #endregion

        #region Session / Schedule Parameters
        [NinjaScriptProperty]
        [Display(Name = "Horaire Hours (UTC, comma-sep)", GroupName = "Session Filter", Order = 1,
            Description = "UTC hours during which entries are allowed, e.g. \"13,14,15,16\"")]
        public string HoraireHours { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Blocked Weekdays (Python 0=Mon)", GroupName = "Session Filter", Order = 2,
            Description = "Python-numbered weekdays to block entries, e.g. \"1\" blocks Tuesday")]
        public string BlockedWeekdays { get; set; }
        #endregion

        #region ATR Filter Parameters
        [NinjaScriptProperty]
        [Range(0.0, 10000.0)]
        [Display(Name = "ATR Min", GroupName = "ATR Filter", Order = 1,
            Description = "Minimum ATR(14) value required for entry")]
        public double AtrMin { get; set; }

        [NinjaScriptProperty]
        [Range(0.0, 10000.0)]
        [Display(Name = "ATR Max", GroupName = "ATR Filter", Order = 2,
            Description = "Maximum ATR(14) value allowed for entry")]
        public double AtrMax { get; set; }
        #endregion

        #region Trade Management Parameters
        [NinjaScriptProperty]
        [Range(0.1, 50.0)]
        [Display(Name = "Target ATR Mult", GroupName = "Trade Management", Order = 1,
            Description = "Profit target as multiple of ATR at entry")]
        public double TargetAtrMult { get; set; }

        [NinjaScriptProperty]
        [Range(1, 500)]
        [Display(Name = "Time Stop Bars", GroupName = "Trade Management", Order = 2,
            Description = "Exit trade after this many bars regardless")]
        public int TimeScanBars { get; set; }

        [NinjaScriptProperty]
        [Range(1, 10)]
        [Display(Name = "Stop Quality", GroupName = "Stop Intelligent", Order = 1,
            Description = "Swing pivot quality: bars on each side to confirm swing")]
        public int StopQuality { get; set; }

        [NinjaScriptProperty]
        [Range(1, 50)]
        [Display(Name = "Stop Recent Volat", GroupName = "Stop Intelligent", Order = 2,
            Description = "Period for recent ATR in stop calculation")]
        public int StopRecentVolat { get; set; }

        [NinjaScriptProperty]
        [Range(1, 100)]
        [Display(Name = "Stop Ref Volat", GroupName = "Stop Intelligent", Order = 3,
            Description = "Period for reference ATR in stop calculation")]
        public int StopRefVolat { get; set; }

        
        [NinjaScriptProperty]
        [Range(1, 100)]
        [Display(Name = "Contracts", GroupName = "Trade Management", Order = 3,
            Description = "Number of contracts per trade")]
        public int Contracts { get; set; }
        [NinjaScriptProperty]
        [Range(0.1, 50.0)]
        [Display(Name = "Stop Coef Volat", GroupName = "Stop Intelligent", Order = 4,
            Description = "Volatility coefficient for stop space calculation")]
        public double StopCoefVolat { get; set; }
        #endregion

        // =====================================================================
        // PRIVATE STATE
        // =====================================================================

        // --- STPMTE composite stochastic series ---
        private Series<double> stok1S, stod1S;
        private Series<double> stok2S, stod2S;
        private Series<double> stok3S, stod3S;
        private Series<double> stok4S, stod4S;
        private Series<double> stpmteS;          // composite STPMTE value

        // --- True Range series (for Stop Intelligent) ---
        private Series<double> trS;              // True Range per bar
        private Series<double> trRecentS;        // SMA(TR, StopRecentVolat)
        private Series<double> trRefS;           // SMA(TR, StopRefVolat)

        // --- STPMT divergence state ---
        // Bearish (short) pivot state
        private double stpmt_last_h_indic  = double.NaN;  // STPMTE at last confirmed high pivot
        private double stpmt_last_h_price  = double.NaN;  // price high at last confirmed high pivot
        private int    stpmt_counter_h     = 0;            // bars since last high pivot
        private bool   stpmt_looking_h     = false;        // waiting for next high pivot

        // Bullish (long) pivot state
        private double stpmt_last_b_indic  = double.NaN;  // STPMTE at last confirmed low pivot
        private double stpmt_last_b_price  = double.NaN;  // price low at last confirmed low pivot
        private int    stpmt_counter_b     = 0;            // bars since last low pivot
        private bool   stpmt_looking_b     = false;        // waiting for next low pivot

        // --- Parsed filter lists ---
        private HashSet<int>         allowedUTCHours;
        private HashSet<DayOfWeek>   blockedDays;

        // --- Trade state ---
        private int    pose          = 0;      // signal: +1 long, -1 short, 0 none
        private double entryPx       = 0.0;
        private double targetPx      = 0.0;
        private double stopPx        = 0.0;
        private double signalLow     = 0.0;    // Low[0] at signal bar (long entry stop seed)
        private double signalHigh    = 0.0;    // High[0] at signal bar (short entry stop seed)
        private double atrAtEntry    = 0.0;
        private int    barsInTrade   = 0;
        private bool   inLong        = false;
        private bool   inShort       = false;

        // =====================================================================
        // OnStateChange
        // =====================================================================
        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name                         = "COMB001_TREND_ES_15m";
                Description                  = "COMB_001_TREND ported from Python — ES 5-minute";
                Calculate                    = Calculate.OnBarClose;
                EntriesPerDirection          = 1;
                EntryHandling                = EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy = true;
                ExitOnSessionCloseSeconds    = 30;
                BarsRequiredToTrade          = 600;
                IsUnmanaged                  = false;

                // Default parameter values for ES 5m
                StpmtSmoothH      = 5;
                StpmtSmoothB      = 5;
                StpmtDistMaxH     = 50;
                StpmtDistMaxL     = 25;
                TrendR1           = 1;
                TrendR2           = 50;
                TrendR3           = 250;
                HoraireHours      = "14,15,16,17,18,19,20,21,22";
                BlockedWeekdays   = "0,1";          // 0,1 blocked
                AtrMin            = 10;
                AtrMax            = 500;
                TargetAtrMult     = 7;
                TimeScanBars      = 25;
                StopQuality       = 3;
                StopRecentVolat   = 1;
                StopRefVolat      = 10;
                StopCoefVolat     = 5;
                Contracts         = 1;
            }
            else if (State == State.DataLoaded)
            {
                // Allocate custom series (must be done in DataLoaded)
                stok1S   = new Series<double>(this);
                stod1S   = new Series<double>(this);
                stok2S   = new Series<double>(this);
                stod2S   = new Series<double>(this);
                stok3S   = new Series<double>(this);
                stod3S   = new Series<double>(this);
                stok4S   = new Series<double>(this);
                stod4S   = new Series<double>(this);
                stpmteS  = new Series<double>(this);
                trS      = new Series<double>(this);
                trRecentS = new Series<double>(this);
                trRefS    = new Series<double>(this);

                // Parse filter parameter strings
                allowedUTCHours = ParseCommaListInt(HoraireHours);
                blockedDays     = ParseBlockedWeekdays(BlockedWeekdays);
            }
        }

        // =====================================================================
        // OnBarUpdate — main strategy logic, fires on bar close
        // =====================================================================
        protected override void OnBarUpdate()
        {
            // Need enough bars for all lookbacks
            if (CurrentBar < BarsRequiredToTrade)
                return;

            // ------------------------------------------------------------------
            // 1. Compute STPMTE composite stochastic
            // ------------------------------------------------------------------
            ComputeStpmte();

            // ------------------------------------------------------------------
            // 2. Compute True Range and its SMAs (for Stop Intelligent)
            // ------------------------------------------------------------------
            ComputeTrSeries();

            // ------------------------------------------------------------------
            // 3. Trade management — check exits first (priority order)
            // ------------------------------------------------------------------
            if (inLong || inShort)
            {
                barsInTrade++;

                // Update trailing stop each bar
                UpdateStopIntelligent();

                // Priority 1: Stop hit
                if (inLong && Low[0] <= stopPx)
                {
                    ExitLong("Stop", "Long");
                    ResetTradeState();
                    return;
                }
                if (inShort && High[0] >= stopPx)
                {
                    ExitShort("Stop", "Short");
                    ResetTradeState();
                    return;
                }

                // Priority 2: Target hit
                if (inLong && High[0] >= targetPx)
                {
                    ExitLong("Target", "Long");
                    ResetTradeState();
                    return;
                }
                if (inShort && Low[0] <= targetPx)
                {
                    ExitShort("Target", "Short");
                    ResetTradeState();
                    return;
                }

                // Priority 3: Opposite signal + filter pass
                int currentPose = ComputeStpmtPose();
                bool filterPass = ComputeTrendFilter() && IsHoraireAllowed() && IsWeekdayAllowed() && IsAtrAllowed();

                if (inLong && currentPose == -1 && filterPass)
                {
                    ExitLong("OppSignal", "Long");
                    ResetTradeState();
                    return;
                }
                if (inShort && currentPose == 1 && filterPass)
                {
                    ExitShort("OppSignal", "Short");
                    ResetTradeState();
                    return;
                }

                // Priority 4: Time stop
                if (barsInTrade >= TimeScanBars)
                {
                    if (inLong)  ExitLong("TimeStop", "Long");
                    if (inShort) ExitShort("TimeStop", "Short");
                    ResetTradeState();
                    return;
                }
            }
            else
            {
                // ------------------------------------------------------------------
                // 4. Entry logic — only when flat
                // ------------------------------------------------------------------
                pose = ComputeStpmtPose();

                if (pose != 0
                    && ComputeTrendFilter()
                    && IsHoraireAllowed()
                    && IsWeekdayAllowed()
                    && IsAtrAllowed())
                {
                    atrAtEntry = ATR(14)[0];

                    if (pose == 1)
                    {
                        signalLow  = Low[0];
                        signalHigh = High[0];
                        EnterLong(Contracts, "Long");
                    }
                    else if (pose == -1)
                    {
                        signalLow  = Low[0];
                        signalHigh = High[0];
                        EnterShort(Contracts, "Short");
                    }
                }
            }
        }

        // =====================================================================
        // OnExecutionUpdate — capture actual fill price to set targets / stops
        // =====================================================================
        protected override void OnExecutionUpdate(
            Execution execution, string executionId, double price, int quantity,
            MarketPosition marketPosition, string orderId, DateTime time)
        {
            if (execution.Order == null) return;

            // Long fill
            if (execution.Order.Name == "Long"
                && execution.Order.OrderAction == OrderAction.Buy
                && marketPosition == MarketPosition.Long)
            {
                entryPx  = execution.Price;
                targetPx = entryPx + TargetAtrMult * atrAtEntry;
                stopPx   = signalLow;          // initial stop = signal bar low
                inLong   = true;
                inShort  = false;
                barsInTrade = 0;
            }

            // Short fill
            if (execution.Order.Name == "Short"
                && execution.Order.OrderAction == OrderAction.SellShort
                && marketPosition == MarketPosition.Short)
            {
                entryPx  = execution.Price;
                targetPx = entryPx - TargetAtrMult * atrAtEntry;
                stopPx   = signalHigh;         // initial stop = signal bar high
                inShort  = true;
                inLong   = false;
                barsInTrade = 0;
            }
        }

        // =====================================================================
        // HELPER: ComputeStpmte
        // Builds the STPMTE weighted composite stochastic and stores in stpmteS[0]
        // =====================================================================
        private void ComputeStpmte()
        {
            // --- stok1: period 5 ---
            double ph1 = MAX(High, 5)[0];
            double pb1 = MIN(Low,  5)[0];
            stok1S[0] = (ph1 == pb1) ? 100.0 : 100.0 - ((ph1 - Close[0]) / (ph1 - pb1)) * 100.0;
            stod1S[0] = SMA(stok1S, 3)[0];

            // --- stok2: period 14 ---
            double ph2 = MAX(High, 14)[0];
            double pb2 = MIN(Low,  14)[0];
            stok2S[0] = (ph2 == pb2) ? 100.0 : 100.0 - ((ph2 - Close[0]) / (ph2 - pb2)) * 100.0;
            stod2S[0] = SMA(stok2S, 3)[0];

            // --- stok3: period 45 ---
            double ph3 = MAX(High, 45)[0];
            double pb3 = MIN(Low,  45)[0];
            stok3S[0] = (ph3 == pb3) ? 100.0 : 100.0 - ((ph3 - Close[0]) / (ph3 - pb3)) * 100.0;
            stod3S[0] = SMA(stok3S, 14)[0];

            // --- stok4: period 75 ---
            double ph4 = MAX(High, 75)[0];
            double pb4 = MIN(Low,  75)[0];
            stok4S[0] = (ph4 == pb4) ? 100.0 : 100.0 - ((ph4 - Close[0]) / (ph4 - pb4)) * 100.0;
            stod4S[0] = SMA(stok4S, 20)[0];

            // --- composite STPMTE ---
            stpmteS[0] = (4.1 * stod1S[0] + 2.5 * stod2S[0] + stod3S[0] + 4.0 * stod4S[0]) / 11.6;
        }

        // =====================================================================
        // HELPER: ComputeStpmtPose
        // Detects bullish/bearish divergence between price and STPMTE.
        // Returns: +1 (long), -1 (short), 0 (no signal)
        // =====================================================================
        private int ComputeStpmtPose()
        {
            int sig = 0;
            int smooth_h = StpmtSmoothH;
            int smooth_b = StpmtSmoothB;

            // Minimum bars needed for pivot detection
            if (CurrentBar < smooth_h + 2 || CurrentBar < smooth_b + 2)
                return 0;

            // ------------------------------------------------------------------
            // BEARISH DIVERGENCE detection (short signal)
            // A high pivot on STPMTE is confirmed at bar[smooth_h] when:
            //   stpmteS[smooth_h] == MAX(stpmteS, smooth_h+1)[0]    (was peak when formed)
            //   stpmteS[smooth_h] == MAX(stpmteS, smooth_h+1)[smooth_h] (still peak looking back)
            // ------------------------------------------------------------------
            double stpmtePeak = stpmteS[smooth_h];
            double maxNow     = MAX(stpmteS, smooth_h + 1)[0];
            double maxOld     = MAX(stpmteS, smooth_h + 1)[smooth_h];

            bool isHighPivot = Math.Abs(stpmtePeak - maxNow) < 1e-9
                            && Math.Abs(stpmtePeak - maxOld) < 1e-9;

            if (isHighPivot)
            {
                double pricePivotH = High[smooth_h];   // price high at the pivot bar

                if (!double.IsNaN(stpmt_last_h_indic))
                {
                    // Current pivot: lower STPMTE high, higher price high → bearish divergence
                    if (stpmtePeak < stpmt_last_h_indic
                        && pricePivotH > stpmt_last_h_price
                        && stpmt_counter_h <= StpmtDistMaxH)
                    {
                        sig = -1;
                    }
                }

                // Update state: this pivot becomes the reference
                stpmt_last_h_indic = stpmtePeak;
                stpmt_last_h_price = pricePivotH;
                stpmt_counter_h    = 0;
                stpmt_looking_h    = true;
            }
            else
            {
                stpmt_counter_h++;
                if (stpmt_counter_h > StpmtDistMaxH)
                {
                    // Too far — reset
                    stpmt_last_h_indic = double.NaN;
                    stpmt_last_h_price = double.NaN;
                    stpmt_counter_h    = 0;
                    stpmt_looking_h    = false;
                }
            }

            // ------------------------------------------------------------------
            // BULLISH DIVERGENCE detection (long signal)
            // A low pivot on STPMTE confirmed at bar[smooth_b]
            // ------------------------------------------------------------------
            double stpmteTrough = stpmteS[smooth_b];
            double minNow       = MIN(stpmteS, smooth_b + 1)[0];
            double minOld       = MIN(stpmteS, smooth_b + 1)[smooth_b];

            bool isLowPivot = Math.Abs(stpmteTrough - minNow) < 1e-9
                           && Math.Abs(stpmteTrough - minOld) < 1e-9;

            if (isLowPivot)
            {
                double pricePivotL = Low[smooth_b];   // price low at the pivot bar

                if (!double.IsNaN(stpmt_last_b_indic))
                {
                    // Current pivot: higher STPMTE low, lower price low → bullish divergence
                    if (stpmteTrough > stpmt_last_b_indic
                        && pricePivotL < stpmt_last_b_price
                        && stpmt_counter_b <= StpmtDistMaxL)
                    {
                        sig = 1;
                    }
                }

                stpmt_last_b_indic = stpmteTrough;
                stpmt_last_b_price = pricePivotL;
                stpmt_counter_b    = 0;
                stpmt_looking_b    = true;
            }
            else
            {
                stpmt_counter_b++;
                if (stpmt_counter_b > StpmtDistMaxL)
                {
                    stpmt_last_b_indic = double.NaN;
                    stpmt_last_b_price = double.NaN;
                    stpmt_counter_b    = 0;
                    stpmt_looking_b    = false;
                }
            }

            return sig;
        }

        // =====================================================================
        // HELPER: ComputeTrendFilter (Mogalef Trend Filter V2)
        // In the Python backtester, blocked_cases is always empty → always "pass".
        // We compute repulse for completeness but always return true.
        // Repulse: rawDiff = EMA(pushUp, period) - EMA(pushDown, period), period = R*5
        // =====================================================================
        private bool ComputeTrendFilter()
        {
            // Compute repulse for R1, R2, R3 (computed but filter always passes)
            // pushUp  = High - prior Close; pushDown = prior Close - Low
            if (CurrentBar < 2) return true;

            double pushUp   = High[0] - Close[1];
            double pushDown = Close[1] - Low[0];

            // R1
            int period1 = TrendR1 * 5;
            // EMA approximation via built-in EMA on custom values is complex;
            // we use a simplified sign check — filter always returns true per Python spec.
            // double rep1Raw = EMA(pushUpS, period1)[0] - EMA(pushDownS, period1)[0];
            // int sens_r1 = rep1Raw >= 0 ? 1 : -1;

            // Per Python spec: blocked_cases always empty → filter always returns true.
            return true;
        }

        // =====================================================================
        // HELPER: ComputeTrSeries
        // True Range and its SMAs for Stop Intelligent
        // =====================================================================
        private void ComputeTrSeries()
        {
            if (CurrentBar < 1)
            {
                trS[0]       = High[0] - Low[0];
                trRecentS[0] = trS[0];
                trRefS[0]    = trS[0];
                return;
            }

            // Standard True Range
            double hl   = High[0] - Low[0];
            double hpc  = Math.Abs(High[0] - Close[1]);
            double lpc  = Math.Abs(Low[0]  - Close[1]);
            trS[0] = Math.Max(hl, Math.Max(hpc, lpc));

            // SMAs over TR
            trRecentS[0] = SMA(trS, StopRecentVolat)[0];
            trRefS[0]    = SMA(trS, StopRefVolat)[0];
        }

        // =====================================================================
        // HELPER: UpdateStopIntelligent
        // Trailing stop based on swing pivot ± volatility space.
        // quality = StopQuality: swing high/low confirmed when bar[q] is
        //   highest/lowest of [q-quality .. q+quality] (in historical bar terms).
        // Space = ((2*ATR_ref - ATR_recent) * coef_volat) / 5
        // =====================================================================
        private void UpdateStopIntelligent()
        {
            int q = StopQuality;

            // Need enough bars to look at swing pivot
            if (CurrentBar < q * 2 + 2) return;

            // Volatility space
            double atrRecent = trRecentS[0];
            double atrRef    = trRefS[0];
            double space     = ((2.0 * atrRef - atrRecent) * StopCoefVolat) / 5.0;
            if (space < 0) space = 0;

            if (inLong)
            {
                // Find swing low: Low[q] is the minimum in [Low[0]..Low[2q]]
                double candidateLow = Low[q];
                bool isSwingLow = true;
                for (int i = 0; i <= 2 * q; i++)
                {
                    if (i == q) continue;
                    if (Low[i] < candidateLow)
                    {
                        isSwingLow = false;
                        break;
                    }
                }
                if (isSwingLow)
                {
                    double newStop = candidateLow - space;
                    // Trailing: only move stop UP
                    if (newStop > stopPx)
                        stopPx = newStop;
                }
            }
            else if (inShort)
            {
                // Find swing high: High[q] is the maximum in [High[0]..High[2q]]
                double candidateHigh = High[q];
                bool isSwingHigh = true;
                for (int i = 0; i <= 2 * q; i++)
                {
                    if (i == q) continue;
                    if (High[i] > candidateHigh)
                    {
                        isSwingHigh = false;
                        break;
                    }
                }
                if (isSwingHigh)
                {
                    double newStop = candidateHigh + space;
                    // Trailing: only move stop DOWN
                    if (newStop < stopPx)
                        stopPx = newStop;
                }
            }
        }

        // =====================================================================
        // HELPER: IsHoraireAllowed
        // Returns true if current bar's UTC hour is in the allowed list
        // =====================================================================
        private bool IsHoraireAllowed()
        {
            DateTime utcTime = Times[0][0].ToUniversalTime();
            return allowedUTCHours.Contains(utcTime.Hour);
        }

        // =====================================================================
        // HELPER: IsWeekdayAllowed
        // Returns true if current weekday is NOT in blocked list.
        // Python weekday → C# DayOfWeek mapping:
        //   Python 0 (Mon) → DayOfWeek.Monday   (1)
        //   Python 1 (Tue) → DayOfWeek.Tuesday  (2)
        //   Python 2 (Wed) → DayOfWeek.Wednesday(3)
        //   Python 3 (Thu) → DayOfWeek.Thursday (4)
        //   Python 4 (Fri) → DayOfWeek.Friday   (5)
        // =====================================================================
        private bool IsWeekdayAllowed()
        {
            DayOfWeek today = Times[0][0].DayOfWeek;
            return !blockedDays.Contains(today);
        }

        // =====================================================================
        // HELPER: IsAtrAllowed
        // Returns true if ATR(14) is within [AtrMin, AtrMax]
        // =====================================================================
        private bool IsAtrAllowed()
        {
            double atr = ATR(14)[0];
            return atr >= AtrMin && atr <= AtrMax;
        }

        // =====================================================================
        // HELPER: ResetTradeState
        // Called after any exit to clear trade tracking variables
        // =====================================================================
        private void ResetTradeState()
        {
            inLong      = false;
            inShort     = false;
            barsInTrade = 0;
            entryPx     = 0.0;
            targetPx    = 0.0;
            stopPx      = 0.0;
            pose        = 0;
        }

        // =====================================================================
        // HELPER: ParseCommaListInt
        // Parses "13,14,15,16" → HashSet<int>{13,14,15,16}
        // =====================================================================
        private HashSet<int> ParseCommaListInt(string csv)
        {
            var result = new HashSet<int>();
            if (string.IsNullOrWhiteSpace(csv)) return result;
            foreach (string token in csv.Split(','))
            {
                string t = token.Trim();
                if (int.TryParse(t, out int val))
                    result.Add(val);
            }
            return result;
        }

        // =====================================================================
        // HELPER: ParseBlockedWeekdays
        // Parses Python-numbered weekday string and returns C# DayOfWeek set.
        // Python: 0=Mon,1=Tue,2=Wed,3=Thu,4=Fri
        // C#:     Sunday=0, Monday=1, Tuesday=2, Wednesday=3, Thursday=4, Friday=5
        // =====================================================================
        private HashSet<DayOfWeek> ParseBlockedWeekdays(string csv)
        {
            var result = new HashSet<DayOfWeek>();
            if (string.IsNullOrWhiteSpace(csv)) return result;

            // Map Python weekday index → C# DayOfWeek
            DayOfWeek[] pythonToCSharp = new DayOfWeek[]
            {
                DayOfWeek.Monday,    // Python 0
                DayOfWeek.Tuesday,   // Python 1
                DayOfWeek.Wednesday, // Python 2
                DayOfWeek.Thursday,  // Python 3
                DayOfWeek.Friday     // Python 4
            };

            foreach (string token in csv.Split(','))
            {
                string t = token.Trim();
                if (int.TryParse(t, out int pyDay) && pyDay >= 0 && pyDay <= 4)
                    result.Add(pythonToCSharp[pyDay]);
            }
            return result;
        }
    }
}



