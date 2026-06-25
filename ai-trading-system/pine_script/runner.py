"""
Pine Script Runner
Pine Script kodunu çalıştırır ve sonuçları döndürür
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from pine_script.parser import PineScriptParser, PineIndicatorLibrary, crossover, crossunder
from utils.logger import logger


class PineScriptRunner:
    """Pine Script kodunu çalıştırma motoru"""
    
    def __init__(self):
        self.parser = PineScriptParser()
        self.library = PineIndicatorLibrary()
    
    def run(self, pine_code: str, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Pine Script kodunu çalıştırır
        
        Args:
            pine_code: Pine Script kodu
            data: OHLCV verisi
        
        Returns:
            Sonuçlar (sinyaller, indikatör değerleri, performans)
        """
        try:
            parsed = self.parser.parse(pine_code)
            
            if 'error' in parsed:
                return {'error': parsed['error']}
            
            df = data.copy()
            
            indicator_values = self._calculate_indicators(df, parsed)
            
            buy_signals, sell_signals = self._generate_signals(df, parsed)
            
            performance = self._calculate_performance(buy_signals, sell_signals, df)
            
            return {
                'success': True,
                'name': parsed.get('name', 'Unknown'),
                'version': parsed.get('version', '5'),
                'indicators': indicator_values,
                'buy_signals': buy_signals.sum(),
                'sell_signals': sell_signals.sum(),
                'performance': performance,
                'python_code': parsed.get('python_code', ''),
            }
            
        except Exception as e:
            logger.error(f"Pine Script çalıştırma hatası: {e}")
            return {'error': str(e)}
    
    def _calculate_indicators(self, df: pd.DataFrame, parsed: Dict) -> Dict[str, pd.Series]:
        """İndikatörleri hesaplar"""
        indicators = {}
        close = df['close']
        high = df['high']
        low = df['low']
        open_ = df['open']
        volume = df['volume']
        
        ta = self.library
        
        for calc in parsed.get('calculations', []):
            try:
                var_name, expr = self._parse_calculation(calc)
                if var_name and expr:
                    result = eval(expr, {
                        'ta': ta,
                        'close': close,
                        'high': high,
                        'low': low,
                        'open': open_,
                        'volume': volume,
                        'pd': pd,
                        'np': np,
                    })
                    if isinstance(result, pd.Series):
                        indicators[var_name] = result
                    elif isinstance(result, tuple):
                        for i, r in enumerate(result):
                            if isinstance(r, pd.Series):
                                indicators[f"{var_name}_{i}"] = r
            except Exception as e:
                logger.warning(f"İndikatör hesaplama hatası: {calc} - {e}")
        
        return indicators
    
    def _parse_calculation(self, calc: str) -> tuple:
        """Hesaplama satırını parse eder"""
        if '=' not in calc:
            return None, None
        
        parts = calc.split('=', 1)
        var_name = parts[0].strip()
        expr = parts[1].strip()
        
        expr = expr.replace('ta.sma', 'ta.sma')
        expr = expr.replace('ta.ema', 'ta.ema')
        expr = expr.replace('ta.rsi', 'ta.rsi')
        expr = expr.replace('ta.macd', 'ta.macd')
        expr = expr.replace('ta.bb', 'ta.bb')
        expr = expr.replace('ta.stoch', 'ta.stoch')
        expr = expr.replace('ta.atr', 'ta.atr')
        
        return var_name, expr
    
    def _generate_signals(self, df: pd.DataFrame, parsed: Dict) -> tuple:
        """Alış/satış sinyallerini üretir"""
        buy_signals = pd.Series(False, index=df.index)
        sell_signals = pd.Series(False, index=df.index)
        
        indicators = self._calculate_indicators(df, parsed)
        
        for cond in parsed.get('conditions', []):
            try:
                converted = self.parser._convert_condition(cond)
                
                if 'buy_signals' in converted:
                    exec(converted, {
                        'buy_signals': buy_signals,
                        'sell_signals': sell_signals,
                        'ta': self.library,
                        'crossover': crossover,
                        'crossunder': crossunder,
                        **indicators,
                        'close': df['close'],
                        'high': df['high'],
                        'low': df['low'],
                        'pd': pd,
                        'np': np,
                    })
            except Exception as e:
                logger.warning(f"Koşul hesaplama hatası: {cond} - {e}")
        
        return buy_signals, sell_signals
    
    def _calculate_performance(self, buy_signals: pd.Series, sell_signals: pd.Series, 
                               data: pd.DataFrame) -> Dict[str, Any]:
        """Strateji performansını hesaplar"""
        position = 0
        entry_price = 0
        trades = []
        equity = 10000
        equity_curve = [equity]
        
        for i in range(len(data)):
            price = data.iloc[i]['close']
            
            if buy_signals.iloc[i] and position == 0:
                position = 1
                entry_price = price
                trades.append({'type': 'buy', 'price': price, 'index': i})
            
            elif sell_signals.iloc[i] and position == 1:
                position = 0
                pnl = (price - entry_price) / entry_price
                equity *= (1 + pnl)
                trades.append({'type': 'sell', 'price': price, 'index': i, 'pnl': pnl})
            
            equity_curve.append(equity)
        
        if position == 1:
            final_price = data.iloc[-1]['close']
            pnl = (final_price - entry_price) / entry_price
            equity *= (1 + pnl)
            equity_curve.append(equity)
        
        equity_arr = np.array(equity_curve)
        returns = np.diff(equity_arr) / equity_arr[:-1]
        
        total_return = (equity - 10000) / 10000 * 100
        max_drawdown = (1 - equity_arr / np.maximum.accumulate(equity_arr)).max() * 100
        sharpe = np.sqrt(252) * returns.mean() / (returns.std() + 1e-10) if len(returns) > 0 else 0
        
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) <= 0]
        total_trades = len([t for t in trades if t['type'] == 'sell'])
        
        return {
            'total_return_pct': total_return,
            'max_drawdown_pct': max_drawdown,
            'sharpe_ratio': sharpe,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / total_trades * 100 if total_trades > 0 else 0,
            'final_equity': equity,
            'equity_curve': equity_curve,
        }


class TradingViewIndicatorPresets:
    """TradingView'den popüler indikatör presetleri"""
    
    PRESETS = {
        'RSI Divergence': '''//@version=5
indicator("RSI Divergence", shorttitle="RSI Div")
rsi = ta.rsi(close, 14)
overbought = rsi > 70
oversold = rsi < 30
plot(rsi, "RSI", color=purple)
hline(70, "Overbought", color=red)
hline(30, "Oversold", color=green)''',
        
        'MACD Crossover': '''//@version=5
indicator("MACD Cross", shorttitle="MACD Cross")
[macdLine, signalLine, histLine] = ta.macd(close, 12, 26, 9)
bullishCross = ta.crossover(macdLine, signalLine)
bearishCross = ta.crossunder(macdLine, signalLine)
plot(macdLine, "MACD", color=blue)
plot(signalLine, "Signal", color=red)''',
        
        'Bollinger Bands': '''//@version=5
indicator("Bollinger Bands", shorttitle="BB")
[upper, middle, lower] = ta.bb(close, 20, 2.0)
plot(upper, "Upper", color=red)
plot(middle, "Middle", color=blue)
plot(lower, "Lower", color=green)''',
        
        'Supertrend': '''//@version=5
indicator("Supertrend", shorttitle="ST")
[supertrend, direction] = ta.supertrend(3.0, 10)
plot(supertrend, "Supertrend", color=direction > 0 ? green : red)''',
        
        'EMA Cross': '''//@version=5
indicator("EMA Cross", shorttitle="EMA Cross")
fast = ta.ema(close, 9)
slow = ta.ema(close, 21)
bullish = ta.crossover(fast, slow)
bearish = ta.crossunder(fast, slow)
plot(fast, "Fast EMA", color=blue)
plot(slow, "Slow EMA", color=red)''',
        
        'Stochastic': '''//@version=5
indicator("Stochastic", shorttitle="Stoch")
[k, d] = ta.stoch(high, low, close, 14, 3)
plot(k, "%K", color=blue)
plot(d, "%D", color=red)
hline(80, "Overbought", color=red)
hline(20, "Oversold", color=green)''',
        
        'ATR Trailing Stop': '''//@version=5
indicator("ATR Trailing", shorttitle="ATR Trail")
atr = ta.atr(high, low, close, 14)
trailingStop = close - (2.0 * atr)
plot(trailingStop, "Trailing Stop", color=orange)''',
        
        'Volume Profile': '''//@version=5
indicator("Volume", shorttitle="Vol")
vol = volume
volSma = ta.sma(volume, 20)
plot(vol, "Volume", color=blue)
plot(volSma, "Vol SMA", color=orange)''',
        
        'Ichimoku Cloud': '''//@version=5
indicator("Ichimoku", shorttitle="ICH")
conversion = (ta.highest(high, 9) + ta.lowest(low, 9)) / 2
base = (ta.highest(high, 26) + ta.lowest(low, 26)) / 2
spanA = (conversion + base) / 2
spanB = (ta.highest(high, 52) + ta.lowest(low, 52)) / 2
plot(conversion, "Conversion", color=blue)
plot(base, "Base", color=red)''',
        
        'VWAP': '''//@version=5
indicator("VWAP", shorttitle="VWAP")
vwap = ta.vwma(close, 20)
plot(vwap, "VWAP", color=purple)''',
    }
    
    @classmethod
    def get_preset(cls, name: str) -> Optional[str]:
        """Preset kodunu döndürür"""
        return cls.PRESETS.get(name)
    
    @classmethod
    def list_presets(cls) -> list:
        """Mevcut presetleri listeler"""
        return list(cls.PRESETS.keys())
