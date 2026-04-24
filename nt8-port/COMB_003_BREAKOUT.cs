//
// COMB_003 Breakout Trading Version C - NT8 NinjaScript Implementation
// Signal: Structural Breakout | Contexto: Horaire | Exits: Fixed Target + Fixed Stop (1:4 R:R)
//
#region Using declarations
using System;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Windows.Media;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;
#endregion

namespace NinjaTrader.NinjaScript.Strategies
{
    public class COMB_003_BREAKOUT : Strategy
    {
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
        [Range(1, 50)]
        [Display(Name = "Breakout Lookback High", Order = 1, GroupName = "Signal")]
        public int BreakoutLookbackHigh { get; set; }

        [NinjaScriptProperty]
        [Range(1, 50)]
        [Display(Name = "Breakout Lookback Low", Order = 2, GroupName = "Signal")]
        public int BreakoutLookbackLow { get; set; }

        [NinjaScriptProperty]
        [Range(0, 50)]
        [Display(Name = "Breakout Min Points", Order = 3, GroupName = "Signal")]
        public double BreakoutMinBreakoutPoints { get; set; }

        [NinjaScriptProperty]
        [Range(30, 200)]
        [Display(Name = "Neutral Zone EMA Period", Order = 10, GroupName = "Contexto - Neutral Zone")]
        public int NeutralZoneEmaPeriod { get; set; }

        [NinjaScriptProperty]
        [Range(50, 150)]
        [Display(Name = "Neutral Zone RET Window", Order = 11, GroupName = "Contexto - Neutral Zone")]
        public int NeutralZoneRetWindow { get; set; }

        [NinjaScriptProperty]
        [Range(1, 5)]
        [Display(Name = "Trend R1", Order = 20, GroupName = "Contexto - Trend")]
        public int TrendR1 { get; set; }

        [NinjaScriptProperty]
        [Range(50, 150)]
        [Display(Name = "Trend R2", Order = 21, GroupName = "Contexto - Trend")]
        public int TrendR2 { get; set; }

        [NinjaScriptProperty]
        [Range(100, 300)]
        [Display(Name = "Trend R3", Order = 22, GroupName = "Contexto - Trend")]
        public int TrendR3 { get; set; }

        [NinjaScriptProperty]
        [Range(0, 23)]
        [Display(Name = "Horaire Start Hour (UTC)", Order = 30, GroupName = "Contexto - Horaire")]
        public int HoraireStartHour { get; set; }

        [NinjaScriptProperty]
        [Range(0, 23)]
        [Display(Name = "Horaire End Hour (UTC)", Order = 31, GroupName = "Contexto - Horaire")]
        public int HoraireEndHour { get; set; }

        [NinjaScriptProperty]
        [Range(5, 50)]
        [Display(Name = "Stop Loss Points", Order = 40, GroupName = "Exits")]
        public double StopLossPoints { get; set; }

        [NinjaScriptProperty]
        [Range(20, 200)]
        [Display(Name = "Profit Target Points", Order = 41, GroupName = "Exits")]
        public double ProfitTargetPoints { get; set; }
        #endregion

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = "COMB_003 Breakout Trading - Eric Mogalef Methodology";
                Name = "COMB_003_BREAKOUT";
                Calculate = Calculate.OnBarClose;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy = true;
                ExitOnSessionCloseSeconds = 30;
                IsFillLimitOnTouch = false;

                BreakoutLookbackHigh = 10;
                BreakoutLookbackLow = 10;
                BreakoutMinBreakoutPoints = 5.0;
                NeutralZoneEmaPeriod = 50;
                NeutralZoneRetWindow = 90;
                TrendR1 = 1;
                TrendR2 = 90;
                TrendR3 = 150;
                HoraireStartHour = 8;
                HoraireEndHour = 21;
                StopLossPoints = 20.0;
                ProfitTargetPoints = 80.0;
            }
        }

        protected override void OnBarUpdate()
        {
            if (CurrentBar < BreakoutLookbackHigh + BreakoutLookbackLow + 10)
                return;

            int currentHour = Time[0].Hour;
            bool horaireOk = (currentHour >= HoraireStartHour && currentHour <= HoraireEndHour);
            bool contextoOk = horaireOk;

            bool longBreakout = false;
            bool shortBreakout = false;

            double lookbackHigh = High[1];
            for (int i = 2; i <= BreakoutLookbackHigh; i++)
            {
                if (High[i] > lookbackHigh)
                    lookbackHigh = High[i];
            }
            if (Close[0] > lookbackHigh + BreakoutMinBreakoutPoints && contextoOk)
                longBreakout = true;

            double lookbackLow = Low[1];
            for (int i = 2; i <= BreakoutLookbackLow; i++)
            {
                if (Low[i] < lookbackLow)
                    lookbackLow = Low[i];
            }
            if (Close[0] < lookbackLow - BreakoutMinBreakoutPoints && contextoOk)
                shortBreakout = true;

            if (entrySide == 0)
            {
                if (longBreakout && Close[0] > Open[0])
                {
                    entrySide = 1;
                    entryPrice = Close[0];
                    targetPrice = entryPrice + ProfitTargetPoints;
                    stopPrice = entryPrice - StopLossPoints;
                    barsInTrade = 0;
                    EnterLong(1, "LongEntry");
                }
                else if (shortBreakout && Close[0] < Open[0])
                {
                    entrySide = -1;
                    entryPrice = Close[0];
                    targetPrice = entryPrice - ProfitTargetPoints;
                    stopPrice = entryPrice + StopLossPoints;
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
