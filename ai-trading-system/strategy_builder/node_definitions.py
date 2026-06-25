"""
Node Tanımları - Strateji Tasarım Modülü
BloodHound/SharkIndicator tarzı node-based strateji oluşturma
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class NodeType(Enum):
    INDICATOR = "indicator"
    LOGIC = "logic"
    FUNCTION = "function"
    CONFIDENCE = "confidence"
    OUTPUT = "output"


@dataclass
class NodePort:
    id: str
    name: str
    type: str
    direction: str  # "input" veya "output"


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
    color: str = "#3b82f6"


# İndikatör Node'ları
INDICATOR_NODES = {
    "sma": NodeDefinition(
        id="sma",
        name="SMA (Simple Moving Average)",
        type=NodeType.INDICATOR,
        category="Trend",
        description="Basit Hareketli Ortalama",
        inputs=[NodePort("price", "Fiyat", "series", "input")],
        outputs=[NodePort("value", "SMA Değeri", "series", "output")],
        parameters={"period": 20},
        icon="trending-up",
        color="#3b82f6"
    ),
    "ema": NodeDefinition(
        id="ema",
        name="EMA (Exponential Moving Average)",
        type=NodeType.INDICATOR,
        category="Trend",
        description="Üstel Hareketli Ortalama",
        inputs=[NodePort("price", "Fiyat", "series", "input")],
        outputs=[NodePort("value", "EMA Değeri", "series", "output")],
        parameters={"period": 20},
        icon="trending-up",
        color="#3b82f6"
    ),
    "rsi": NodeDefinition(
        id="rsi",
        name="RSI (Relative Strength Index)",
        type=NodeType.INDICATOR,
        category="Momentum",
        description="Göreceli Güç Endeksi",
        inputs=[NodePort("price", "Fiyat", "series", "input")],
        outputs=[NodePort("value", "RSI Değeri", "series", "output")],
        parameters={"period": 14},
        icon="activity",
        color="#a855f7"
    ),
    "macd": NodeDefinition(
        id="macd",
        name="MACD",
        type=NodeType.INDICATOR,
        category="Trend",
        description="Moving Average Convergence Divergence",
        inputs=[NodePort("price", "Fiyat", "series", "input")],
        outputs=[
            NodePort("macd", "MACD", "series", "output"),
            NodePort("signal", "Signal", "series", "output"),
            NodePort("histogram", "Histogram", "series", "output")
        ],
        parameters={"fast": 12, "slow": 26, "signal": 9},
        icon="bar-chart-2",
        color="#3b82f6"
    ),
    "bollinger": NodeDefinition(
        id="bollinger",
        name="Bollinger Bands",
        type=NodeType.INDICATOR,
        category="Volatility",
        description="Bollinger Bantları",
        inputs=[NodePort("price", "Fiyat", "series", "input")],
        outputs=[
            NodePort("upper", "Üst Bant", "series", "output"),
            NodePort("middle", "Orta Bant", "series", "output"),
            NodePort("lower", "Alt Bant", "series", "output")
        ],
        parameters={"period": 20, "std_dev": 2.0},
        icon="git-branch",
        color="#eab308"
    ),
    "atr": NodeDefinition(
        id="atr",
        name="ATR (Average True Range)",
        type=NodeType.INDICATOR,
        category="Volatility",
        description="Ortalama Gerçek Aralık",
        inputs=[
            NodePort("high", "Yüksek", "series", "input"),
            NodePort("low", "Düşük", "series", "input"),
            NodePort("close", "Kapanış", "series", "input")
        ],
        outputs=[NodePort("value", "ATR Değeri", "series", "output")],
        parameters={"period": 14},
        icon="zap",
        color="#eab308"
    ),
    "stochastic": NodeDefinition(
        id="stochastic",
        name="Stochastic Oscillator",
        type=NodeType.INDICATOR,
        category="Momentum",
        description="Stokastik Osilatör",
        inputs=[
            NodePort("high", "Yüksek", "series", "input"),
            NodePort("low", "Düşük", "series", "input"),
            NodePort("close", "Kapanış", "series", "input")
        ],
        outputs=[
            NodePort("k", "%K", "series", "output"),
            NodePort("d", "%D", "series", "output")
        ],
        parameters={"k_period": 14, "d_period": 3},
        icon="activity",
        color="#a855f7"
    ),
    "volume": NodeDefinition(
        id="volume",
        name="Volume",
        type=NodeType.INDICATOR,
        category="Volume",
        description="Hacim İndikatörü",
        inputs=[NodePort("volume", "Hacim", "series", "input")],
        outputs=[NodePort("value", "Hacim", "series", "output")],
        parameters={},
        icon="bar-chart",
        color="#22c55e"
    ),
}

# Mantık Node'ları
LOGIC_NODES = {
    "and": NodeDefinition(
        id="and",
        name="AND",
        type=NodeType.LOGIC,
        category="Mantık",
        description="VE Mantığı - Tüm koşullar doğru olmalı",
        inputs=[
            NodePort("input1", "Girdi 1", "boolean", "input"),
            NodePort("input2", "Girdi 2", "boolean", "input")
        ],
        outputs=[NodePort("output", "Çıktı", "boolean", "output")],
        icon="ampersand",
        color="#ef4444"
    ),
    "or": NodeDefinition(
        id="or",
        name="OR",
        type=NodeType.LOGIC,
        category="Mantık",
        description="VEYA Mantığı - En az bir koşul doğru olmalı",
        inputs=[
            NodePort("input1", "Girdi 1", "boolean", "input"),
            NodePort("input2", "Girdi 2", "boolean", "input")
        ],
        outputs=[NodePort("output", "Çıktı", "boolean", "output")],
        icon="plus",
        color="#ef4444"
    ),
    "xor": NodeDefinition(
        id="xor",
        name="XOR",
        type=NodeType.LOGIC,
        category="Mantık",
        description="ÖZEL VEYA - Sadece biri doğru olmalı",
        inputs=[
            NodePort("input1", "Girdi 1", "boolean", "input"),
            NodePort("input2", "Girdi 2", "boolean", "input")
        ],
        outputs=[NodePort("output", "Çıktı", "boolean", "output")],
        icon="git-merge",
        color="#ef4444"
    ),
    "not": NodeDefinition(
        id="not",
        name="NOT",
        type=NodeType.LOGIC,
        category="Mantık",
        description="DEĞİL - Tersine çevir",
        inputs=[NodePort("input", "Girdi", "boolean", "input")],
        outputs=[NodePort("output", "Çıktı", "boolean", "output")],
        icon="minus",
        color="#ef4444"
    ),
}

# Confidence Solver Node'ları
CONFIDENCE_NODES = {
    "crossover": NodeDefinition(
        id="crossover",
        name="Crossover",
        type=NodeType.CONFIDENCE,
        category="Confidence Solver",
        description="Kesişim Algılama",
        inputs=[
            NodePort("series1", "Seri 1", "series", "input"),
            NodePort("series2", "Seri 2", "series", "input")
        ],
        outputs=[NodePort("signal", "Sinyal", "boolean", "output")],
        parameters={"direction": "above"},
        icon="git-merge",
        color="#06b6d4"
    ),
    "comparison": NodeDefinition(
        id="comparison",
        name="Comparison",
        type=NodeType.CONFIDENCE,
        category="Confidence Solver",
        description="Değer Karşılaştırma",
        inputs=[
            NodePort("value1", "Değer 1", "number", "input"),
            NodePort("value2", "Değer 2", "number", "input")
        ],
        outputs=[NodePort("result", "Sonuç", "boolean", "output")],
        parameters={"operator": ">"},
        icon="git-compare",
        color="#06b6d4"
    ),
    "threshold": NodeDefinition(
        id="threshold",
        name="Threshold",
        type=NodeType.CONFIDENCE,
        category="Confidence Solver",
        description="Eşik Değer Kontrolü",
        inputs=[NodePort("value", "Değer", "number", "input")],
        outputs=[NodePort("signal", "Sinyal", "boolean", "output")],
        parameters={"threshold": 50, "condition": "above"},
        icon="sliders",
        color="#06b6d4"
    ),
    "slope": NodeDefinition(
        id="slope",
        name="Slope",
        type=NodeType.CONFIDENCE,
        category="Confidence Solver",
        description="Eğim Kontrolü",
        inputs=[NodePort("series", "Seri", "series", "input")],
        outputs=[NodePort("signal", "Sinyal", "boolean", "output")],
        parameters={"period": 5, "direction": "up"},
        icon="trending-up",
        color="#06b6d4"
    ),
}

# Fonksiyon Node'ları
FUNCTION_NODES = {
    "lookback": NodeDefinition(
        id="lookback",
        name="Lookback",
        type=NodeType.FUNCTION,
        category="Fonksiyon",
        description="Geriye Dönük Bakış",
        inputs=[NodePort("series", "Seri", "series", "input")],
        outputs=[NodePort("value", "Değer", "number", "output")],
        parameters={"bars": 1},
        icon="history",
        color="#f97316"
    ),
    "max": NodeDefinition(
        id="max",
        name="Max",
        type=NodeType.FUNCTION,
        category="Fonksiyon",
        description="Maksimum Değer",
        inputs=[NodePort("series", "Seri", "series", "input")],
        outputs=[NodePort("value", "Maksimum", "number", "output")],
        parameters={"period": 20},
        icon="arrow-up",
        color="#f97316"
    ),
    "min": NodeDefinition(
        id="min",
        name="Min",
        type=NodeType.FUNCTION,
        category="Fonksiyon",
        description="Minimum Değer",
        inputs=[NodePort("series", "Seri", "series", "input")],
        outputs=[NodePort("value", "Minimum", "number", "output")],
        parameters={"period": 20},
        icon="arrow-down",
        color="#f97316"
    ),
}

# Çıktı Node'ları
OUTPUT_NODES = {
    "buy_signal": NodeDefinition(
        id="buy_signal",
        name="BUY Signal",
        type=NodeType.OUTPUT,
        category="Çıktı",
        description="Alış Sinyali",
        inputs=[NodePort("condition", "Koşul", "boolean", "input")],
        outputs=[],
        icon="shopping-cart",
        color="#22c55e"
    ),
    "sell_signal": NodeDefinition(
        id="sell_signal",
        name="SELL Signal",
        type=NodeType.OUTPUT,
        category="Çıktı",
        description="Satış Sinyali",
        inputs=[NodePort("condition", "Koşul", "boolean", "input")],
        outputs=[],
        icon="trending-down",
        color="#ef4444"
    ),
}

# Tüm node'ları birleştir
ALL_NODES = {
    **INDICATOR_NODES,
    **LOGIC_NODES,
    **CONFIDENCE_NODES,
    **FUNCTION_NODES,
    **OUTPUT_NODES,
}


def get_node_categories() -> Dict[str, List[Dict]]:
    """Node'ları kategorilere göre grupla"""
    categories = {}
    for node_id, node_def in ALL_NODES.items():
        category = node_def.category
        if category not in categories:
            categories[category] = []
        categories[category].append({
            "id": node_id,
            "name": node_def.name,
            "description": node_def.description,
            "icon": node_def.icon,
            "color": node_def.color,
            "type": node_def.type.value,
            "inputs": [{"id": p.id, "name": p.name, "type": p.type} for p in node_def.inputs],
            "outputs": [{"id": p.id, "name": p.name, "type": p.type} for p in node_def.outputs],
            "parameters": node_def.parameters,
        })
    return categories


def get_node_definition(node_id: str) -> Optional[NodeDefinition]:
    """Node tanımını getir"""
    return ALL_NODES.get(node_id)
