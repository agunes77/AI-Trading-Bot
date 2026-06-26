import pandas as pd
from typing import Dict, Any
import numpy as np
from strategy_builder.solvers.base_solver import BaseSolver


class BollingerSqueezeSolver(BaseSolver):
    id = "bb_squeeze"
    name = "Expansion / Contraction"
    category = "Confidence Solver"
    description = "Volatilitenin (Bollinger genişliği) genişlemesi veya daralması (squeeze)."
    inputs = []
    parameters = {"bb_period": 20, "mode": "squeeze", "threshold_percentile": 20}

    def calculate(self, data: pd.DataFrame, inputs: Dict[str, Any]) -> pd.Series:
        period = self.params.get("bb_period", 20)
        mode = self.params.get("mode", "squeeze")
        pct_threshold = self.params.get("threshold_percentile", 20)

        sma = data["close"].rolling(window=period).mean()
        std = data["close"].rolling(window=period).std()
        width = (sma + 2 * std) - (sma - 2 * std)

        # Genişliği percentile ile değerlendir
        rolling_pct = width.rolling(window=period * 5).rank(pct=True) * 100

        if mode == "squeeze":
            # Squeeze durumunda (daralma) skor yüksek
            score = (100 - rolling_pct).clip(0, 100)
        else:  # expansion
            score = rolling_pct.clip(0, 100)
            
        return score.fillna(50)