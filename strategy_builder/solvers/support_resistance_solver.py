import pandas as pd
import numpy as np
from strategy_builder.solvers.base_solver import BaseSolver


class SupportResistanceSolver(BaseSolver):
    id = "support_resistance"
    name = "Support / Resistance"
    category = "Confidence Solver"
    description = "Fiyatın bilinen S/R seviyelerine yakınlığı. Destek yakınında alış, direnç yakınında satış skoru."
    inputs = []
    parameters = {"lookback": 50, "proximity_pct": 1.0, "mode": "support"}

    def calculate(self, data: pd.DataFrame, inputs: Dict[str, Any]) -> pd.Series:
        lookback = self.params.get("lookback", 50)
        proximity_pct = self.params.get("proximity_pct", 1.0) / 100.0
        mode = self.params.get("mode", "support")

        high = data["high"]
        low = data["low"]
        close = data["close"]
        
        # Son N bardaki en yüksek/düşük
        recent_high = high.rolling(window=lookback).max()
        recent_low = low.rolling(window=lookback).min()
        
        score = pd.Series(0.0, index=data.index)
        
        if mode == "support":
            # Fiyat destek seviyesine yaklaştıkça skor artar
            distance = (close - recent_low) / close
            # 0'a yakın = tam destek, max skor
            score = (1.0 - (distance / proximity_pct).clip(0, 1)) * 100
        else:  # resistance
            # Fiyat direnç seviyesine yaklaştıkça (satış sinyali için) skor artar
            distance = (recent_high - close) / close
            score = (1.0 - (distance / proximity_pct).clip(0, 1)) * 100
            
        return score.fillna(0).clip(0, 100)