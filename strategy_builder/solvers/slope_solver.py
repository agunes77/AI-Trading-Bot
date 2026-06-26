import pandas as pd
import numpy as np
from strategy_builder.solvers.base_solver import BaseSolver


class SlopeSolver(BaseSolver):
    id = "slope"
    name = "Slope (Trend Gücü)"
    category = "Confidence Solver"
    description = "Serinin N barlık eğimini hesaplar. Eğim pozitif/negatif gücüne göre 0-100 skor verir."
    inputs = [{"id": "series", "name": "Seri", "type": "series"}]
    parameters = {"period": 5, "direction": "up", "sensitivity": 1.0}

    def calculate(self, data: pd.DataFrame, inputs: Dict[str, Any]) -> pd.Series:
        series = inputs.get("series", data["close"])
        period = self.params.get("period", 5)
        direction = self.params.get("direction", "up")
        sensitivity = self.params.get("sensitivity", 1.0)

        slope = series.diff(period) / series.shift(period)
        slope = slope.replace([np.inf, -np.inf], np.nan).fillna(0)

        if direction == "up":
            score = (slope * 1000 * sensitivity).clip(0, 100)
        else:
            score = (-slope * 1000 * sensitivity).clip(0, 100)
            
        return score