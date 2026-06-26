import pandas as pd
import numpy as np
from strategy_builder.solvers.base_solver import BaseSolver


class BarDirectionSolver(BaseSolver):
    id = "bar_direction"
    name = "Bar Direction"
    category = "Confidence Solver"
    description = "Son N barın yön (yukarı/aşağı) oranına göre güven skoru üretir."
    inputs = []
    parameters = {"lookback": 5, "direction": "up"}

    def calculate(self, data: pd.DataFrame, inputs: Dict[str, Any]) -> pd.Series:
        lookback = self.params.get("lookback", 5)
        direction = self.params.get("direction", "up")

        is_up = data["close"] > data["open"]
        
        if direction == "up":
            trend_strength = is_up.rolling(window=lookback).mean() * 100
        else:
            trend_strength = (~is_up).rolling(window=lookback).mean() * 100
            
        return trend_strength.fillna(50)