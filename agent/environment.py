import numpy as np
import pandas as pd
import gymnasium as gym
from gymnasium import spaces
from utils.logger import logger
from config.settings import RISK_CONFIG


class TradingEnvironment(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        df: pd.DataFrame,
        feature_columns: list,
        initial_balance: float = 10000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
        render_mode: str = None,
    ):
        super().__init__()
        self.df = df.reset_index(drop=True)
        self.feature_columns = feature_columns
        self.initial_balance = initial_balance
        self.commission = commission
        self.slippage = slippage
        self.render_mode = render_mode

        self.n_features = len(feature_columns)
        self.action_space = spaces.Discrete(3)
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(self.n_features + 4,), dtype=np.float64
        )

        self.max_position_pct = RISK_CONFIG["max_position_pct"]
        self.stop_loss_pct = RISK_CONFIG["stop_loss_pct"]
        self.take_profit_pct = RISK_CONFIG["take_profit_pct"]

        self._reset_state()

    def _reset_state(self):
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0
        self.entry_price = 0.0
        self.shares_held = 0.0
        self.total_asset = self.initial_balance
        self.trade_log = []
        self.equity_curve = [self.initial_balance]
        self.daily_pnl = 0.0
        self.max_equity = self.initial_balance
        self.consecutive_losses = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self._reset_state()
        return self._get_obs(), self._get_info()

    def _get_obs(self):
        row = self.df.iloc[self.current_step]
        features = row[self.feature_columns].values.astype(np.float64)
        position_info = np.array([
            self.position,
            self.balance / self.initial_balance,
            self.total_asset / self.initial_balance,
            self.consecutive_losses / 10.0,
        ], dtype=np.float64)
        return np.concatenate([features, position_info])

    def _get_info(self):
        return {
            "step": self.current_step,
            "balance": self.balance,
            "total_asset": self.total_asset,
            "position": self.position,
            "equity_curve": self.equity_curve.copy(),
        }

    def step(self, action: int):
        current_price = self.df.iloc[self.current_step]["close"]
        prev_total = self.total_asset

        self._execute_action(action, current_price)
        self._check_stop_conditions(current_price)

        self.total_asset = self.balance + self.shares_held * current_price
        self.equity_curve.append(self.total_asset)

        reward = self._calculate_reward(prev_total, current_price)

        self.current_step += 1
        terminated = self.current_step >= len(self.df) - 1
        truncated = self.total_asset < self.initial_balance * 0.5

        if terminated:
            self._close_position(current_price, reason="episode_end")

        return self._get_obs(), reward, terminated, truncated, self._get_info()

    def _execute_action(self, action: int, price: float):
        if action == 1 and self.position == 0:
            self._open_long(price)
        elif action == 2 and self.position == 1:
            self._close_position(price, reason="sell_signal")
        elif action == 0:
            pass

    def _open_long(self, price: float):
        exec_price = price * (1 + self.slippage)
        risk_amount = self.balance * self.max_position_pct
        cost = risk_amount * (1 + self.commission)
        if cost > self.balance:
            return
        self.shares_held = risk_amount / exec_price
        self.balance -= cost
        self.entry_price = exec_price
        self.position = 1
        self.trade_log.append({
            "step": self.current_step, "action": "buy",
            "price": exec_price, "shares": self.shares_held,
        })

    def _close_position(self, price: float, reason: str = ""):
        if self.position == 0:
            return
        exec_price = price * (1 - self.slippage)
        revenue = self.shares_held * exec_price
        commission_cost = revenue * self.commission
        self.balance += revenue - commission_cost
        pnl = (exec_price - self.entry_price) / self.entry_price
        self.trade_log.append({
            "step": self.current_step, "action": "sell",
            "price": exec_price, "shares": self.shares_held,
            "pnl_pct": pnl, "reason": reason,
        })
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        self.shares_held = 0.0
        self.entry_price = 0.0
        self.position = 0

    def _check_stop_conditions(self, price: float):
        if self.position == 1:
            pnl_pct = (price - self.entry_price) / self.entry_price
            if pnl_pct <= -self.stop_loss_pct:
                self._close_position(price, reason="stop_loss")
            elif pnl_pct >= self.take_profit_pct:
                self._close_position(price, reason="take_profit")

    def _calculate_reward(self, prev_total: float, current_price: float) -> float:
        current_total = self.balance + self.shares_held * current_price
        step_return = (current_total - prev_total) / prev_total

        unrealized_pnl = 0.0
        if self.position == 1:
            unrealized_pnl = (current_price - self.entry_price) / self.entry_price

        drawdown = 0.0
        if current_total > self.max_equity:
            self.max_equity = current_total
        if self.max_equity > 0:
            drawdown = (self.max_equity - current_total) / self.max_equity

        reward = step_return * 100.0
        reward += unrealized_pnl * 5.0
        reward -= drawdown * 10.0
        reward -= 0.01

        if self.consecutive_losses >= 3:
            reward -= 1.0

        return float(np.clip(reward, -10.0, 10.0))

    def get_performance(self) -> dict:
        equity = np.array(self.equity_curve)
        if len(equity) < 2:
            return {}
        returns = np.diff(equity) / equity[:-1]
        total_trades = len([t for t in self.trade_log if t["action"] == "sell"])
        winning_trades = len([t for t in self.trade_log if t["action"] == "sell" and t.get("pnl_pct", 0) > 0])
        return {
            "total_return_pct": (equity[-1] - equity[0]) / equity[0] * 100,
            "max_drawdown_pct": (1 - equity / np.maximum.accumulate(equity)).max() * 100,
            "sharpe_ratio": np.sqrt(252) * returns.mean() / (returns.std() + 1e-10),
            "total_trades": total_trades,
            "win_rate_pct": (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            "final_balance": equity[-1],
        }
