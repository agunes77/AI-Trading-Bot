import pandas as pd
import numpy as np
from typing import Dict, Any, Optional


class BaseSolver:
    """Tüm solver'ların base class'ı. 0-100 arası confidence score döndürür."""
    
    id: str = "base"
    name: str = "Base Solver"
    category: str = "Confidence Solver"
    description: str = "Base solver class"
    inputs: list = []
    outputs: list = [{"id": "score", "name": "Score (0-100)", "type": "score"}]
    parameters: dict = {}
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        self.params = params or self.parameters.copy()
    
    def calculate(self, data: pd.DataFrame, inputs: Dict[str, Any]) -> pd.Series:
        """0-100 arası confidence score serisi döndürür."""
        raise NotImplementedError("Subclass must implement calculate()")
    
    def _to_score(self, condition_series: pd.Series) -> pd.Series:
        """Boolean seriyi 0-100 score'a dönüştürür (True=100, False=0)."""
        return condition_series.astype(float) * 100.0
    
    def _normalize(self, series: pd.Series, min_val: float = 0, max_val: float = 100) -> pd.Series:
        """Değerleri 0-100 arasına normalize et."""
        series = series.replace([np.inf, -np.inf], np.nan).fillna(0)
        s_min, s_max = series.min(), series.max()
        if s_max == s_min:
            return pd.Series(50.0, index=series.index)
        normalized = 100 * (series - s_min) / (s_max - s_min)
        return normalized.clip(0, 100)