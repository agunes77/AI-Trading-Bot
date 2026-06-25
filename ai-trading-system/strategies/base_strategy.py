import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from utils.logger import logger


class Signal:
    BUY = 1
    SELL = -1
    HOLD = 0


class BaseStrategy(ABC):
    def __init__(self, name: str, params: dict = None):
        self.name = name
        self.params = params or {}

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        pass

    def describe(self) -> str:
        param_str = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return f"{self.name}({param_str})"

    def _validate_df(self, df: pd.DataFrame, required_cols: list) -> bool:
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            logger.warning(f"{self.name}: Eksik kolonlar: {missing}")
            return False
        return True
