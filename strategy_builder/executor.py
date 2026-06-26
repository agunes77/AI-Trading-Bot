"""
Strateji Çalıştırma Motoru (Topological Sort ile 0-100 Confidence Score hesaplar)
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from strategy_builder.solvers import (
    BaseSolver, CrossoverSolver, ComparisonSolver, ThresholdSolver,
    SlopeSolver, BarDirectionSolver, ChangeInSlopeSolver,
    BollingerSqueezeSolver, SupportResistanceSolver
)
from utils.logger import logger


SOLVER_MAP = {
    "crossover": CrossoverSolver,
    "comparison": ComparisonSolver,
    "threshold": ThresholdSolver,
    "slope": SlopeSolver,
    "bar_direction": BarDirectionSolver,
    "change_in_slope": ChangeInSlopeSolver,
    "bb_squeeze": BollingerSqueezeSolver,
    "support_resistance": SupportResistanceSolver,
}


class StrategyExecutor:
    def __init__(self):
        self.node_outputs = {}

    def execute(self, strategy: Dict, data: pd.DataFrame) -> Dict[str, Any]:
        try:
            nodes = strategy.get("nodes", [])
            edges = strategy.get("edges", [])
            
            if not nodes:
                return {"error": "Stratejide node yok"}

            # Topological Sort
            sorted_nodes = self._topological_sort(nodes, edges)
            
            self.node_outputs = {}
            
            for node in sorted_nodes:
                node_id = node.get("id")
                node_type = node.get("type")
                node_data = node.get("data", {})
                params = node_data.get("parameters", {})
                
                inputs = self._get_node_inputs(node_id, edges, data)
                
                output = self._execute_node(node_type, params, inputs, data)
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

    def _topological_sort(self, nodes: List[Dict], edges: List[Dict]) -> List[Dict]:
        """Node'ları bağımlılık sırasına göre diz (Kahn's Algorithm)"""
        node_map = {n["id"]: n for n in nodes}
        in_degree = {n["id"]: 0 for n in nodes}
        adj = {n["id"]: [] for n in nodes}
        
        for edge in edges:
            src, tgt = edge.get("source"), edge.get("target")
            if src in adj and tgt in in_degree:
                adj[src].append(tgt)
                in_degree[tgt] += 1
        
        queue = [nid for nid in in_degree if in_degree[nid] == 0]
        sorted_ids = []
        
        while queue:
            nid = queue.pop(0)
            sorted_ids.append(nid)
            for neighbor in adj[nid]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return [node_map[nid] for nid in sorted_ids if nid in node_map]

    def _get_node_inputs(self, node_id: str, edges: List[Dict], data: pd.DataFrame) -> Dict[str, Any]:
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

    def _execute_node(self, node_type: str, params: Dict, inputs: Dict, data: pd.DataFrame) -> Any:
        # 1. İndikatörler
        if node_type == "sma":
            price = inputs.get("value", data["close"])
            period = params.get("period", 20)
            return {"value": price.rolling(window=period).mean()}
        elif node_type == "ema":
            price = inputs.get("value", data["close"])
            period = params.get("period", 20)
            return {"value": price.ewm(span=period, adjust=False).mean()}
        elif node_type == "rsi":
            price = inputs.get("value", data["close"])
            period = params.get("period", 14)
            delta = price.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return {"value": 100 - (100 / (1 + rs))}
        elif node_type == "macd":
            price = inputs.get("value", data["close"])
            p = params
            ema_fast = price.ewm(span=p.get("fast", 12), adjust=False).mean()
            ema_slow = price.ewm(span=p.get("slow", 26), adjust=False).mean()
            macd_l = ema_fast - ema_slow
            signal = macd_l.ewm(span=p.get("signal", 9), adjust=False).mean()
            return {"macd": macd_l, "signal": signal, "histogram": macd_l - signal}
        elif node_type == "bollinger":
            price = inputs.get("value", data["close"])
            period = params.get("period", 20)
            std_dev = params.get("std_dev", 2.0)
            sma = price.rolling(window=period).mean()
            std = price.rolling(window=period).std()
            return {"upper": sma + (std * std_dev), "lower": sma - (std * std_dev)}
        elif node_type == "atr":
            tr = pd.concat([data["high"] - data["low"], abs(data["high"] - data["close"].shift()), abs(data["low"] - data["close"].shift())], axis=1).max(axis=1)
            return {"value": tr.rolling(window=params.get("period", 14)).mean()}
        elif node_type == "close_price":
            return {"value": data["close"]}

        # 2. Solver'lar (0-100 skor üretir)
        if node_type in SOLVER_MAP:
            solver = SOLVER_MAP[node_type](params=params)
            score = solver.calculate(data, inputs)
            return {"score": score}

        # 3. Logic Node'lar
        elif node_type == "and":
            in1 = inputs.get("in1", pd.Series(0, index=data.index))
            in2 = inputs.get("in2", pd.Series(0, index=data.index))
            threshold = params.get("threshold", 50)
            # En düşük skoru al ama ikisi de threshold üzerinde olmalı
            min_score = pd.concat([in1, in2], axis=1).min(axis=1)
            min_score[in1 < threshold] = 0
            min_score[in2 < threshold] = 0
            return {"score": min_score.clip(0, 100)}
        elif node_type == "or":
            in1 = inputs.get("in1", pd.Series(0, index=data.index))
            in2 = inputs.get("in2", pd.Series(0, index=data.index))
            threshold = params.get("threshold", 50)
            max_score = pd.concat([in1, in2], axis=1).max(axis=1)
            return {"score": max_score.clip(0, 100)}
        elif node_type == "xor":
            in1 = inputs.get("in1", pd.Series(0, index=data.index))
            in2 = inputs.get("in2", pd.Series(0, index=data.index))
            threshold = params.get("threshold", 50)
            c1 = in1 > threshold
            c2 = in2 > threshold
            xor_cond = c1 ^ c2
            score = pd.Series(0.0, index=data.index)
            score[xor_cond & c1] = in1[xor_cond & c1]
            score[xor_cond & c2] = in2[xor_cond & c2]
            return {"score": score.clip(0, 100)}
        elif node_type == "additive":
            in1 = inputs.get("in1", pd.Series(0, index=data.index))
            in2 = inputs.get("in2", pd.Series(0, index=data.index))
            w1 = params.get("weight1", 0.5)
            w2 = params.get("weight2", 0.5)
            return {"score": (in1 * w1 + in2 * w2).clip(0, 100)}

        # 4. Function Node'lar
        elif node_type == "inverter":
            score = inputs.get("score", pd.Series(50, index=data.index))
            return {"score": (100 - score).clip(0, 100)}
        elif node_type == "lookback":
            score = inputs.get("score", pd.Series(0, index=data.index))
            bars = params.get("bars", 1)
            return {"score": score.shift(bars).fillna(0)}
        elif node_type == "signal_extender":
            score = inputs.get("score", pd.Series(0, index=data.index))
            bars = params.get("bars", 3)
            # Yüksek skoru N bar boyunca tut
            return {"score": score.rolling(window=bars).max().fillna(0).clip(0, 100)}

        return None

    def _generate_signals(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, pd.Series]:
        signals = {"buy": pd.Series(False), "sell": pd.Series(False)}
        for node in nodes:
            node_id = node.get("id")
            node_type = node.get("type")
            params = node.get("data", {}).get("parameters", {})
            threshold = params.get("threshold", 60)
            
            if node_type == "buy_signal" and node_id in self.node_outputs:
                score = self.node_outputs[node_id].get("score", pd.Series(0))
                signals["buy"] = score >= threshold
            elif node_type == "sell_signal" and node_id in self.node_outputs:
                score = self.node_outputs[node_id].get("score", pd.Series(0))
                signals["sell"] = score >= threshold
        return signals

    def _build_chart_data(self, signals: Dict[str, pd.Series], data: pd.DataFrame) -> Dict[str, Any]:
        buy_signals = signals.get("buy", pd.Series(False))
        sell_signals = signals.get("sell", pd.Series(False))
        if len(buy_signals) != len(data):
            buy_signals = pd.Series(False, index=data.index)
        if len(sell_signals) != len(data):
            sell_signals = pd.Series(False, index=data.index)
        
        candles, buy_markers, sell_markers = [], [], []
        for i in range(len(data)):
            row = data.iloc[i]
            ts = row.name if hasattr(row.name, 'isoformat') else str(row.name)
            if hasattr(ts, 'isoformat'):
                ts = ts.isoformat()
            candles.append({
                "timestamp": ts, "open": float(row["open"]), "high": float(row["high"]),
                "low": float(row["low"]), "close": float(row["close"]), "volume": float(row["volume"]),
            })
            if bool(buy_signals.iloc[i]):
                buy_markers.append({"timestamp": ts, "price": float(row["low"]) * 0.998, "index": i, "type": "buy"})
            if bool(sell_signals.iloc[i]):
                sell_markers.append({"timestamp": ts, "price": float(row["high"]) * 1.002, "index": i, "type": "sell"})
        
        return {"candles": candles, "buy_markers": buy_markers, "sell_markers": sell_markers,
                "total_candles": len(candles), "buy_count": len(buy_markers), "sell_count": len(sell_markers)}

    def _calculate_performance(self, signals: Dict[str, pd.Series], data: pd.DataFrame) -> Dict[str, Any]:
        buy_signals = signals.get("buy", pd.Series(False))
        sell_signals = signals.get("sell", pd.Series(False))
        position, entry_price, trades, equity, equity_curve = 0, 0, [], 10000, [10000]
        
        for i in range(len(data)):
            price = data.iloc[i]["close"]
            if buy_signals.iloc[i] and position == 0:
                position = 1; entry_price = price
                trades.append({"type": "buy", "price": price, "index": i})
            elif sell_signals.iloc[i] and position == 1:
                position = 0; pnl = (price - entry_price) / entry_price; equity *= (1 + pnl)
                trades.append({"type": "sell", "price": price, "index": i, "pnl": pnl})
            equity_curve.append(equity)
        if position == 1:
            pnl = (data.iloc[-1]["close"] - entry_price) / entry_price; equity *= (1 + pnl)
            equity_curve.append(equity)
        
        equity_arr = np.array(equity_curve)
        returns = np.diff(equity_arr) / equity_arr[:-1]
        total_return = (equity - 10000) / 10000 * 100
        max_dd = (1 - equity_arr / np.maximum.accumulate(equity_arr)).max() * 100
        sharpe = np.sqrt(252) * returns.mean() / (returns.std() + 1e-10) if len(returns) > 0 else 0
        winning = [t for t in trades if t.get("pnl", 0) > 0]
        sell_trades = [t for t in trades if t["type"] == "sell"]
        
        return {
            "total_return_pct": total_return, "max_drawdown_pct": max_dd, "sharpe_ratio": sharpe,
            "total_trades": len(sell_trades), "winning_trades": len(winning),
            "losing_trades": len(sell_trades) - len(winning),
            "win_rate": len(winning) / len(sell_trades) * 100 if sell_trades else 0,
            "final_equity": equity, "equity_curve": equity_curve,
        }