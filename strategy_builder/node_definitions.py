"""
Node Tanımları - Strateji Tasarım Modülü (0-100 Confidence Score)
BloodHound/SharkIndicator tarzı güçlendirilmiş node kütüphanesi
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class NodeType(Enum):
    SOLVER = "solver"
    LOGIC = "logic"
    FUNCTION = "function"
    INDICATOR = "indicator"
    OUTPUT = "output"


@dataclass
class NodePort:
    id: str
    name: str
    type: str
    direction: str


@dataclass
class NodeDefinition:
    id: str
    name: str
    type: NodeType
    category: str
    description: str
    inputs: List[NodePort] = field(default_factory=list)
    outputs: List[NodePort] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    icon: str = "circle"
    color: str = "#06b6d4"

# --- İndikatör Node'ları (Ham veri üretir) ---
INDICATOR_NODES = {
    "sma": NodeDefinition(id="sma", name="SMA", type=NodeType.INDICATOR, category="1. İndikatörler", description="Basit Hareketli Ortalama", outputs=[NodePort("value", "SMA", "series", "output")], parameters={"period": 20}, icon="trending-up", color="#3b82f6"),
    "ema": NodeDefinition(id="ema", name="EMA", type=NodeType.INDICATOR, category="1. İndikatörler", description="Üstel Hareketli Ortalama", outputs=[NodePort("value", "EMA", "series", "output")], parameters={"period": 20}, icon="trending-up", color="#3b82f6"),
    "rsi": NodeDefinition(id="rsi", name="RSI", type=NodeType.INDICATOR, category="1. İndikatörler", description="Göreceli Güç Endeksi", outputs=[NodePort("value", "RSI", "series", "output")], parameters={"period": 14}, icon="activity", color="#a855f7"),
    "macd": NodeDefinition(id="macd", name="MACD", type=NodeType.INDICATOR, category="1. İndikatörler", description="Moving Average Convergence Divergence", outputs=[NodePort("macd", "MACD", "series", "output"), NodePort("signal", "Signal", "series", "output")], parameters={"fast": 12, "slow": 26, "signal": 9}, icon="bar-chart-2", color="#3b82f6"),
    "bollinger": NodeDefinition(id="bollinger", name="Bollinger Bands", type=NodeType.INDICATOR, category="1. İndikatörler", description="Bollinger Bantları", outputs=[NodePort("upper", "Üst Bant", "series", "output"), NodePort("lower", "Alt Bant", "series", "output")], parameters={"period": 20, "std_dev": 2.0}, icon="git-branch", color="#eab308"),
    "atr": NodeDefinition(id="atr", name="ATR", type=NodeType.INDICATOR, category="1. İndikatörler", description="Ortalama Gerçek Aralık", outputs=[NodePort("value", "ATR", "series", "output")], parameters={"period": 14}, icon="zap", color="#eab308"),
    "close_price": NodeDefinition(id="close_price", name="Kapanış Fiyatı", type=NodeType.INDICATOR, category="1. İndikatörler", description="Kapanış fiyatı verisi", outputs=[NodePort("value", "Kapanış", "series", "output")], icon="dollar-sign", color="#22c55e"),
}

# --- Solver Node'ları (0-100 Skor üretir) ---
SOLVER_NODES = {
    "crossover": NodeDefinition(id="crossover", name="Crossover", type=NodeType.SOLVER, category="2. Confidence Solver'lar", description="İki serinin kesişimi (Golden/Death Cross)", inputs=[NodePort("series1", "Fast Seri", "series", "input"), NodePort("series2", "Slow Seri", "series", "input")], outputs=[NodePort("score", "Skor (0-100)", "score", "output")], parameters={"direction": "above"}, icon="git-merge", color="#06b6d4"),
    "comparison": NodeDefinition(id="comparison", name="Comparison (A vs B)", type=NodeType.SOLVER, category="2. Confidence Solver'lar", description="İki değeri karşılaştırır", inputs=[NodePort("value1", "Değer A", "series", "input"), NodePort("value2", "Değer B", "series", "input")], outputs=[NodePort("score", "Skor (0-100)", "score", "output")], parameters={"operator": ">"}, icon="git-compare", color="#06b6d4"),
    "threshold": NodeDefinition(id="threshold", name="Threshold", type=NodeType.SOLVER, category="2. Confidence Solver'lar", description="Eşik Değer Kontrolü", inputs=[NodePort("value", "Değer", "series", "input")], outputs=[NodePort("score", "Skor (0-100)", "score", "output")], parameters={"threshold": 50, "condition": "above"}, icon="sliders", color="#06b6d4"),
    "slope": NodeDefinition(id="slope", name="Slope (Trend Gücü)", type=NodeType.SOLVER, category="2. Confidence Solver'lar", description="Serinin N barlık eğimi", inputs=[NodePort("series", "Seri", "series", "input")], outputs=[NodePort("score", "Skor (0-100)", "score", "output")], parameters={"period": 5, "direction": "up"}, icon="trending-up", color="#06b6d4"),
    "bar_direction": NodeDefinition(id="bar_direction", name="Bar Direction", type=NodeType.SOLVER, category="2. Confidence Solver'lar", description="Son N barın yön oranına göre skor", inputs=[], outputs=[NodePort("score", "Skor (0-100)", "score", "output")], parameters={"lookback": 5, "direction": "up"}, icon="bar-chart", color="#06b6d4"),
    "change_in_slope": NodeDefinition(id="change_in_slope", name="Change in Slope (Dönüş)", type=NodeType.SOLVER, category="2. Confidence Solver'lar", description="Momentum dönüşü tespiti", inputs=[NodePort("series", "Seri", "series", "input")], outputs=[NodePort("score", "Skor (0-100)", "score", "output")], parameters={"lookback": 2}, icon="repeat", color="#06b6d4"),
    "bb_squeeze": NodeDefinition(id="bb_squeeze", name="Expansion / Contraction", type=NodeType.SOLVER, category="2. Confidence Solver'lar", description="Volatilite daralma/genişleme", inputs=[], outputs=[NodePort("score", "Skor (0-100)", "score", "output")], parameters={"bb_period": 20, "mode": "squeeze"}, icon="git-branch", color="#06b6d4"),
    "support_resistance": NodeDefinition(id="support_resistance", name="Support / Resistance", type=NodeType.SOLVER, category="2. Confidence Solver'lar", description="S/R seviyelerine yakınlık", inputs=[], outputs=[NodePort("score", "Skor (0-100)", "score", "output")], parameters={"lookback": 50, "mode": "support"}, icon="anchor", color="#06b6d4"),
}

# --- Logic Node'ları (Skorları birleştirir) ---
LOGIC_NODES = {
    "and": NodeDefinition(id="and", name="AND (Weakest Link)", type=NodeType.LOGIC, category="3. Logic Node'lar", description="Tüm girdiler eşiği geçmeli (En düşük skoru alır)", inputs=[NodePort("in1", "Girdi 1", "score", "input"), NodePort("in2", "Girdi 2", "score", "input")], outputs=[NodePort("score", "Skor (0-100)", "score", "output")], parameters={"threshold": 50}, icon="ampersand", color="#ef4444"),
    "or": NodeDefinition(id="or", name="OR (Max Skor)", type=NodeType.LOGIC, category="3. Logic Node'lar", description="Herhangi bir girdi eşiği geçer", inputs=[NodePort("in1", "Girdi 1", "score", "input"), NodePort("in2", "Girdi 2", "score", "input")], outputs=[NodePort("score", "Skor (0-100)", "score", "output")], parameters={"threshold": 50}, icon="plus", color="#ef4444"),
    "xor": NodeDefinition(id="xor", name="XOR (Special)", type=NodeType.LOGIC, category="3. Logic Node'lar", description="Sadece biri aktifken sinyal üretir", inputs=[NodePort("in1", "Girdi 1", "score", "input"), NodePort("in2", "Girdi 2", "score", "input")], outputs=[NodePort("score", "Skor (0-100)", "score", "output")], parameters={"threshold": 50}, icon="git-merge", color="#ef4444"),
    "additive": NodeDefinition(id="additive", name="Additive (Weighted)", type=NodeType.LOGIC, category="3. Logic Node'lar", description="Ağırlıklı toplam (Weight Slider)", inputs=[NodePort("in1", "Girdi 1", "score", "input"), NodePort("in2", "Girdi 2", "score", "input")], outputs=[NodePort("score", "Skor (0-100)", "score", "output")], parameters={"weight1": 0.5, "weight2": 0.5}, icon="plus-circle", color="#ef4444"),
}

# --- Function Node'lar ---
FUNCTION_NODES = {
    "inverter": NodeDefinition(id="inverter", name="Inverter (Ters Çevir)", type=NodeType.FUNCTION, category="4. Function Node'lar", description="Skoru ters çevirir (100 - skor)", inputs=[NodePort("score", "Skor", "score", "input")], outputs=[NodePort("score", "Skor (0-100)", "score", "output")], icon="refresh-cw", color="#f97316"),
    "lookback": NodeDefinition(id="lookback", name="Lookback", type=NodeType.FUNCTION, category="4. Function Node'lar", description="N bar öncesindeki skoru al", inputs=[NodePort("score", "Skor", "score", "input")], outputs=[NodePort("score", "Skor (0-100)", "score", "output")], parameters={"bars": 1}, icon="history", color="#f97316"),
    "signal_extender": NodeDefinition(id="signal_extender", name="Signal Extender", type=NodeType.FUNCTION, category="4. Function Node'lar", description="Sinyali N bar boyunca aktif tut", inputs=[NodePort("score", "Skor", "score", "input")], outputs=[NodePort("score", "Skor (0-100)", "score", "output")], parameters={"bars": 3}, icon="maximize-2", color="#f97316"),
}

# --- Çıktı Node'ları ---
OUTPUT_NODES = {
    "buy_signal": NodeDefinition(id="buy_signal", name="ALIŞ Sinyali (Long)", type=NodeType.OUTPUT, category="5. Sinyal Çıkışı", description="Eşik aşılınca ALIŞ", inputs=[NodePort("score", "Skor", "score", "input")], outputs=[], parameters={"threshold": 60}, icon="shopping-cart", color="#22c55e"),
    "sell_signal": NodeDefinition(id="sell_signal", name="SATIŞ Sinyali (Short)", type=NodeType.OUTPUT, category="5. Sinyal Çıkışı", description="Eşik aşılınca SATIŞ", inputs=[NodePort("score", "Skor", "score", "input")], outputs=[], parameters={"threshold": 60}, icon="trending-down", color="#ef4444"),
}

ALL_NODES = {**INDICATOR_NODES, **SOLVER_NODES, **LOGIC_NODES, **FUNCTION_NODES, **OUTPUT_NODES}

def get_node_categories() -> Dict[str, List[Dict]]:
    categories = {}
    for node_id, node_def in ALL_NODES.items():
        category = node_def.category
        if category not in categories:
            categories[category] = []
        categories[category].append({
            "id": node_id, "name": node_def.name, "description": node_def.description,
            "icon": node_def.icon, "color": node_def.color, "type": node_def.type.value,
            "inputs": [{"id": p.id, "name": p.name, "type": p.type} for p in node_def.inputs],
            "outputs": [{"id": p.id, "name": p.name, "type": p.type} for p in node_def.outputs],
            "parameters": node_def.parameters,
        })
    return categories