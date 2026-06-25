import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from strategies.strategy_engine import StrategyEngine
from strategies.classic_strategies import ALL_STRATEGIES
from features.technical_indicators import FeatureEngineer
from utils.logger import logger
from config.settings import BACKTEST_CONFIG, LOGS_DIR


class StrategyBacktester:
    def __init__(self, feature_engineer: FeatureEngineer = None):
        self.fe = feature_engineer or FeatureEngineer()
        self.engine = StrategyEngine(self.fe)

    def run_single(self, df: pd.DataFrame, strategy_name: str, symbol: str = "UNKNOWN",
                   initial_balance: float = None, stop_loss: float = 0.02, take_profit: float = 0.04) -> dict:
        if strategy_name not in ALL_STRATEGIES:
            logger.error(f"Bilinmeyen strateji: {strategy_name}")
            logger.info(f"Mevcut stratejiler: {list(ALL_STRATEGIES.keys())}")
            return {}

        initial_balance = initial_balance or BACKTEST_CONFIG["initial_balance"]
        strategy = ALL_STRATEGIES[strategy_name]()
        result = self.engine.backtest_strategy(
            df, strategy,
            initial_balance=initial_balance,
            stop_loss_pct=stop_loss,
            take_profit_pct=take_profit,
        )
        self._log_single_result(result, symbol)
        self._plot_single(df, result, symbol, strategy_name)
        return result

    def run_comparison(self, df: pd.DataFrame, symbol: str = "UNKNOWN",
                       initial_balance: float = None, stop_loss: float = 0.02, take_profit: float = 0.04) -> pd.DataFrame:
        initial_balance = initial_balance or BACKTEST_CONFIG["initial_balance"]
        logger.info(f"Strateji karsilastirmasi basliyor | {symbol} | {len(ALL_STRATEGIES)} strateji")

        comparison = self.engine.compare_all_strategies(
            df, initial_balance=initial_balance,
            stop_loss_pct=stop_loss, take_profit_pct=take_profit,
        )

        self._log_comparison(comparison, symbol)
        self._plot_comparison(comparison, symbol)
        return comparison

    def run_top_strategies(self, df: pd.DataFrame, symbol: str = "UNKNOWN", top_n: int = 5,
                           initial_balance: float = None, sort_by: str = "sharpe_ratio") -> list:
        initial_balance = initial_balance or BACKTEST_CONFIG["initial_balance"]
        logger.info(f"En iyi {top_n} strateji aranıyor | {symbol} | Siralama: {sort_by}")

        top = self.engine.get_best_strategies(df, top_n=top_n, sort_by=sort_by)

        logger.info(f"\n{'='*80}")
        logger.info(f"EN IYI {top_n} STRATEJI | {symbol} | Siralama: {sort_by}")
        logger.info(f"{'='*80}")
        for i, r in enumerate(top, 1):
            logger.info(f"#{i} {r['strategy_name']}")
            logger.info(f"   Getiri: {r['total_return_pct']:.2f}% | Max DD: {r['max_drawdown_pct']:.2f}% | Sharpe: {r['sharpe_ratio']:.3f}")
            logger.info(f"   Islem: {r['total_trades']} | Kazanma: {r['win_rate_pct']:.1f}% | PF: {r['profit_factor']:.2f}")
        logger.info(f"{'='*80}")

        self._plot_top_strategies(df, top, symbol)
        return top

    def run_ensemble(self, df: pd.DataFrame, symbol: str = "UNKNOWN",
                     initial_balance: float = None, stop_loss: float = 0.02, take_profit: float = 0.04) -> dict:
        initial_balance = initial_balance or BACKTEST_CONFIG["initial_balance"]
        df = self.engine.prepare_data(df)

        all_signals = {}
        for name, strategy_cls in ALL_STRATEGIES.items():
            strategy = strategy_cls()
            signals = strategy.generate_signals(df)
            all_signals[name] = signals

        consensus = pd.Series(0, index=df.index, dtype=float)
        for name, signals in all_signals.items():
            consensus += signals

        avg_consensus = consensus / len(all_signals)

        balance = initial_balance
        position = 0
        entry_price = 0.0
        shares = 0.0
        equity_curve = [initial_balance]
        trades = []

        for i in range(len(df)):
            price = df.iloc[i]["close"]
            signal = avg_consensus.iloc[i]

            if position == 1:
                pnl_pct = (price - entry_price) / entry_price
                if pnl_pct <= -stop_loss:
                    revenue = shares * price * 0.999
                    balance += revenue
                    trades.append({"step": i, "action": "sell_sl", "pnl_pct": pnl_pct})
                    position = 0
                    shares = 0.0
                elif pnl_pct >= take_profit:
                    revenue = shares * price * 0.999
                    balance += revenue
                    trades.append({"step": i, "action": "sell_tp", "pnl_pct": pnl_pct})
                    position = 0
                    shares = 0.0

            if signal > 0.3 and position == 0:
                invest = balance * 0.95
                exec_price = price * 1.0005
                shares = invest / exec_price
                balance -= invest
                entry_price = exec_price
                position = 1
                trades.append({"step": i, "action": "buy", "pnl_pct": 0})

            elif signal < -0.3 and position == 1:
                revenue = shares * price * 0.999
                balance += revenue
                pnl_pct = (price - entry_price) / entry_price
                trades.append({"step": i, "action": "sell", "pnl_pct": pnl_pct})
                position = 0
                shares = 0.0

            total = balance + shares * price
            equity_curve.append(total)

        if position == 1:
            balance += shares * df.iloc[-1]["close"] * 0.999

        equity = np.array(equity_curve)
        returns = np.diff(equity) / (equity[:-1] + 1e-10)
        sell_trades = [t for t in trades if t["action"] in ("sell", "sell_sl", "sell_tp")]
        winning = [t for t in sell_trades if t["pnl_pct"] > 0]

        result = {
            "strategy_name": f"Ensemble ({len(ALL_STRATEGIES)} strateji)",
            "initial_balance": initial_balance,
            "final_balance": balance,
            "total_return_pct": (balance - initial_balance) / initial_balance * 100,
            "max_drawdown_pct": (1 - equity / np.maximum.accumulate(equity)).max() * 100,
            "sharpe_ratio": np.sqrt(252) * returns.mean() / (returns.std() + 1e-10) if len(returns) > 0 else 0,
            "total_trades": len(sell_trades),
            "win_rate_pct": (len(winning) / len(sell_trades) * 100) if sell_trades else 0,
            "equity_curve": equity_curve,
            "trades": trades,
        }

        self._log_single_result(result, symbol)
        return result

    def _log_single_result(self, result: dict, symbol: str):
        logger.info(f"\n{'='*60}")
        logger.info(f"STRATEJI BACKTEST | {symbol}")
        logger.info(f"{'='*60}")
        logger.info(f"Strateji:       {result.get('strategy_name', 'N/A')}")
        logger.info(f"Baslangic:      ${result.get('initial_balance', 0):,.2f}")
        logger.info(f"Son Bakiye:     ${result.get('final_balance', 0):,.2f}")
        logger.info(f"Toplam Getiri:  {result.get('total_return_pct', 0):.2f}%")
        logger.info(f"Max Drawdown:   {result.get('max_drawdown_pct', 0):.2f}%")
        logger.info(f"Sharpe Ratio:   {result.get('sharpe_ratio', 0):.4f}")
        logger.info(f"Toplam Islem:   {result.get('total_trades', 0)}")
        logger.info(f"Kazanma Orani:  {result.get('win_rate_pct', 0):.1f}%")
        logger.info(f"Ort Kazanc:     {result.get('avg_win_pct', 0):.2f}%")
        logger.info(f"Ort Kayip:      {result.get('avg_loss_pct', 0):.2f}%")
        pf = result.get('profit_factor', 0)
        logger.info(f"Profit Factor:  {pf:.2f}" if pf != float('inf') else "Profit Factor:  inf")
        logger.info(f"{'='*60}")

    def _log_comparison(self, comparison: pd.DataFrame, symbol: str):
        logger.info(f"\n{'='*100}")
        logger.info(f"STRATEJI KARŞILAŞTIRMASI | {symbol} | {len(comparison)} strateji")
        logger.info(f"{'='*100}")
        logger.info(f"\n{comparison.to_string(index=False)}")
        logger.info(f"{'='*100}")

        if "Getiri %" in comparison.columns:
            sorted_df = comparison.copy()
            sorted_df["Getiri_Sayısal"] = sorted_df["Getiri %"].str.replace("%", "").astype(float)
            best = sorted_df.loc[sorted_df["Getiri_Sayısal"].idxmax()]
            logger.info(f"\nEn Yuksek Getiri: {best['Strateji']} | {best['Getiri %']}")

        if "Sharpe" in comparison.columns:
            sorted_df = comparison.copy()
            sorted_df["Sharpe_Sayısal"] = sorted_df["Sharpe"].astype(float)
            best = sorted_df.loc[sorted_df["Sharpe_Sayısal"].idxmax()]
            logger.info(f"En Iyi Sharpe:    {best['Strateji']} | {best['Sharpe']}")

    def _plot_single(self, df: pd.DataFrame, result: dict, symbol: str, strategy_name: str):
        try:
            fig, axes = plt.subplots(4, 1, figsize=(16, 14), sharex=False)

            axes[0].plot(df.index, df["close"], label="Fiyat", alpha=0.8)
            axes[0].set_title(f"{symbol} - Fiyat")
            axes[0].set_ylabel("Fiyat")
            axes[0].legend()

            equity = result.get("equity_curve", [])
            if equity:
                axes[1].plot(equity, label="Varilik", color="green", alpha=0.8)
                axes[1].axhline(y=result["initial_balance"], color="gray", linestyle="--", alpha=0.5)
                axes[1].set_title(f"Varilik Egrisi | Getiri: {result['total_return_pct']:.2f}%")
                axes[1].set_ylabel("Bakiye ($)")
                axes[1].legend()

            if "rsi" in df.columns:
                axes[2].plot(df.index, df["rsi"], label="RSI", alpha=0.7)
                axes[2].axhline(y=70, color="r", linestyle="--", alpha=0.5)
                axes[2].axhline(y=30, color="g", linestyle="--", alpha=0.5)
                axes[2].set_title("RSI")
                axes[2].set_ylabel("RSI")
                axes[2].legend()

            if "macd" in df.columns:
                axes[3].plot(df.index, df["macd"], label="MACD", alpha=0.7)
                axes[3].plot(df.index, df["macd_signal"], label="Signal", alpha=0.7)
                axes[3].bar(df.index, df["macd_diff"], alpha=0.3, label="Histogram")
                axes[3].set_title("MACD")
                axes[3].legend()

            plt.suptitle(f"{symbol} - {result.get('strategy_name', strategy_name)}", fontsize=14, fontweight="bold")
            plt.tight_layout()
            plot_path = LOGS_DIR / f"strategy_{symbol}_{strategy_name}.png"
            plt.savefig(plot_path, dpi=100)
            plt.close()
            logger.info(f"Grafik kaydedildi: {plot_path}")
        except Exception as e:
            logger.error(f"Grafik hatasi: {e}")

    def _plot_comparison(self, comparison: pd.DataFrame, symbol: str):
        try:
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))

            names = [n[:25] for n in comparison["Strateji"].values]
            returns = comparison["Getiri %"].str.replace("%", "").astype(float).values
            sharpe = comparison["Sharpe"].astype(float).values
            win_rates = comparison["Kazanma %"].str.replace("%", "").astype(float).values
            drawdowns = comparison["Max DD %"].str.replace("%", "").astype(float).values

            colors = ["green" if r > 0 else "red" for r in returns]
            axes[0, 0].barh(range(len(names)), returns, color=colors, alpha=0.7)
            axes[0, 0].set_yticks(range(len(names)))
            axes[0, 0].set_yticklabels(names, fontsize=7)
            axes[0, 0].set_title("Toplam Getiri (%)")
            axes[0, 0].axvline(x=0, color="black", linewidth=0.5)

            axes[0, 1].barh(range(len(names)), sharpe, color="steelblue", alpha=0.7)
            axes[0, 1].set_yticks(range(len(names)))
            axes[0, 1].set_yticklabels(names, fontsize=7)
            axes[0, 1].set_title("Sharpe Ratio")

            axes[1, 0].barh(range(len(names)), win_rates, color="orange", alpha=0.7)
            axes[1, 0].set_yticks(range(len(names)))
            axes[1, 0].set_yticklabels(names, fontsize=7)
            axes[1, 0].set_title("Kazanma Orani (%)")
            axes[1, 0].axvline(x=50, color="gray", linestyle="--", alpha=0.5)

            axes[1, 1].barh(range(len(names)), drawdowns, color="crimson", alpha=0.7)
            axes[1, 1].set_yticks(range(len(names)))
            axes[1, 1].set_yticklabels(names, fontsize=7)
            axes[1, 1].set_title("Max Drawdown (%)")

            plt.suptitle(f"{symbol} - Strateji Karsilastirmasi", fontsize=14, fontweight="bold")
            plt.tight_layout()
            plot_path = LOGS_DIR / f"strategy_comparison_{symbol}.png"
            plt.savefig(plot_path, dpi=100)
            plt.close()
            logger.info(f"Karsilastirma grafigi kaydedildi: {plot_path}")
        except Exception as e:
            logger.error(f"Karsilastirma grafigi hatasi: {e}")

    def _plot_top_strategies(self, df: pd.DataFrame, top_results: list, symbol: str):
        try:
            fig, axes = plt.subplots(2, 1, figsize=(16, 10))

            for i, r in enumerate(top_results):
                equity = r.get("equity_curve", [])
                if equity:
                    normalized = [e / equity[0] * 100 for e in equity]
                    axes[0].plot(normalized, label=r["strategy_name"][:30], alpha=0.8)

            axes[0].axhline(y=100, color="gray", linestyle="--", alpha=0.5)
            axes[0].set_title(f"{symbol} - En Iyi {len(top_results)} Stratejinin Varilik Egrisi (Normalize)")
            axes[0].set_ylabel("Varilik (%)")
            axes[0].legend(fontsize=8)

            names = [r["strategy_name"][:25] for r in top_results]
            returns = [r["total_return_pct"] for r in top_results]
            colors = ["green" if r > 0 else "red" for r in returns]
            axes[1].barh(range(len(names)), returns, color=colors, alpha=0.7)
            axes[1].set_yticks(range(len(names)))
            axes[1].set_yticklabels(names, fontsize=8)
            axes[1].set_title("Toplam Getiri (%)")
            axes[1].axvline(x=0, color="black", linewidth=0.5)

            plt.tight_layout()
            plot_path = LOGS_DIR / f"top_strategies_{symbol}.png"
            plt.savefig(plot_path, dpi=100)
            plt.close()
            logger.info(f"En iyi stratejiler grafigi kaydedildi: {plot_path}")
        except Exception as e:
            logger.error(f"Grafik hatasi: {e}")
