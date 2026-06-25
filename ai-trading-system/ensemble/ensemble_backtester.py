import numpy as np
import pandas as pd
from typing import Optional
from ensemble.ensemble_ml import EnsembleML
from features.technical_indicators import FeatureEngineer
from utils.logger import logger
from config.settings import MODELS_DIR


class EnsembleBacktester:
    def __init__(self, feature_engineer: FeatureEngineer = None):
        self.fe = feature_engineer or FeatureEngineer()
        self.ensemble = EnsembleML()

    def run(
        self,
        df: pd.DataFrame,
        symbol: str = "UNKNOWN",
        initial_balance: float = 10000.0,
        commission: float = 0.001,
        lookahead: int = 5,
        threshold: float = 0.005,
        stop_loss_pct: float = 0.02,
        take_profit_pct: float = 0.04,
    ) -> dict:
        logger.info(f"Ensemble backtest basliyor | {symbol}")

        df = self.fe.add_all_indicators(df)
        feature_cols = self.fe.get_feature_columns()
        available_cols = [c for c in feature_cols if c in df.columns]

        df_clean = df.dropna(subset=available_cols).copy()
        df_clean = df_clean.reset_index(drop=True)

        if len(df_clean) < 200:
            logger.error(f"Yetersiz veri: {len(df_clean)} satir")
            return {"error": "Yetersiz veri"}

        labels = self.ensemble.prepare_labels(df_clean, lookahead=lookahead, threshold=threshold)
        df_clean = df_clean.iloc[:-lookahead].copy()
        labels = labels.iloc[:-lookahead]

        valid_mask = labels != 0
        df_clean = df_clean[valid_mask]
        labels = labels[valid_mask]

        split_idx = int(len(df_clean) * 0.7)
        X_train = df_clean.iloc[:split_idx][available_cols]
        y_train = labels.iloc[:split_idx]
        X_val = df_clean.iloc[split_idx:][available_cols]
        y_val = labels.iloc[split_idx:]

        logger.info(f"Egitim: {len(X_train)} | Dogrulama: {len(X_val)}")

        train_results = self.ensemble.train(X_train, y_train, X_val, y_val)

        cv_results = self.ensemble.cross_validate(
            pd.concat([X_train, X_val]),
            pd.concat([y_train, y_val]),
            n_splits=5,
        )

        test_signals = self.ensemble.predict_signal(X_val)

        backtest_result = self._simulate_trades(
            df_clean.iloc[split_idx:].copy(),
            test_signals,
            initial_balance,
            commission,
            stop_loss_pct,
            take_profit_pct,
        )

        top_features = self.ensemble.get_top_features(20)

        result = {
            "symbol": symbol,
            "train_results": train_results,
            "cv_results": cv_results,
            "backtest": backtest_result,
            "top_features": top_features,
            "weights": self.ensemble.weights,
            "train_size": len(X_train),
            "val_size": len(X_val),
        }

        self._log_results(result)
        return result

    def _simulate_trades(
        self,
        df: pd.DataFrame,
        signals: np.ndarray,
        initial_balance: float,
        commission: float,
        stop_loss_pct: float,
        take_profit_pct: float,
    ) -> dict:
        balance = initial_balance
        position = 0
        entry_price = 0.0
        shares = 0.0
        equity_curve = [initial_balance]
        trades = []

        for i in range(len(df)):
            price = df.iloc[i]["close"]
            signal = signals[i] if i < len(signals) else 0

            if position == 1:
                pnl_pct = (price - entry_price) / entry_price
                if pnl_pct <= -stop_loss_pct:
                    revenue = shares * price * (1 - commission)
                    balance += revenue
                    trades.append({"step": i, "action": "sell_sl", "pnl_pct": pnl_pct})
                    position = 0
                    shares = 0.0
                elif pnl_pct >= take_profit_pct:
                    revenue = shares * price * (1 - commission)
                    balance += revenue
                    trades.append({"step": i, "action": "sell_tp", "pnl_pct": pnl_pct})
                    position = 0
                    shares = 0.0

            if signal == 1 and position == 0:
                invest = balance * 0.95
                exec_price = price * (1 + commission)
                shares = invest / exec_price
                balance -= invest
                entry_price = exec_price
                position = 1
                trades.append({"step": i, "action": "buy", "pnl_pct": 0})

            elif signal == -1 and position == 1:
                revenue = shares * price * (1 - commission)
                balance += revenue
                pnl_pct = (price - entry_price) / entry_price
                trades.append({"step": i, "action": "sell", "pnl_pct": pnl_pct})
                position = 0
                shares = 0.0

            total = balance + shares * price
            equity_curve.append(total)

        if position == 1:
            balance += shares * df.iloc[-1]["close"] * (1 - commission)

        equity = np.array(equity_curve)
        returns = np.diff(equity) / (equity[:-1] + 1e-10)

        sell_trades = [t for t in trades if t["action"] in ("sell", "sell_sl", "sell_tp")]
        winning = [t for t in sell_trades if t["pnl_pct"] > 0]
        losing = [t for t in sell_trades if t["pnl_pct"] <= 0]

        return {
            "initial_balance": initial_balance,
            "final_balance": balance,
            "total_return_pct": (balance - initial_balance) / initial_balance * 100,
            "max_drawdown_pct": (1 - equity / np.maximum.accumulate(equity)).max() * 100,
            "sharpe_ratio": np.sqrt(252) * returns.mean() / (returns.std() + 1e-10) if len(returns) > 0 else 0,
            "total_trades": len(sell_trades),
            "win_rate_pct": (len(winning) / len(sell_trades) * 100) if sell_trades else 0,
            "avg_win_pct": np.mean([t["pnl_pct"] for t in winning]) * 100 if winning else 0,
            "avg_loss_pct": np.mean([t["pnl_pct"] for t in losing]) * 100 if losing else 0,
            "equity_curve": equity_curve.tolist(),
        }

    def _log_results(self, result: dict):
        logger.info(f"\n{'='*70}")
        logger.info(f"ENSEMBLE BACKTEST SONUCLARI | {result['symbol']}")
        logger.info(f"{'='*70}")

        logger.info("Model Performanslari:")
        for model_name, metrics in result.get("train_results", {}).items():
            if metrics:
                logger.info(f"  {model_name:<12} | Acc: {metrics.get('accuracy', 0):.4f} | F1: {metrics.get('f1', 0):.4f}")

        logger.info(f"\nCross-Validation (5-fold):")
        for model_name, cv in result.get("cv_results", {}).items():
            logger.info(f"  {model_name:<12} | Mean: {cv['mean']:.4f} (+/- {cv['std']:.4f})")

        bt = result.get("backtest", {})
        logger.info(f"\nBacktest Sonuclari:")
        logger.info(f"  Toplam Getiri:  {bt.get('total_return_pct', 0):.2f}%")
        logger.info(f"  Max Drawdown:   {bt.get('max_drawdown_pct', 0):.2f}%")
        logger.info(f"  Sharpe Ratio:   {bt.get('sharpe_ratio', 0):.4f}")
        logger.info(f"  Toplam Islem:   {bt.get('total_trades', 0)}")
        logger.info(f"  Kazanma Orani:  {bt.get('win_rate_pct', 0):.1f}%")
        logger.info(f"  Son Bakiye:     ${bt.get('final_balance', 0):,.2f}")

        logger.info(f"\nEnsemble Agirliklari:")
        for model, weight in result.get("weights", {}).items():
            logger.info(f"  {model:<12}: {weight:.2f}")

        logger.info(f"\nEn Onemli 10 Ozellik:")
        for i, (feature, score) in enumerate(list(result.get("top_features", {}).items())[:10], 1):
            logger.info(f"  {i:2d}. {feature:<25} ({score:.4f})")

        logger.info(f"{'='*70}")
