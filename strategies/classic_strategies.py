import pandas as pd
import numpy as np
from strategies.base_strategy import BaseStrategy, Signal


class SMACrossover(BaseStrategy):
    def __init__(self, fast: int = 10, slow: int = 50):
        super().__init__("SMA_Crossover", {"fast": fast, "slow": slow})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        fast = df[f"sma_{self.params['fast']}"]
        slow = df[f"sma_{self.params['slow']}"]
        signals = pd.Series(Signal.HOLD, index=df.index)
        signals[(fast > slow) & (fast.shift(1) <= slow.shift(1))] = Signal.BUY
        signals[(fast < slow) & (fast.shift(1) >= slow.shift(1))] = Signal.SELL
        return signals


class EMACrossover(BaseStrategy):
    def __init__(self, fast: int = 12, slow: int = 26):
        super().__init__("EMA_Crossover", {"fast": fast, "slow": slow})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        fast = df[f"ema_{self.params['fast']}"]
        slow = df[f"ema_{self.params['slow']}"]
        signals = pd.Series(Signal.HOLD, index=df.index)
        signals[(fast > slow) & (fast.shift(1) <= slow.shift(1))] = Signal.BUY
        signals[(fast < slow) & (fast.shift(1) >= slow.shift(1))] = Signal.SELL
        return signals


class GoldenCrossDeathCross(BaseStrategy):
    def __init__(self):
        super().__init__("GoldenCross_DeathCross", {"fast": 50, "slow": 200})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        fast = df["sma_50"]
        slow = df["sma_200"]
        signals = pd.Series(Signal.HOLD, index=df.index)
        signals[(fast > slow) & (fast.shift(1) <= slow.shift(1))] = Signal.BUY
        signals[(fast < slow) & (fast.shift(1) >= slow.shift(1))] = Signal.SELL
        return signals


class RSIOversoldOverbought(BaseStrategy):
    def __init__(self, oversold: float = 30, overbought: float = 70):
        super().__init__("RSI_OB_OS", {"oversold": oversold, "overbought": overbought})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        rsi = df["rsi"]
        signals = pd.Series(Signal.HOLD, index=df.index)
        signals[(rsi < self.params["oversold"]) & (rsi.shift(1) >= self.params["oversold"])] = Signal.BUY
        signals[(rsi > self.params["overbought"]) & (rsi.shift(1) <= self.params["overbought"])] = Signal.SELL
        return signals


class RSIDivergence(BaseStrategy):
    def __init__(self, lookback: int = 14):
        super().__init__("RSI_Divergence", {"lookback": lookback})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        rsi = df["rsi"]
        close = df["close"]
        lb = self.params["lookback"]
        signals = pd.Series(Signal.HOLD, index=df.index)

        for i in range(lb, len(df)):
            price_window = close.iloc[i - lb:i]
            rsi_window = rsi.iloc[i - lb:i]

            price_lower_low = close.iloc[i] < price_window.min()
            rsi_higher_low = rsi.iloc[i] > rsi_window.min()
            if price_lower_low and rsi_higher_low and rsi.iloc[i] < 40:
                signals.iloc[i] = Signal.BUY

            price_higher_high = close.iloc[i] > price_window.max()
            rsi_lower_high = rsi.iloc[i] < rsi_window.max()
            if price_higher_high and rsi_lower_high and rsi.iloc[i] > 60:
                signals.iloc[i] = Signal.SELL

        return signals


class MACDCrossover(BaseStrategy):
    def __init__(self):
        super().__init__("MACD_Crossover", {})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        macd = df["macd"]
        signal = df["macd_signal"]
        signals = pd.Series(Signal.HOLD, index=df.index)
        signals[(macd > signal) & (macd.shift(1) <= signal.shift(1))] = Signal.BUY
        signals[(macd < signal) & (macd.shift(1) >= signal.shift(1))] = Signal.SELL
        return signals


class MACDHistogramReversal(BaseStrategy):
    def __init__(self):
        super().__init__("MACD_Hist_Reversal", {})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        hist = df["macd_diff"]
        signals = pd.Series(Signal.HOLD, index=df.index)
        signals[(hist > 0) & (hist.shift(1) <= 0)] = Signal.BUY
        signals[(hist < 0) & (hist.shift(1) >= 0)] = Signal.SELL
        return signals


class BollingerBandSqueeze(BaseStrategy):
    def __init__(self, squeeze_threshold: float = 0.03):
        super().__init__("BB_Squeeze", {"squeeze_threshold": squeeze_threshold})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        bb_width = df["bb_width"]
        close = df["close"]
        bb_low = df["bb_low"]
        bb_high = df["bb_high"]
        threshold = self.params["squeeze_threshold"]
        signals = pd.Series(Signal.HOLD, index=df.index)

        squeeze = bb_width < bb_width.rolling(20).quantile(0.2)
        breakout_up = (close > bb_high) & (close.shift(1) <= bb_high.shift(1))
        breakout_down = (close < bb_low) & (close.shift(1) >= bb_low.shift(1))

        signals[squeeze.shift(1) & breakout_up] = Signal.BUY
        signals[squeeze.shift(1) & breakout_down] = Signal.SELL
        return signals


class BollingerBandBounce(BaseStrategy):
    def __init__(self):
        super().__init__("BB_Bounce", {})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        bb_pct = df["bb_pct"]
        signals = pd.Series(Signal.HOLD, index=df.index)
        signals[(bb_pct < 0.05) & (bb_pct.shift(1) >= 0.05)] = Signal.BUY
        signals[(bb_pct > 0.95) & (bb_pct.shift(1) <= 0.95)] = Signal.SELL
        return signals


class IchimokuCloud(BaseStrategy):
    def __init__(self):
        super().__init__("Ichimoku_Cloud", {})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(Signal.HOLD, index=df.index)
        if not all(c in df.columns for c in ["ichimoku_a", "ichimoku_b", "ichimoku_base"]):
            return signals
        span_a = df["ichimoku_a"]
        span_b = df["ichimoku_b"]
        base = df["ichimoku_base"]
        close = df["close"]

        cloud_support = span_a > span_b
        above_cloud = close > span_a
        below_cloud = close < span_b
        cross_up = (close > base) & (close.shift(1) <= base.shift(1))
        cross_down = (close < base) & (close.shift(1) >= base.shift(1))

        signals[above_cloud & cloud_support & cross_up] = Signal.BUY
        signals[below_cloud & cross_down] = Signal.SELL
        return signals


class SupertrendStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Supertrend", {})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(Signal.HOLD, index=df.index)
        if "supertrend" not in df.columns or "supertrend_dir" not in df.columns:
            return signals
        st_dir = df["supertrend_dir"]
        signals[(st_dir == 1) & (st_dir.shift(1) == -1)] = Signal.BUY
        signals[(st_dir == -1) & (st_dir.shift(1) == 1)] = Signal.SELL
        return signals


class ParabolicSARStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Parabolic_SAR", {})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(Signal.HOLD, index=df.index)
        if "psar" not in df.columns:
            return signals
        psar = df["psar"]
        close = df["close"]
        was_below = (close.shift(1) < psar.shift(1))
        was_above = (close.shift(1) > psar.shift(1))
        is_above = close > psar
        is_below = close < psar
        signals[was_below & is_above] = Signal.BUY
        signals[was_above & is_below] = Signal.SELL
        return signals


class VWAPStrategy(BaseStrategy):
    def __init__(self, std_multiplier: float = 1.5):
        super().__init__("VWAP", {"std_multiplier": std_multiplier})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(Signal.HOLD, index=df.index)
        if "vwap" not in df.columns:
            return signals
        vwap = df["vwap"]
        close = df["close"]
        std = close.rolling(20).std()
        upper = vwap + self.params["std_multiplier"] * std
        lower = vwap - self.params["std_multiplier"] * std
        signals[(close < lower) & (close.shift(1) >= lower.shift(1))] = Signal.BUY
        signals[(close > upper) & (close.shift(1) <= upper.shift(1))] = Signal.SELL
        return signals


class ATRBreakout(BaseStrategy):
    def __init__(self, multiplier: float = 2.0, lookback: int = 20):
        super().__init__("ATR_Breakout", {"multiplier": multiplier, "lookback": lookback})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(Signal.HOLD, index=df.index)
        atr = df["atr"]
        close = df["close"]
        lb = self.params["lookback"]
        mult = self.params["multiplier"]
        upper_band = close.rolling(lb).mean() + mult * atr
        lower_band = close.rolling(lb).mean() - mult * atr
        signals[(close > upper_band) & (close.shift(1) <= upper_band.shift(1))] = Signal.BUY
        signals[(close < lower_band) & (close.shift(1) >= lower_band.shift(1))] = Signal.SELL
        return signals


class StochasticCrossover(BaseStrategy):
    def __init__(self, oversold: float = 20, overbought: float = 80):
        super().__init__("Stochastic_Cross", {"oversold": oversold, "overbought": overbought})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        stoch_k = df["stoch_k"]
        stoch_d = df["stoch_d"]
        signals = pd.Series(Signal.HOLD, index=df.index)
        buy_cond = (stoch_k > stoch_d) & (stoch_k.shift(1) <= stoch_d.shift(1)) & (stoch_k < self.params["oversold"] + 10)
        sell_cond = (stoch_k < stoch_d) & (stoch_k.shift(1) >= stoch_d.shift(1)) & (stoch_k > self.params["overbought"] - 10)
        signals[buy_cond] = Signal.BUY
        signals[sell_cond] = Signal.SELL
        return signals


class PivotPointStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Pivot_Points", {})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(Signal.HOLD, index=df.index)
        if "pivot" not in df.columns:
            return signals
        pivot = df["pivot"]
        s1 = df["pivot_s1"]
        r1 = df["pivot_r1"]
        close = df["close"]
        signals[(close < s1) & (close.shift(1) >= s1.shift(1))] = Signal.BUY
        signals[(close > r1) & (close.shift(1) <= r1.shift(1))] = Signal.SELL
        return signals


class FibonacciRetracement(BaseStrategy):
    def __init__(self, lookback: int = 50, entry_level: float = 0.618):
        super().__init__("Fibonacci_Retracement", {"lookback": lookback, "entry_level": entry_level})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(Signal.HOLD, index=df.index)
        close = df["close"]
        lb = self.params["lookback"]
        level = self.params["entry_level"]

        for i in range(lb, len(df)):
            window = close.iloc[i - lb:i]
            high = window.max()
            low = window.min()
            diff = high - low
            if diff == 0:
                continue
            fib_618 = high - diff * level
            fib_382 = low + diff * (1 - level)
            current = close.iloc[i]
            prev = close.iloc[i - 1]
            if prev <= fib_618 and current > fib_618 and current < high * 0.98:
                signals.iloc[i] = Signal.BUY
            elif prev >= fib_382 and current < fib_382 and current > low * 1.02:
                signals.iloc[i] = Signal.SELL

        return signals


class TripleScreenElder(BaseStrategy):
    def __init__(self):
        super().__init__("Triple_Screen_Elder", {})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(Signal.HOLD, index=df.index)
        if not all(c in df.columns for c in ["ema_50", "sma_200", "macd_diff", "stoch_k"]):
            return signals

        trend_up = df["ema_50"] > df["sma_200"]
        trend_down = df["ema_50"] < df["sma_200"]
        macd_bullish = df["macd_diff"] > 0
        macd_bearish = df["macd_diff"] < 0
        stoch_oversold = df["stoch_k"] < 30
        stoch_overbought = df["stoch_k"] > 70

        signals[trend_up & macd_bullish & stoch_oversold] = Signal.BUY
        signals[trend_down & macd_bearish & stoch_overbought] = Signal.SELL
        return signals


class TurtleTrading(BaseStrategy):
    def __init__(self, entry_period: int = 20, exit_period: int = 10):
        super().__init__("Turtle_Trading", {"entry_period": entry_period, "exit_period": exit_period})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(Signal.HOLD, index=df.index)
        high = df["high"]
        low = df["low"]
        close = df["close"]
        ep = self.params["entry_period"]
        xp = self.params["exit_period"]

        entry_high = high.rolling(ep).max()
        entry_low = low.rolling(ep).min()
        exit_high = high.rolling(xp).max()
        exit_low = low.rolling(xp).min()

        signals[(close > entry_high.shift(1)) & (close.shift(1) <= entry_high.shift(2))] = Signal.BUY
        signals[(close < entry_low.shift(1)) & (close.shift(1) >= entry_low.shift(2))] = Signal.SELL
        return signals


class MeanReversion(BaseStrategy):
    def __init__(self, lookback: int = 20, entry_z: float = 2.0, exit_z: float = 0.5):
        super().__init__("Mean_Reversion", {"lookback": lookback, "entry_z": entry_z, "exit_z": exit_z})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(Signal.HOLD, index=df.index)
        close = df["close"]
        lb = self.params["lookback"]
        entry_z = self.params["entry_z"]

        sma = close.rolling(lb).mean()
        std = close.rolling(lb).std()
        z_score = (close - sma) / (std + 1e-10)

        signals[(z_score < -entry_z) & (z_score.shift(1) >= -entry_z)] = Signal.BUY
        signals[(z_score > entry_z) & (z_score.shift(1) <= entry_z)] = Signal.SELL
        return signals


class ADXTrendStrength(BaseStrategy):
    def __init__(self, adx_threshold: float = 25):
        super().__init__("ADX_Trend", {"adx_threshold": adx_threshold})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(Signal.HOLD, index=df.index)
        adx = df["adx"]
        ema_10 = df["ema_10"]
        ema_20 = df["ema_20"]
        threshold = self.params["adx_threshold"]

        strong_trend = adx > threshold
        buy_cross = (ema_10 > ema_20) & (ema_10.shift(1) <= ema_20.shift(1))
        sell_cross = (ema_10 < ema_20) & (ema_10.shift(1) >= ema_20.shift(1))

        signals[strong_trend & buy_cross] = Signal.BUY
        signals[strong_trend & sell_cross] = Signal.SELL
        return signals


class VolumeBreakout(BaseStrategy):
    def __init__(self, volume_mult: float = 2.0, lookback: int = 20):
        super().__init__("Volume_Breakout", {"volume_mult": volume_mult, "lookback": lookback})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(Signal.HOLD, index=df.index)
        vol = df["volume"]
        close = df["close"]
        lb = self.params["lookback"]
        mult = self.params["volume_mult"]

        avg_vol = vol.rolling(lb).mean()
        high_vol = vol > avg_vol * mult
        price_up = close > close.shift(1)
        price_down = close < close.shift(1)

        signals[high_vol & price_up] = Signal.BUY
        signals[high_vol & price_down] = Signal.SELL
        return signals


class TripleMA(BaseStrategy):
    def __init__(self):
        super().__init__("Triple_MA", {"fast": 10, "mid": 20, "slow": 50})

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(Signal.HOLD, index=df.index)
        fast = df["sma_10"]
        mid = df["sma_20"]
        slow = df["sma_50"]
        aligned_bull = (fast > mid) & (mid > slow)
        aligned_bear = (fast < mid) & (mid < slow)
        was_not_bull = ~((fast.shift(1) > mid.shift(1)) & (mid.shift(1) > slow.shift(1)))
        was_not_bear = ~((fast.shift(1) < mid.shift(1)) & (mid.shift(1) < slow.shift(1)))
        signals[aligned_bull & was_not_bull] = Signal.BUY
        signals[aligned_bear & was_not_bear] = Signal.SELL
        return signals


ALL_STRATEGIES = {
    "sma_crossover": SMACrossover,
    "ema_crossover": EMACrossover,
    "golden_cross": GoldenCrossDeathCross,
    "rsi_ob_os": RSIOversoldOverbought,
    "rsi_divergence": RSIDivergence,
    "macd_crossover": MACDCrossover,
    "macd_hist": MACDHistogramReversal,
    "bb_squeeze": BollingerBandSqueeze,
    "bb_bounce": BollingerBandBounce,
    "ichimoku": IchimokuCloud,
    "supertrend": SupertrendStrategy,
    "psar": ParabolicSARStrategy,
    "vwap": VWAPStrategy,
    "atr_breakout": ATRBreakout,
    "stochastic": StochasticCrossover,
    "pivot": PivotPointStrategy,
    "fibonacci": FibonacciRetracement,
    "triple_screen": TripleScreenElder,
    "turtle": TurtleTrading,
    "mean_reversion": MeanReversion,
    "adx_trend": ADXTrendStrength,
    "volume_breakout": VolumeBreakout,
    "triple_ma": TripleMA,
}
