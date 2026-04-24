//
// COMB_002 Impulse Trading Version B - NT8 NinjaScript Implementation
// Signal: Momentum | Contexto: Horaire + Volatility (NO Trend) | Exits: Scalping Target + 15-bar TimeStop + SuperStop
//
#region Using declarations
using System;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Windows.Media;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.Indicators;
#endregion

namespace NinjaTrader.NinjaScript.Strategies
{
    public class COMB_002_IMPULSE : Strategy
    {
        private ATR atr;
        private double targetPrice = 0;
        private double stopPrice = 0;
        private double entryPrice = 0;
        private int barsInTrade = 0;
        private int entrySide = 0;
        private int tradesWon = 0;
        private int tradesLost = 0;
        private double totalEquity = 0;

        #region Parameters
        [NinjaScriptProperty]
        [Range(1, 10)]
        [Display(Name = "STPMT Smooth H", Order = 1, GroupName = "Signal")]
        public int StpmtSmoothH { get; set; }

        [NinjaScriptProperty]
        [Range(1, 10)]
        [Display(Name = "STPMT Smooth B", Order = 2, GroupName = "Signal")]
        public int StpmtSmoothB { get; set; }

        [NinjaScriptProperty]
        [Range(50, 300)]
        [Display(Name = "STPMT Distance Max H", Order = 3, GroupName = "Signal")]
        public int StpmtDistanceMaxH { get; set; }

        [NinjaScriptProperty]
        [Range(50, 300)]
        [Display(Name = "STPMT Distance Max L", Order = 4, GroupName = "Signal")]
        public int StpmtDistanceMaxL { get; set; }

        [NinjaScriptProperty]
        [Range(0, 23)]
        [Display(Name = "Horaire Start Hour (UTC)", Order = 10, GroupName = "Contexto - Horaire")]
        public int HoraireStartHour { get; set; }

        [NinjaScriptProperty]
        [Range(0, 23)]
        [Display(Name = "Horaire End Hour (UTC)", Order = 11, GroupName = "Contexto - Horaire")]
        public int HoraireEndHour { get; set; }

        [NinjaScriptProperty]
        [Range(0, 100)]
        [Display(Name = "ATR Min (points)", Order = 20, GroupName = "Contexto - Volatility")]
        public double VolatilityAtrMin { get; set; }

        [NinjaScriptProperty]
        [Range(100, 500)]
        [Display(Name = "ATR Max (points)", Order = 21, GroupName = "Contexto - Volatility")]
        public double VolatilityAtrMax { get; set; }

        [NinjaScriptProperty]
        [Range(1.0, 10.0)]
        [Display(Name = "Scalping Target Coef Volat", Order = 30, GroupName = "Exits")]
        public double ScalpingTargetCoefVolat { get; set; }

        [NinjaScriptProperty]
        [Range(5, 50)]
        [Display(Name = "TimeStop Bars (Impulse)", Order = 31, GroupName = "Exits")]
        public int TimescanBars { get; set; }

        [NinjaScriptProperty]
        [Range(1.0, 10.0)]
        [Display(Name = "SuperStop Coef Volat", Order = 40, GroupName = "Stops")]
        public double SuperstopCoefVolat { get; set; }
        #endregion

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = "COMB_002 Impulse Trading - Eric Mogalef Methodology";
                Name = "COMB_002_IMPULSE";
                Calculate = Calculate.OnBarClose;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy = true;
                ExitOnSessionCloseSeconds = 30;
                IsFillLimitOnTouch = false;

                StpmtSmoothH = 2;
                StpmtSmoothB = 2;
                StpmtDistanceMaxH = 200;
                StpmtDistanceMaxL = 200;
                HoraireStartHour = 9;
                HoraireEndHour = 15;
                VolatilityAtrMin = 0.0;
                VolatilityAtrMax = 500.0;
                ScalpingTargetCoefVolat = 3.0;
                TimescanBars = 15;
                SuperstopCoefVolat = 3.0;
            }
            else if (State == State.DataLoaded)
            {
                atr = ATR(14);
            }
        }

        protected override void OnBarUpdate()
        {
            if (CurrentBar < StpmtSmoothH + 50)
                return;

            double currentAtr = atr[0];
            int currentHour = Time[0].Hour;
            bool horaireOk = (currentHour >= HoraireStartHour && currentHour <= HoraireEndHour);
            bool volatilityOk = (currentAtr >= VolatilityAtrMin && currentAtr <= VolatilityAtrMax);
            bool contextoOk = horaireOk && volatilityOk;

            double priceChange = Close[0] - Close[StpmtSmoothH];
            bool longSignal = priceChange > 0 && contextoOk;
            bool shortSignal = priceChange < 0 && contextoOk;

            if (entrySide == 0)
            {
                if (longSignal && Close[0] > Open[0])
                {
                    entrySide = 1;
                    entryPrice = Close[0];
                    targetPrice = entryPrice + (currentAtr * ScalpingTargetCoefVolat);
                    stopPrice = entryPrice - (currentAtr * (SuperstopCoefVolat / 2));
                    barsInTrade = 0;
                    EnterLong(1, "LongEntry");
                }
                else if (shortSignal && Close[0] < Open[0])
                {
                    entrySide = -1;
                    entryPrice = Close[0];
                    targetPrice = entryPrice - (currentAtr * ScalpingTargetCoefVolat);
                    stopPrice = entryPrice + (currentAtr * (SuperstopCoefVolat / 2));
                    barsInTrade = 0;
                    EnterShort(1, "ShortEntry");
                }
            }
            else
            {
                barsInTrade++;

                if ((entrySide == 1 && Low[0] <= stopPrice) ||
                    (entrySide == -1 && High[0] >= stopPrice))
                {
                    ExitTrade("Stop");
                    totalEquity += (entrySide == 1 ? stopPrice - entryPrice : entryPrice - stopPrice);
                    tradesLost++;
                }
                else if ((entrySide == 1 && High[0] >= targetPrice) ||
                         (entrySide == -1 && Low[0] <= targetPrice))
                {
                    ExitTrade("Target");
                    totalEquity += (entrySide == 1 ? targetPrice - entryPrice : entryPrice - targetPrice);
                    tradesWon++;
                }
                else if (barsInTrade >= TimescanBars)
                {
                    ExitTrade("TimeStop");
                    double pnl = entrySide == 1 ? Close[0] - entryPrice : entryPrice - Close[0];
                    totalEquity += pnl;
                    if (pnl > 0) tradesWon++;
                    else tradesLost++;
                }
            }
        }

        private void ExitTrade(string reason)
        {
            if (entrySide == 1)
                ExitLong(1, reason, "LongEntry");
            else if (entrySide == -1)
                ExitShort(1, reason, "ShortEntry");

            entrySide = 0;
        }
    }
}
