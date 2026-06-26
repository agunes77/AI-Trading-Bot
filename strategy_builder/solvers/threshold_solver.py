import pandas as pd
from strategy_builder.solvers.base_solver import BaseSolver


class ThresholdSolver(BaseSolver):
    id = "threshold"
    name = "Threshold"
    category = "Confidence Solver"
    description = "Bir değerin eşiğin üstünde/altında olmasına göre skor üretir. Aşan kısmın büyüklüğüne göre skor artar."
    inputs = [{"id": "value", "name": "Değer", "type": "series"}]
    parameters = {"threshold": 50, "condition": "above", "scale": 10}

    def calculate(self, data: pd.DataFrame, inputs: Dict[str, Any]) -> pd.Series:
        val = inputs.get("value", data["close"])
        threshold = self.params.get("threshold", 50)
        condition = self.params.get("condition", "above")
        scale = self.params.get("scale", 10)

        if condition == "above":
            score = ((val - threshold) / scale).clip(0, 100)
        else:
            score = ((threshold - val) / scale).clip(0, 100)
            
        return score.fillna(0)