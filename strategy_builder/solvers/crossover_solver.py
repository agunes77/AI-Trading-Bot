import pandas as pd
from typing import Dict, Any
from strategy_builder.solvers.base_solver import BaseSolver


class CrossoverSolver(BaseSolver):
    id = "crossover"
    name = "Crossover (Golden/Death Cross)"
    category = "Confidence Solver"
    description = "İki serinin kesişimine göre 0-100 skor üretir. Kesişim yönüne göre %100, karşı yönde %0."
    inputs = [
        {"id": "series1", "name": "Seri 1 (Fast)", "type": "series"},
        {"id": "series2", "name": "Seri 2 (Slow)", "type": "series"}
    ]
    parameters = {"direction": "above"}  # "above" (yukarı kes) veya "below" (aşağı kes)

    def calculate(self, data: pd.DataFrame, inputs: Dict[str, Any]) -> pd.Series:
        s1 = inputs.get("series1", data["close"])
        s2 = inputs.get("series2", data["close"])
        direction = self.params.get("direction", "above")

        if direction == "above":
            cross = (s1 > s2) & (s1.shift(1) <= s2.shift(1))
        else:
            cross = (s1 < s2) & (s1.shift(1) >= s2.shift(1))
            
        # Kesişim olduğu barlarda 100, kesişim sonrası s1 > s2 olduğu sürece gradual skor
        if direction == "above":
            score = (s1 > s2).astype(float) * 100
        else:
            score = (s1 < s2).astype(float) * 100
            
        # Kesişim noktalarını max yap
        score = score.where(~cross, 100.0)
        return score.fillna(0)