import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from agent.rl_agent import RLAgent
from features.technical_indicators import FeatureEngineer
from utils.logger import logger
from config.settings import BACKTEST_CONFIG, LOGS_DIR


class Backtester:
    def __init__(self, agent: RLAgent, feature_engineer: FeatureEngineer = None):
        self.agent = agent
        self.fe = feature_engineer or FeatureEngineer()
        self.results = {}

    def run(
        self,
        df: pd.DataFrame,
        symbol: str = "UNKNOWN",
        initial_balance: float = None,
        commission: float = None,
    ) -> dict:
        initial_balance = initial_balance or BACKTEST_CONFIG["initial_balance"]
        commission = commission or BACKTEST_CONFIG["commission_pct"]

        df_features = self.fe.add_all_indicators(df)
        feature_cols = self.fe.get_feature_columns()
        available_cols = [c for c in feature_cols if c in df_features.columns]

        df_clean = df_features.dropna(subset=available_cols).reset_index(drop=True)
        if len(df_clean) < 100:
            logger.error(f"Yetersiz veri: {len(df_clean)} satir (min 100)")
            return {}

        split_idx = int(len(df_clean) * 0.7)
        train_df = df_clean.iloc[:split_idx].copy()
        test_df = df_clean.iloc[split_idx:].copy()

        logger.info(f"Backtest basliyor | {symbol} | Egitim: {len(train_df)} | Test: {len(test_df)}")

        self.agent.train(
            df=train_df,
            feature_columns=available_cols,
            total_timesteps=min(50000, len(train_df) * 10),
            initial_balance=initial_balance,
            eval_df=test_df.iloc[:len(test_df)//2].copy(),
        )

        test_perf = self.agent.backtest(test_df, available_cols, initial_balance)
        train_perf = self.agent.backtest(train_df, available_cols, initial_balance)

        self.results = {
            "symbol": symbol,
            "train": train_perf,
            "test": test_perf,
            "train_size": len(train_df),
            "test_size": len(test_df),
        }

        self._log_results()
        self._plot_results(train_df, test_df, available_cols, symbol)

        return self.results

    def _log_results(self):
        r = self.results
        logger.info("=" * 60)
        logger.info(f"BACKTEST SONUCLARI | {r['symbol']}")
        logger.info("=" * 60)
        for phase in ["train", "test"]:
            p = r.get(phase, {})
            logger.info(f"[{phase.upper()}]")
            logger.info(f"  Toplam Getiri:  {p.get('total_return_pct', 0):.2f}%")
            logger.info(f"  Max Drawdown:   {p.get('max_drawdown_pct', 0):.2f}%")
            logger.info(f"  Sharpe Ratio:   {p.get('sharpe_ratio', 0):.4f}")
            logger.info(f"  Toplam Islem:   {p.get('total_trades', 0)}")
            logger.info(f"  Kazanma Orani:  {p.get('win_rate_pct', 0):.1f}%")
            logger.info(f"  Son Bakiye:     ${p.get('final_balance', 0):,.2f}")
        logger.info("=" * 60)

    def _plot_results(self, train_df, test_df, feature_cols, symbol):
        try:
            fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=False)

            axes[0].plot(train_df.index, train_df["close"], label="Egitim", alpha=0.7)
            axes[0].plot(test_df.index + len(train_df), test_df["close"], label="Test", alpha=0.7, color="orange")
            axes[0].set_title(f"{symbol} - Fiyat Grafigi")
            axes[0].set_ylabel("Fiyat")
            axes[0].legend()

            train_equity = self.agent.backtest(train_df, feature_cols).get("equity_curve", [])
            test_equity = self.agent.backtest(test_df, feature_cols).get("equity_curve", [])

            if train_equity:
                axes[1].plot(train_equity, label="Egitim", alpha=0.7)
            if test_equity:
                axes[1].plot(range(len(train_equity), len(train_equity) + len(test_equity)), test_equity, label="Test", alpha=0.7, color="orange")
            axes[1].set_title("Varilik Egrisi (Equity Curve)")
            axes[1].set_ylabel("Bakiye ($)")
            axes[1].legend()

            if "rsi" in train_df.columns:
                axes[2].plot(train_df.index, train_df["rsi"], label="RSI", alpha=0.7)
                axes[2].plot(test_df.index + len(train_df), test_df["rsi"], label="RSI (Test)", alpha=0.7, color="orange")
                axes[2].axhline(y=70, color="r", linestyle="--", alpha=0.5)
                axes[2].axhline(y=30, color="g", linestyle="--", alpha=0.5)
                axes[2].set_title("RSI")
                axes[2].set_ylabel("RSI")
                axes[2].legend()

            plt.tight_layout()
            plot_path = LOGS_DIR / f"backtest_{symbol}.png"
            plt.savefig(plot_path, dpi=100)
            plt.close()
            logger.info(f"Grafik kaydedildi: {plot_path}")
        except Exception as e:
            logger.error(f"Grafik olusturulurken hata: {e}")
