import pandas as pd
import numpy as np
from strategy_builder.solvers.base_solver import BaseSolver


class ChangeInSlopeSolver(BaseSolver):
    id = "change_in_slope"
    name = "Change in Slope (Momentum Dönüşü)"
    category = "Confidence Solver"
    description = "İndikatörün eğiminin (1. türev) yön değiştirmesi. Momentum dönüşü tespiti."
    inputs = [{"id": "series", "name": "Seri/İndikatör", "type": "series"}]
    parameters = {"lookback": 2, "confirmation_bars": 1}

    def calculate(self, data: pd.DataFrame, inputs: Dict[str, Any]) -> pd.Series:
        series = inputs.get("series", data["close"])
        lookback = self.params.get("lookback", 2)
        
        # İkinci türev (eğimin eğimi)
        first_deriv = series.diff(lookback)
        second_deriv = first_deriv.diff(lookback)
        
        # Yön değişimi: 2. türevin pozitif olması = alttan üste dönüş
        direction_change_up = (second_deriv > 0) & (first_deriv.shift(lookback) < 0)
        direction_change_down = (second_deriv < 0) & (first_deriv.shift(lookback) > 0)
        
        score = pd.Series(50.0, index=data.index)
        score = score.where(~direction_change_up, 100.0)
        score = score.where(~direction_change_down, 0.0)
        
        # Yumuşatma
        score = score.clip(0, 100)
        return score.fillna(50)