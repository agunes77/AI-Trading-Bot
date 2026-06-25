"""
Pine Script Parser
TradingView Pine Script kodunu Python koduna dönüştürür
"""
import re
from typing import Dict, List, Any, Optional
from utils.logger import logger


class PineScriptParser:
    """Pine Script kodunu parse eder ve Python koduna dönüştürür"""
    
    def __init__(self):
        self.indicator_map = {
            'sma': 'ta.sma',
            'ema': 'ta.ema',
            'wma': 'ta.wma',
            'rsi': 'ta.rsi',
            'macd': 'ta.macd',
            'stoch': 'ta.stoch',
            'atr': 'ta.atr',
            'bb': 'ta.bb',
            'cci': 'ta.cci',
            'willr': 'ta.willr',
            'mom': 'ta.mom',
            'roc': 'ta.roc',
            'obv': 'ta.obv',
            'vwma': 'ta.vwma',
            'supertrend': 'ta.supertrend',
            'pivot': 'ta.pivot',
            'valuewhen': 'ta.valuewhen',
            'cross': 'ta.cross',
            'crossover': 'ta.crossover',
            'crossunder': 'ta.crossunder',
            'highest': 'ta.highest',
            'lowest': 'ta.lowest',
            'sum': 'ta.sum',
            'change': 'ta.change',
            'pivothigh': 'ta.pivothigh',
            'pivotlow': 'ta.pivotlow',
        }
        
        self.math_map = {
            'abs': 'abs',
            'ceil': 'math.ceil',
            'floor': 'math.floor',
            'round': 'round',
            'max': 'max',
            'min': 'min',
            'pow': 'pow',
            'sqrt': 'math.sqrt',
            'log': 'math.log',
            'log10': 'math.log10',
            'sign': 'np.sign',
            'sin': 'math.sin',
            'cos': 'math.cos',
            'tan': 'math.tan',
        }
    
    def parse(self, pine_code: str) -> Dict[str, Any]:
        """Pine Script kodunu parse eder"""
        try:
            lines = pine_code.strip().split('\n')
            
            result = {
                'version': self._extract_version(lines),
                'name': self._extract_name(lines),
                'inputs': self._extract_inputs(lines),
                'calculations': self._extract_calculations(lines),
                'plots': self._extract_plots(lines),
                'conditions': self._extract_conditions(lines),
                'raw_code': pine_code,
            }
            
            python_code = self._to_python(result)
            result['python_code'] = python_code
            
            return result
            
        except Exception as e:
            logger.error(f"Pine Script parse hatası: {e}")
            return {'error': str(e)}
    
    def _extract_version(self, lines: List[str]) -> str:
        """Pine Script versiyonunu çıkarır"""
        for line in lines:
            if line.strip().startswith('//@version='):
                return line.strip().split('=')[1].strip()
        return '5'
    
    def _extract_name(self, lines: List[str]) -> str:
        """İndikatör/strateji adını çıkarır"""
        for line in lines:
            line = line.strip()
            if line.startswith('indicator(') or line.startswith('strategy('):
                match = re.search(r'["\']([^"\']+)["\']', line)
                if match:
                    return match.group(1)
        return 'Unknown'
    
    def _extract_inputs(self, lines: List[str]) -> List[Dict]:
        """Input parametrelerini çıkarır"""
        inputs = []
        for line in lines:
            line = line.strip()
            if 'input(' in line or 'input.int(' in line or 'input.float(' in line:
                match = re.search(r'(\w+)\s*=\s*input(?:\.int|\.float)?\(([^)]+)\)', line)
                if match:
                    name = match.group(1)
                    params = match.group(2)
                    inputs.append({
                        'name': name,
                        'params': params,
                    })
        return inputs
    
    def _extract_calculations(self, lines: List[str]) -> List[str]:
        """Hesaplama satırlarını çıkarır"""
        calculations = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith('//') or line.startswith('//@'):
                continue
            if '=' in line and not line.startswith('indicator') and not line.startswith('strategy'):
                calculations.append(line)
        return calculations
    
    def _extract_plots(self, lines: List[str]) -> List[Dict]:
        """Plot tanımlarını çıkarır"""
        plots = []
        for line in lines:
            line = line.strip()
            if line.startswith('plot('):
                match = re.search(r'plot\(([^,]+)(?:,\s*([^)]+))?\)', line)
                if match:
                    plots.append({
                        'series': match.group(1).strip(),
                        'params': match.group(2) if match.group(2) else '',
                    })
        return plots
    
    def _extract_conditions(self, lines: List[str]) -> List[str]:
        """Koşul tanımlarını çıkarır"""
        conditions = []
        for line in lines:
            line = line.strip()
            if 'ta.crossover' in line or 'ta.crossunder' in line:
                conditions.append(line)
            elif 'longCondition' in line or 'shortCondition' in line:
                conditions.append(line)
        return conditions
    
    def _to_python(self, parsed: Dict) -> str:
        """Parse edilmiş Pine Script'i Python koduna dönüştürür"""
        python_lines = [
            "import pandas as pd",
            "import numpy as np",
            "",
            "def calculate_indicators(df):",
            "    \"\"\"Pine Script indikatörlerini hesapla\"\"\"",
            "    close = df['close']",
            "    high = df['high']",
            "    low = df['low']",
            "    open_ = df['open']",
            "    volume = df['volume']",
            "",
        ]
        
        for calc in parsed.get('calculations', []):
            python_line = self._convert_line(calc)
            if python_line:
                python_lines.append(f"    {python_line}")
        
        python_lines.extend([
            "",
            "    return df",
            "",
            "def generate_signals(df):",
            "    \"\"\"Alış/satış sinyallerini üret\"\"\"",
            "    buy_signals = pd.Series(False, index=df.index)",
            "    sell_signals = pd.Series(False, index=df.index)",
            "",
        ])
        
        for cond in parsed.get('conditions', []):
            python_cond = self._convert_condition(cond)
            if python_cond:
                python_lines.append(f"    {python_cond}")
        
        python_lines.extend([
            "",
            "    return buy_signals, sell_signals",
        ])
        
        return '\n'.join(python_lines)
    
    def _convert_line(self, line: str) -> str:
        """Tek bir Pine Script satırını Python'a dönüştürür"""
        converted = line
        
        for pine_func, py_func in self.indicator_map.items():
            converted = re.sub(
                rf'\b{pine_func}\s*\(',
                f'{py_func}(',
                converted
            )
        
        for pine_func, py_func in self.math_map.items():
            converted = re.sub(
                rf'\b{pine_func}\s*\(',
                f'{py_func}(',
                converted
            )
        
        converted = converted.replace('close', 'close')
        converted = converted.replace('high', 'high')
        converted = converted.replace('low', 'low')
        converted = converted.replace('open', 'open_')
        converted = converted.replace('volume', 'volume')
        
        converted = re.sub(r'\[(\d+)\]', r'.shift(\1)', converted)
        
        return converted
    
    def _convert_condition(self, line: str) -> str:
        """Koşul satırını Python'a dönüştürür"""
        converted = self._convert_line(line)
        
        if 'ta.crossover' in converted:
            converted = converted.replace('ta.crossover', 'crossover')
            converted = f"buy_signals |= {converted.split('=', 1)[-1].strip()}"
        elif 'ta.crossunder' in converted:
            converted = converted.replace('ta.crossunder', 'crossunder')
            converted = f"sell_signals |= {converted.split('=', 1)[-1].strip()}"
        
        return converted


def crossover(series1: pd.Series, series2: pd.Series) -> pd.Series:
    """Yukarı kesişim"""
    return (series1 > series2) & (series1.shift(1) <= series2.shift(1))


def crossunder(series1: pd.Series, series2: pd.Series) -> pd.Series:
    """Aşağı kesişim"""
    return (series1 < series2) & (series1.shift(1) >= series2.shift(1))


class PineIndicatorLibrary:
    """TradingView uyumlu indikatör kütüphanesi"""
    
    @staticmethod
    def sma(series: pd.Series, period: int = 20) -> pd.Series:
        return series.rolling(window=period).mean()
    
    @staticmethod
    def ema(series: pd.Series, period: int = 20) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def wma(series: pd.Series, period: int = 20) -> pd.Series:
        weights = np.arange(1, period + 1)
        return series.rolling(window=period).apply(
            lambda x: np.dot(x, weights) / weights.sum(), raw=True
        )
    
    @staticmethod
    def rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def bb(series: pd.Series, period: int = 20, std_dev: float = 2.0):
        middle = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
    
    @staticmethod
    def stoch(high: pd.Series, low: pd.Series, close: pd.Series, 
              k_period: int = 14, d_period: int = 3):
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d = k.rolling(window=d_period).mean()
        return k, d
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    @staticmethod
    def cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        tp = (high + low + close) / 3
        sma = tp.rolling(window=period).mean()
        mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
        return (tp - sma) / (0.015 * mad)
    
    @staticmethod
    def willr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        return -100 * (highest_high - close) / (highest_high - lowest_low)
    
    @staticmethod
    def mom(series: pd.Series, period: int = 10) -> pd.Series:
        return series.diff(period)
    
    @staticmethod
    def roc(series: pd.Series, period: int = 10) -> pd.Series:
        return ((series - series.shift(period)) / series.shift(period)) * 100
    
    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        direction = np.sign(close.diff())
        return (volume * direction).cumsum()
    
    @staticmethod
    def vwma(series: pd.Series, volume: pd.Series, period: int = 20) -> pd.Series:
        return (series * volume).rolling(window=period).sum() / volume.rolling(window=period).sum()
    
    @staticmethod
    def supertrend(high: pd.Series, low: pd.Series, close: pd.Series, 
                   period: int = 10, multiplier: float = 3.0):
        atr = PineIndicatorLibrary.atr(high, low, close, period)
        hl2 = (high + low) / 2
        upper_band = hl2 + multiplier * atr
        lower_band = hl2 - multiplier * atr
        
        supertrend = pd.Series(np.nan, index=close.index)
        direction = pd.Series(1, index=close.index)
        
        for i in range(period, len(close)):
            if close.iloc[i] > upper_band.iloc[i-1]:
                direction.iloc[i] = 1
            elif close.iloc[i] < lower_band.iloc[i-1]:
                direction.iloc[i] = -1
            else:
                direction.iloc[i] = direction.iloc[i-1]
            
            if direction.iloc[i] > 0:
                supertrend.iloc[i] = lower_band.iloc[i]
            else:
                supertrend.iloc[i] = upper_band.iloc[i]
        
        return supertrend, direction
    
    @staticmethod
    def pivot(series: pd.Series, left: int = 5, right: int = 5):
        pivothigh = pd.Series(np.nan, index=series.index)
        pivotlow = pd.Series(np.nan, index=series.index)
        
        for i in range(left, len(series) - right):
            if all(series.iloc[i] > series.iloc[i-j] for j in range(1, left + 1)) and \
               all(series.iloc[i] > series.iloc[i+j] for j in range(1, right + 1)):
                pivothigh.iloc[i] = series.iloc[i]
            
            if all(series.iloc[i] < series.iloc[i-j] for j in range(1, left + 1)) and \
               all(series.iloc[i] < series.iloc[i+j] for j in range(1, right + 1)):
                pivotlow.iloc[i] = series.iloc[i]
        
        return pivothigh, pivotlow
