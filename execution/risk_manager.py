import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from utils.logger import logger
from config.settings import RISK_CONFIG


class RiskManager:
    def __init__(self, config=None):
        self.config = config or RISK_CONFIG
        self.daily_start_balance = 0.0
        self.weekly_start_balance = 0.0
        self.daily_pnl = 0.0
        self.weekly_pnl = 0.0
        self.open_trades = 0
        self.last_reset_date = datetime.utcnow().date()
        self.last_week_reset = self._get_week_start()
        self.trade_history = []
        self.open_positions = {}

        self.max_daily_loss_pct = self.config.get("max_daily_loss_pct", 0.05)
        self.max_weekly_loss_pct = self.config.get("max_weekly_loss_pct", 0.10)
        self.max_open_trades = self.config.get("max_open_trades", 3)
        self.max_position_pct = self.config.get("max_position_pct", 0.02)
        self.max_correlation = self.config.get("max_correlation", 0.7)
        self.stop_loss_pct = self.config.get("stop_loss_pct", 0.02)
        self.take_profit_pct = self.config.get("take_profit_pct", 0.04)
        self.trailing_stop_pct = self.config.get("trailing_stop_pct", 0.015)

    def _get_week_start(self) -> datetime:
        today = datetime.utcnow().date()
        monday = today - timedelta(days=today.weekday())
        return datetime(monday.year, monday.month, monday.day)

    def _check_day_reset(self):
        today = datetime.utcnow().date()
        if today != self.last_reset_date:
            self.daily_pnl = 0.0
            self.last_reset_date = today
            logger.info("Gunluk PnL sifirlandi")

    def _check_week_reset(self):
        current_week = self._get_week_start()
        if current_week != self.last_week_reset:
            self.weekly_pnl = 0.0
            self.last_week_reset = current_week
            logger.info("Haftalik PnL sifirlandi")

    def set_start_balance(self, balance: float):
        self.daily_start_balance = balance
        self.weekly_start_balance = balance

    def can_open_trade(
        self,
        current_balance: float,
        symbol: str = None,
        price_data: Optional[dict] = None,
    ) -> tuple[bool, str]:
        self._check_day_reset()
        self._check_week_reset()

        if self.open_trades >= self.max_open_trades:
            return False, f"Maksimum acik islem limitine ulasildi: {self.max_open_trades}"

        if self.daily_start_balance > 0:
            daily_loss = (self.daily_start_balance - current_balance) / self.daily_start_balance
            if daily_loss >= self.max_daily_loss_pct:
                return False, f"Gunluk kayip limiti asildi: {daily_loss:.2%} >= {self.max_daily_loss_pct:.2%}"

        if self.weekly_start_balance > 0:
            weekly_loss = (self.weekly_start_balance - current_balance) / self.weekly_start_balance
            if weekly_loss >= self.max_weekly_loss_pct:
                return False, f"Haftalik kayip limiti asildi: {weekly_loss:.2%} >= {self.max_weekly_loss_pct:.2%}"

        if symbol and price_data:
            is_correlated, reason = self.check_correlation(symbol, price_data)
            if is_correlated:
                return False, f"Korelasyon kontrolu: {reason}"

        consecutive_losses = self._count_consecutive_losses()
        if consecutive_losses >= 5:
            return False, f"Art arda {consecutive_losses} kayip islem. Kisa sureli duraklama onerilir."

        return True, ""

    def check_correlation(self, new_symbol: str, price_data: dict) -> tuple[bool, str]:
        if not self.open_positions:
            return False, ""

        correlations = {}
        for existing_symbol, pos_data in self.open_positions.items():
            if existing_symbol == new_symbol:
                return True, f"Ayni sembolde zaten pozisyon var: {existing_symbol}"

            if "prices" in pos_data and "new_prices" in price_data:
                existing_prices = pos_data["prices"]
                new_prices = price_data["new_prices"]

                min_len = min(len(existing_prices), len(new_prices))
                if min_len >= 20:
                    corr = np.corrcoef(existing_prices[-min_len:], new_prices[-min_len:])[0, 1]
                    correlations[existing_symbol] = corr

                    if abs(corr) > self.max_correlation:
                        return True, f"{existing_symbol} ile korelasyon: {corr:.3f} (limit: {self.max_correlation})"

        return False, ""

    def calculate_position_size(self, balance: float, price: float, volatility: float = None) -> float:
        risk_amount = balance * self.max_position_pct

        if volatility is not None:
            base_volatility = 0.02
            vol_adjustment = base_volatility / max(volatility, 0.001)
            vol_adjustment = max(0.5, min(2.0, vol_adjustment))
            risk_amount *= vol_adjustment

        shares = risk_amount / price
        return shares

    def get_stop_loss(self, entry_price: float, side: str = "long", atr: float = None) -> float:
        if atr is not None:
            multiplier = 2.0
            if side == "long":
                return entry_price - (atr * multiplier)
            return entry_price + (atr * multiplier)

        if side == "long":
            return entry_price * (1 - self.stop_loss_pct)
        return entry_price * (1 + self.stop_loss_pct)

    def get_take_profit(self, entry_price: float, side: str = "long", atr: float = None) -> float:
        if atr is not None:
            multiplier = 3.0
            if side == "long":
                return entry_price + (atr * multiplier)
            return entry_price - (atr * multiplier)

        if side == "long":
            return entry_price * (1 + self.take_profit_pct)
        return entry_price * (1 - self.take_profit_pct)

    def get_trailing_stop(self, current_price: float, side: str = "long") -> float:
        if side == "long":
            return current_price * (1 - self.trailing_stop_pct)
        return current_price * (1 + self.trailing_stop_pct)

    def record_trade_open(self, symbol: str, price_data: list = None):
        self.open_trades += 1
        self.open_positions[symbol] = {
            "opened_at": datetime.utcnow(),
            "prices": price_data or [],
        }

    def record_trade_close(self, symbol: str, pnl: float):
        self.open_trades = max(0, self.open_trades - 1)
        self.daily_pnl += pnl
        self.weekly_pnl += pnl

        self.trade_history.append({
            "symbol": symbol,
            "pnl": pnl,
            "closed_at": datetime.utcnow(),
            "daily_pnl_after": self.daily_pnl,
            "weekly_pnl_after": self.weekly_pnl,
        })

        if symbol in self.open_positions:
            del self.open_positions[symbol]

    def update_position_price(self, symbol: str, price: float):
        if symbol in self.open_positions:
            if "prices" not in self.open_positions[symbol]:
                self.open_positions[symbol]["prices"] = []
            self.open_positions[symbol]["prices"].append(price)

    def _count_consecutive_losses(self) -> int:
        if not self.trade_history:
            return 0

        consecutive = 0
        for trade in reversed(self.trade_history):
            if trade["pnl"] < 0:
                consecutive += 1
            else:
                break
        return consecutive

    def get_status(self) -> dict:
        return {
            "open_trades": self.open_trades,
            "daily_pnl": self.daily_pnl,
            "weekly_pnl": self.weekly_pnl,
            "max_open_trades": self.max_open_trades,
            "max_daily_loss_pct": self.max_daily_loss_pct,
            "max_weekly_loss_pct": self.max_weekly_loss_pct,
            "max_correlation": self.max_correlation,
            "consecutive_losses": self._count_consecutive_losses(),
            "total_trades": len(self.trade_history),
            "win_rate": self._calculate_win_rate(),
        }

    def _calculate_win_rate(self) -> float:
        if not self.trade_history:
            return 0.0
        wins = sum(1 for t in self.trade_history if t["pnl"] > 0)
        return (wins / len(self.trade_history)) * 100

    def get_risk_report(self) -> dict:
        if not self.trade_history:
            return {"message": "Henuz islem gecmisi yok"}

        pnls = [t["pnl"] for t in self.trade_history]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        return {
            "total_trades": len(pnls),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": (len(wins) / len(pnls) * 100) if pnls else 0,
            "total_pnl": sum(pnls),
            "avg_win": np.mean(wins) if wins else 0,
            "avg_loss": np.mean(losses) if losses else 0,
            "profit_factor": abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else float("inf"),
            "max_consecutive_wins": self._max_consecutive(True),
            "max_consecutive_losses": self._max_consecutive(False),
            "daily_pnl": self.daily_pnl,
            "weekly_pnl": self.weekly_pnl,
        }

    def _max_consecutive(self, wins: bool) -> int:
        max_count = 0
        current = 0
        for trade in self.trade_history:
            if (trade["pnl"] > 0) == wins:
                current += 1
                max_count = max(max_count, current)
            else:
                current = 0
        return max_count
