import pandas as pd
import numpy as np
import ta
from utils.logger import logger


class FeatureEngineer:
    def __init__(self):
        pass

    def add_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df = self._add_trend_indicators(df)
        df = self._add_momentum_indicators(df)
        df = self._add_volatility_indicators(df)
        df = self._add_volume_indicators(df)
        df = self._add_ichimoku(df)
        df = self._add_supertrend(df)
        df = self._add_parabolic_sar(df)
        df = self._add_pivot_points(df)
        df = self._add_advanced_ma(df)
        df = self._add_oscillators(df)
        df = self._add_price_features(df)
        df = self._add_statistical_features(df)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.fillna(method="ffill", inplace=True)
        df.fillna(0, inplace=True)
        return df

    def _add_trend_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df["sma_10"] = ta.trend.sma_indicator(df["close"], window=10)
        df["sma_20"] = ta.trend.sma_indicator(df["close"], window=20)
        df["sma_50"] = ta.trend.sma_indicator(df["close"], window=50)
        df["sma_200"] = ta.trend.sma_indicator(df["close"], window=200)
        df["ema_10"] = ta.trend.ema_indicator(df["close"], window=10)
        df["ema_20"] = ta.trend.ema_indicator(df["close"], window=20)
        df["ema_50"] = ta.trend.ema_indicator(df["close"], window=50)
        df["macd"] = ta.trend.macd(df["close"])
        df["macd_signal"] = ta.trend.macd_signal(df["close"])
        df["macd_diff"] = ta.trend.macd_diff(df["close"])
        df["adx"] = ta.trend.adx(df["high"], df["low"], df["close"])
        df["cci"] = ta.trend.cci(df["high"], df["low"], df["close"])
        return df

    def _add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df["rsi"] = ta.momentum.rsi(df["close"])
        df["stoch_k"] = ta.momentum.stoch(df["high"], df["low"], df["close"])
        df["stoch_d"] = ta.momentum.stoch_signal(df["high"], df["low"], df["close"])
        df["williams_r"] = ta.momentum.williams_r(df["high"], df["low"], df["close"])
        df["roc"] = ta.momentum.roc(df["close"])
        df["mfi"] = ta.volume.money_flow_index(df["high"], df["low"], df["close"], df["volume"])
        df["tsi"] = ta.momentum.tsi(df["close"])
        df["uo"] = ta.momentum.ultimate_oscillator(df["high"], df["low"], df["close"])
        return df

    def _add_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df["bb_high"] = ta.volatility.bollinger_hband(df["close"])
        df["bb_low"] = ta.volatility.bollinger_lband(df["close"])
        df["bb_mid"] = ta.volatility.bollinger_mavg(df["close"])
        df["bb_width"] = (df["bb_high"] - df["bb_low"]) / df["bb_mid"]
        df["bb_pct"] = (df["close"] - df["bb_low"]) / (df["bb_high"] - df["bb_low"])
        df["atr"] = ta.volatility.average_true_range(df["high"], df["low"], df["close"])
        df["keltner_high"] = ta.volatility.keltner_channel_hband(df["high"], df["low"], df["close"])
        df["keltner_low"] = ta.volatility.keltner_channel_lband(df["high"], df["low"], df["close"])
        df["dc_high"] = ta.volatility.donchian_channel_hband(df["close"])
        df["dc_low"] = ta.volatility.donchian_channel_lband(df["close"])
        df["dc_width"] = (df["dc_high"] - df["dc_low"]) / df["close"]
        return df

    def _add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df["obv"] = ta.volume.on_balance_volume(df["close"], df["volume"])
        df["vwap"] = (df["volume"] * (df["high"] + df["low"] + df["close"]) / 3).cumsum() / df["volume"].cumsum()
        df["volume_sma_20"] = df["volume"].rolling(window=20).mean()
        df["volume_ratio"] = df["volume"] / df["volume_sma_20"]
        df["cmf"] = ta.volume.chaikin_money_flow(df["high"], df["low"], df["close"], df["volume"])
        df["fi"] = ta.volume.force_index(df["close"], df["volume"])
        df["emv"] = ta.volume.ease_of_movement(df["high"], df["low"], df["volume"])
        return df

    def _add_ichimoku(self, df: pd.DataFrame) -> pd.DataFrame:
        high = df["high"]
        low = df["low"]
        close = df["close"]

        tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
        kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
        span_a = ((tenkan + kijun) / 2).shift(26)
        span_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
        chikou = close.shift(-26)

        df["ichimoku_conversion"] = tenkan
        df["ichimoku_base"] = kijun
        df["ichimoku_a"] = span_a
        df["ichimoku_b"] = span_b
        df["ichimoku_chikou"] = chikou
        df["ichimoku_cloud_top"] = np.maximum(span_a, span_b)
        df["ichimoku_cloud_bottom"] = np.minimum(span_a, span_b)
        df["ichimoku_cloud_width"] = df["ichimoku_cloud_top"] - df["ichimoku_cloud_bottom"]
        return df

    def _add_supertrend(self, df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
        hl2 = (df["high"] + df["low"]) / 2
        atr = ta.volatility.average_true_range(df["high"], df["low"], df["close"], window=period)

        upper_band = hl2 + multiplier * atr
        lower_band = hl2 - multiplier * atr

        supertrend = pd.Series(np.nan, index=df.index, dtype=float)
        direction = pd.Series(1, index=df.index, dtype=int)

        supertrend.iloc[0] = upper_band.iloc[0]

        for i in range(1, len(df)):
            if df["close"].iloc[i] > supertrend.iloc[i - 1]:
                direction.iloc[i] = 1
            else:
                direction.iloc[i] = -1

            if direction.iloc[i] == 1:
                supertrend.iloc[i] = max(lower_band.iloc[i], supertrend.iloc[i - 1]) if direction.iloc[i - 1] == 1 else lower_band.iloc[i]
            else:
                supertrend.iloc[i] = min(upper_band.iloc[i], supertrend.iloc[i - 1]) if direction.iloc[i - 1] == -1 else upper_band.iloc[i]

        df["supertrend"] = supertrend
        df["supertrend_dir"] = direction
        df["supertrend_dist"] = (df["close"] - supertrend) / df["close"]
        return df

    def _add_parabolic_sar(self, df: pd.DataFrame, af_start: float = 0.02, af_step: float = 0.02, af_max: float = 0.2) -> pd.DataFrame:
        high = df["high"].values
        low = df["low"].values
        close = df["close"].values
        n = len(df)

        psar = np.full(n, np.nan)
        psar_dir = np.ones(n, dtype=int)

        trend = 1
        ep = low[0]
        hp = high[0]
        af = af_start
        psar[0] = low[0]

        for i in range(1, n):
            prev_psar = psar[i - 1]

            if trend == 1:
                psar[i] = prev_psar + af * (hp - prev_psar)
                if low[i] < psar[i]:
                    trend = -1
                    psar[i] = hp
                    ep = low[i]
                    af = af_start
                else:
                    if high[i] > hp:
                        hp = high[i]
                        af = min(af + af_step, af_max)
                    psar[i] = min(psar[i], low[i - 1]) if i >= 2 else psar[i]
                    psar[i] = min(psar[i], low[i - 2]) if i >= 3 else psar[i]
            else:
                psar[i] = prev_psar + af * (ep - prev_psar)
                if high[i] > psar[i]:
                    trend = 1
                    psar[i] = ep
                    hp = high[i]
                    af = af_start
                else:
                    if low[i] < ep:
                        ep = low[i]
                        af = min(af + af_step, af_max)
                    psar[i] = max(psar[i], high[i - 1]) if i >= 2 else psar[i]
                    psar[i] = max(psar[i], high[i - 2]) if i >= 3 else psar[i]

            psar_dir[i] = trend

        df["psar"] = psar
        df["psar_dir"] = psar_dir
        return df

    def _add_pivot_points(self, df: pd.DataFrame) -> pd.DataFrame:
        high = df["high"]
        low = df["low"]
        close = df["close"]

        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        r3 = high + 2 * (pivot - low)
        s3 = low - 2 * (high - pivot)

        df["pivot"] = pivot
        df["pivot_r1"], df["pivot_r2"], df["pivot_r3"] = r1, r2, r3
        df["pivot_s1"], df["pivot_s2"], df["pivot_s3"] = s1, s2, s3
        df["pivot_dist"] = (close - pivot) / pivot
        return df

    def _add_advanced_ma(self, df: pd.DataFrame) -> pd.DataFrame:
        close = df["close"]
        ema_10 = ta.trend.ema_indicator(close, window=10)
        ema_20 = ta.trend.ema_indicator(close, window=20)
        df["dema_10"] = 2 * ema_10 - ta.trend.ema_indicator(ema_10, window=10)
        df["dema_20"] = 2 * ema_20 - ta.trend.ema_indicator(ema_20, window=20)

        ema_10_v = ta.trend.ema_indicator(close, window=10)
        df["tema_10"] = 3 * ema_10_v - 3 * ta.trend.ema_indicator(ema_10_v, window=10) + ta.trend.ema_indicator(ta.trend.ema_indicator(ema_10_v, window=10), window=10)

        df["wma_10"] = close.rolling(10).apply(lambda x: np.dot(x, np.arange(1, 11)) / np.arange(1, 11).sum(), raw=True)
        df["wma_20"] = close.rolling(20).apply(lambda x: np.dot(x, np.arange(1, 21)) / np.arange(1, 21).sum(), raw=True)

        df["hma_20"] = self._hull_moving_average(close, 20)
        return df

    def _hull_moving_average(self, series: pd.Series, period: int) -> pd.Series:
        half = int(period / 2)
        sqrt = int(np.sqrt(period))
        wma_half = series.rolling(half).mean()
        wma_full = series.rolling(period).mean()
        raw = 2 * wma_half - wma_full
        return raw.rolling(sqrt).mean()

    def _add_oscillators(self, df: pd.DataFrame) -> pd.DataFrame:
        close = df["close"]
        high = df["high"]
        low = df["low"]

        ema_fast = ta.trend.ema_indicator(close, window=5)
        ema_slow = ta.trend.ema_indicator(close, window=34)
        df["ao"] = ema_fast - ema_slow

        df["kst"] = (
            ta.momentum.roc(close, 10).rolling(10).mean() * 1 +
            ta.momentum.roc(close, 15).rolling(10).mean() * 2 +
            ta.momentum.roc(close, 20).rolling(10).mean() * 3 +
            ta.momentum.roc(close, 30).rolling(15).mean() * 4
        )

        df["dpo"] = close - close.shift(int((20 / 2) + 1)).rolling(20).mean()

        df["trix"] = ta.trend.trix(close, window=15)

        df["detrended_rsi"] = ta.momentum.rsi(close) - ta.momentum.rsi(close).rolling(10).mean()

        df["connors_rsi"] = (
            ta.momentum.rsi(close) +
            ta.momentum.rsi(close.pct_change()) +
            close.pct_change().rolling(100).apply(lambda x: pd.Series(x).rank(pct=True).iloc[-1], raw=False) * 100
        ) / 3
        return df

    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df["returns"] = df["close"].pct_change()
        df["log_returns"] = np.log(df["close"] / df["close"].shift(1))
        df["high_low_range"] = (df["high"] - df["low"]) / df["close"]
        df["close_open_range"] = (df["close"] - df["open"]) / df["open"]
        df["upper_shadow"] = (df["high"] - df[["open", "close"]].max(axis=1)) / df["close"]
        df["lower_shadow"] = (df[["open", "close"]].min(axis=1) - df["low"]) / df["close"]
        df["close_to_sma20"] = (df["close"] - df["sma_20"]) / df["sma_20"]
        df["close_to_sma50"] = (df["close"] - df["sma_50"]) / df["sma_50"]
        df["close_to_sma200"] = (df["close"] - df["sma_200"]) / df["sma_200"]
        return df

    def _add_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        for w in [5, 10, 20]:
            df[f"volatility_{w}"] = df["returns"].rolling(window=w).std()
            df[f"skewness_{w}"] = df["returns"].rolling(window=w).skew()
            df[f"kurtosis_{w}"] = df["returns"].rolling(window=w).kurt()
        return df

    def get_feature_columns(self) -> list:
        return [
            "sma_10", "sma_20", "sma_50", "sma_200",
            "ema_10", "ema_20", "ema_50",
            "macd", "macd_signal", "macd_diff", "adx", "cci",
            "rsi", "stoch_k", "stoch_d", "williams_r", "roc", "mfi", "tsi", "uo",
            "bb_width", "bb_pct", "atr", "dc_width",
            "obv", "volume_ratio", "cmf", "fi",
            "ichimoku_conversion", "ichimoku_base", "ichimoku_a", "ichimoku_b",
            "ichimoku_cloud_width",
            "supertrend", "supertrend_dir", "supertrend_dist",
            "psar", "psar_dir",
            "pivot", "pivot_r1", "pivot_s1", "pivot_dist",
            "dema_10", "dema_20", "tema_10", "wma_10", "wma_20",
            "ao", "kst", "dpo", "trix",
            "returns", "log_returns", "high_low_range", "close_open_range",
            "upper_shadow", "lower_shadow",
            "close_to_sma20", "close_to_sma50", "close_to_sma200",
            "volatility_5", "volatility_10", "volatility_20",
            "skewness_5", "skewness_10", "skewness_20",
            "kurtosis_5", "kurtosis_10", "kurtosis_20",
        ]
