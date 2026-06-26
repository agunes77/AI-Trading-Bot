"""
Strateji Çalıştırma Motoru
Node-based stratejiyi çalıştırır ve sinyaller üretir
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from strategy_builder.node_definitions import get_node_definition, NodeType
from utils.logger import logger


class StrategyExecutor:
    """Strateji çalıştırma motoru"""
    
    def __init__(self):
        self.node_outputs = {}
    
    def execute(self, strategy: Dict, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Stratejiyi çalıştır
        
        Args:
            strategy: Strateji tanımı (nodes ve edges)
            data: OHLCV verisi
        
        Returns:
            Sinyaller ve performans metrikleri
        """
        try:
            nodes = strategy.get("nodes", [])
            edges = strategy.get("edges", [])
            
            if not nodes:
                return {"error": "Stratejide node yok"}
            
            self.node_outputs = {}
            
            for node in nodes:
                node_id = node.get("id")
                node_type = node.get("type")
                node_data = node.get("data", {})
                
                inputs = self._get_node_inputs(node_id, edges, data)
                output = self._execute_node(node_type, node_data, inputs, data)
                self.node_outputs[node_id] = output
            
            signals = self._generate_signals(nodes, edges)
            performance = self._calculate_performance(signals, data)
            chart_data = self._build_chart_data(signals, data)
            
            return {
                "success": True,
                "signals": signals,
                "performance": performance,
                "chart_data": chart_data,
                "node_count": len(nodes),
            }
            
        except Exception as e:
            logger.error(f"Strateji çalıştırma hatası: {e}")
            return {"error": str(e)}
    
    def _get_node_inputs(self, node_id: str, edges: List[Dict], data: pd.DataFrame) -> Dict[str, Any]:
        """Node'un girdilerini topla"""
        inputs = {}
        
        for edge in edges:
            if edge.get("target") == node_id:
                source_id = edge.get("source")
                source_handle = edge.get("sourceHandle", "output")
                target_handle = edge.get("targetHandle", "input")
                
                if source_id in self.node_outputs:
                    source_output = self.node_outputs[source_id]
                    if isinstance(source_output, dict):
                        inputs[target_handle] = source_output.get(source_handle, source_output)
                    else:
                        inputs[target_handle] = source_output
        
        return inputs
    
    def _execute_node(self, node_type: str, node_data: Dict, inputs: Dict, data: pd.DataFrame) -> Any:
        """Tek bir node'u çalıştır"""
        
        if node_type == "sma":
            price = inputs.get("price", data["close"])
            period = node_data.get("parameters", {}).get("period", 20)
            return price.rolling(window=period).mean()
        
        elif node_type == "ema":
            price = inputs.get("price", data["close"])
            period = node_data.get("parameters", {}).get("period", 20)
            return price.ewm(span=period, adjust=False).mean()
        
        elif node_type == "rsi":
            price = inputs.get("price", data["close"])
            period = node_data.get("parameters", {}).get("period", 14)
            return self._calculate_rsi(price, period)
        
        elif node_type == "macd":
            price = inputs.get("price", data["close"])
            params = node_data.get("parameters", {})
            fast = params.get("fast", 12)
            slow = params.get("slow", 26)
            signal = params.get("signal", 9)
            
            ema_fast = price.ewm(span=fast, adjust=False).mean()
            ema_slow = price.ewm(span=slow, adjust=False).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            histogram = macd_line - signal_line
            
            return {"macd": macd_line, "signal": signal_line, "histogram": histogram}
        
        elif node_type == "bollinger":
            price = inputs.get("price", data["close"])
            params = node_data.get("parameters", {})
            period = params.get("period", 20)
            std_dev = params.get("std_dev", 2.0)
            
            middle = price.rolling(window=period).mean()
            std = price.rolling(window=period).std()
            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)
            
            return {"upper": upper, "middle": middle, "lower": lower}
        
        elif node_type == "atr":
            high = inputs.get("high", data["high"])
            low = inputs.get("low", data["low"])
            close = inputs.get("close", data["close"])
            period = node_data.get("parameters", {}).get("period", 14)
            
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()
            
            return atr
        
        elif node_type == "stochastic":
            high = inputs.get("high", data["high"])
            low = inputs.get("low", data["low"])
            close = inputs.get("close", data["close"])
            params = node_data.get("parameters", {})
            k_period = params.get("k_period", 14)
            d_period = params.get("d_period", 3)
            
            lowest_low = low.rolling(window=k_period).min()
            highest_high = high.rolling(window=k_period).max()
            k = 100 * (close - lowest_low) / (highest_high - lowest_low)
            d = k.rolling(window=d_period).mean()
            
            return {"k": k, "d": d}
        
        elif node_type == "and":
            input1 = inputs.get("input1", False)
            input2 = inputs.get("input2", False)
            return input1 & input2
        
        elif node_type == "or":
            input1 = inputs.get("input1", False)
            input2 = inputs.get("input2", False)
            return input1 | input2
        
        elif node_type == "xor":
            input1 = inputs.get("input1", False)
            input2 = inputs.get("input2", False)
            return input1 ^ input2
        
        elif node_type == "not":
            input_val = inputs.get("input", False)
            return ~input_val
        
        elif node_type == "crossover":
            series1 = inputs.get("series1")
            series2 = inputs.get("series2")
            direction = node_data.get("parameters", {}).get("direction", "above")
            
            if series1 is None or series2 is None:
                return pd.Series(False, index=data.index)
            
            if direction == "above":
                return (series1 > series2) & (series1.shift(1) <= series2.shift(1))
            else:
                return (series1 < series2) & (series1.shift(1) >= series2.shift(1))
        
        elif node_type == "comparison":
            value1 = inputs.get("value1")
            value2 = inputs.get("value2")
            operator = node_data.get("parameters", {}).get("operator", ">")
            
            if value1 is None or value2 is None:
                return pd.Series(False, index=data.index)
            
            if operator == ">":
                return value1 > value2
            elif operator == "<":
                return value1 < value2
            elif operator == ">=":
                return value1 >= value2
            elif operator == "<=":
                return value1 <= value2
            elif operator == "==":
                return value1 == value2
            else:
                return pd.Series(False, index=data.index)
        
        elif node_type == "threshold":
            value = inputs.get("value")
            params = node_data.get("parameters", {})
            threshold = params.get("threshold", 50)
            condition = params.get("condition", "above")
            
            if value is None:
                return pd.Series(False, index=data.index)
            
            if condition == "above":
                return value > threshold
            else:
                return value < threshold
        
        elif node_type == "slope":
            series = inputs.get("series")
            params = node_data.get("parameters", {})
            period = params.get("period", 5)
            direction = params.get("direction", "up")
            
            if series is None:
                return pd.Series(False, index=data.index)
            
            slope = series.diff(period)
            
            if direction == "up":
                return slope > 0
            else:
                return slope < 0
        
        else:
            logger.warning(f"Bilinmeyen node tipi: {node_type}")
            return None
    
    def _calculate_rsi(self, price: pd.Series, period: int = 14) -> pd.Series:
        """RSI hesapla"""
        delta = price.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _generate_signals(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, pd.Series]:
        """Alış/satış sinyallerini üret"""
        signals = {"buy": pd.Series(False), "sell": pd.Series(False)}
        
        for node in nodes:
            node_id = node.get("id")
            node_type = node.get("type")
            
            if node_type == "buy_signal":
                if node_id in self.node_outputs:
                    signals["buy"] = self.node_outputs[node_id]
            
            elif node_type == "sell_signal":
                if node_id in self.node_outputs:
                    signals["sell"] = self.node_outputs[node_id]
        
        return signals
    
    def _build_chart_data(self, signals: Dict[str, pd.Series], data: pd.DataFrame) -> Dict[str, Any]:
        """Grafik verisi ve sinyal noktalarını oluştur"""
        buy_signals = signals.get("buy", pd.Series(False))
        sell_signals = signals.get("sell", pd.Series(False))
        
        if len(buy_signals) != len(data):
            buy_signals = pd.Series(False, index=data.index)
        if len(sell_signals) != len(data):
            sell_signals = pd.Series(False, index=data.index)
        
        candles = []
        buy_markers = []
        sell_markers = []
        
        for i in range(len(data)):
            row = data.iloc[i]
            ts = row.name if hasattr(row.name, 'isoformat') else str(row.name)
            if hasattr(ts, 'isoformat'):
                ts = ts.isoformat()
            
            candle = {
                "timestamp": ts,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            }
            candles.append(candle)
            
            if bool(buy_signals.iloc[i]):
                buy_markers.append({
                    "timestamp": ts,
                    "price": float(row["low"]) * 0.998,
                    "index": i,
                    "type": "buy",
                })
            
            if bool(sell_signals.iloc[i]):
                sell_markers.append({
                    "timestamp": ts,
                    "price": float(row["high"]) * 1.002,
                    "index": i,
                    "type": "sell",
                })
        
        return {
            "candles": candles,
            "buy_markers": buy_markers,
            "sell_markers": sell_markers,
            "total_candles": len(candles),
            "buy_count": len(buy_markers),
            "sell_count": len(sell_markers),
        }
    
    def _calculate_performance(self, signals: Dict[str, pd.Series], data: pd.DataFrame) -> Dict[str, Any]:
        """Strateji performansını hesapla"""
        buy_signals = signals.get("buy", pd.Series(False))
        sell_signals = signals.get("sell", pd.Series(False))
        
        position = 0
        entry_price = 0
        trades = []
        equity = 10000
        equity_curve = [equity]
        
        for i in range(len(data)):
            price = data.iloc[i]["close"]
            
            if buy_signals.iloc[i] and position == 0:
                position = 1
                entry_price = price
                trades.append({"type": "buy", "price": price, "index": i})
            
            elif sell_signals.iloc[i] and position == 1:
                position = 0
                pnl = (price - entry_price) / entry_price
                equity *= (1 + pnl)
                trades.append({"type": "sell", "price": price, "index": i, "pnl": pnl})
            
            equity_curve.append(equity)
        
        if position == 1:
            final_price = data.iloc[-1]["close"]
            pnl = (final_price - entry_price) / entry_price
            equity *= (1 + pnl)
            equity_curve.append(equity)
        
        equity_arr = np.array(equity_curve)
        returns = np.diff(equity_arr) / equity_arr[:-1]
        
        total_return = (equity - 10000) / 10000 * 100
        max_drawdown = (1 - equity_arr / np.maximum.accumulate(equity_arr)).max() * 100
        sharpe = np.sqrt(252) * returns.mean() / (returns.std() + 1e-10) if len(returns) > 0 else 0
        
        winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in trades if t.get("pnl", 0) <= 0]
        
        return {
            "total_return_pct": total_return,
            "max_drawdown_pct": max_drawdown,
            "sharpe_ratio": sharpe,
            "total_trades": len([t for t in trades if t["type"] == "sell"]),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": len(winning_trades) / len([t for t in trades if t["type"] == "sell"]) * 100 if trades else 0,
            "final_equity": equity,
            "equity_curve": equity_curve,
        }
