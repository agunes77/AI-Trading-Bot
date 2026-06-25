"""
Strateji Tasarım Modülü API Router
Görsel node editor + Pine Script kod editörü
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from strategy_builder.node_definitions import get_node_categories
from strategy_builder.storage import save_strategy, load_strategy, list_strategies, delete_strategy
from strategy_builder.executor import StrategyExecutor

router = APIRouter()


class StrategySaveRequest(BaseModel):
    id: str
    name: str
    description: str = ""
    mode: str = "visual"
    nodes: List[Dict] = []
    edges: List[Dict] = []
    pine_code: str = ""


class StrategyRunRequest(BaseModel):
    nodes: List[Dict] = []
    edges: List[Dict] = []
    source: str = "crypto"
    symbol: str = "BTC/USDT"
    timeframe: str = "1h"
    days: int = 365


class PineScriptRunRequest(BaseModel):
    pine_code: str
    source: str = "crypto"
    symbol: str = "BTC/USDT"
    timeframe: str = "1h"
    days: int = 365


@router.get("/nodes")
async def get_node_library():
    """Node kütüphanesini getir"""
    categories = get_node_categories()
    return {"categories": categories}


@router.get("/strategies")
async def get_strategies():
    """Kayıtlı stratejileri listele"""
    strategies = list_strategies()
    return {"strategies": strategies, "count": len(strategies)}


@router.get("/strategies/{strategy_id}")
async def get_strategy(strategy_id: str):
    """Strateji detayını getir"""
    strategy = load_strategy(strategy_id)
    if strategy is None:
        raise HTTPException(status_code=404, detail="Strateji bulunamadi")
    return strategy


@router.post("/strategies")
async def create_strategy(request: StrategySaveRequest):
    """Strateji kaydet"""
    strategy_data = {
        "name": request.name,
        "description": request.description,
        "mode": request.mode,
        "nodes": request.nodes,
        "edges": request.edges,
        "pine_code": request.pine_code,
    }
    
    success = save_strategy(request.id, strategy_data)
    if not success:
        raise HTTPException(status_code=500, detail="Strateji kaydedilemedi")
    
    return {"success": True, "id": request.id}


@router.put("/strategies/{strategy_id}")
async def update_strategy(strategy_id: str, request: StrategySaveRequest):
    """Strateji güncelle"""
    existing = load_strategy(strategy_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Strateji bulunamadi")
    
    strategy_data = {
        "name": request.name,
        "description": request.description,
        "mode": request.mode,
        "nodes": request.nodes,
        "edges": request.edges,
        "pine_code": request.pine_code,
        "created_at": existing.get("created_at"),
    }
    
    success = save_strategy(strategy_id, strategy_data)
    if not success:
        raise HTTPException(status_code=500, detail="Strateji guncellenemedi")
    
    return {"success": True, "id": strategy_id}


@router.delete("/strategies/{strategy_id}")
async def remove_strategy(strategy_id: str):
    """Strateji sil"""
    success = delete_strategy(strategy_id)
    if not success:
        raise HTTPException(status_code=404, detail="Strateji bulunamadi")
    return {"success": True}


@router.post("/run")
async def run_strategy(request: StrategyRunRequest):
    """Görsel stratejiyi çalıştır ve backtest et"""
    try:
        from data.data_manager import DataManager
        
        dm = DataManager()
        if request.source == "crypto":
            df = dm.get_crypto_data(request.symbol, request.timeframe, request.days)
        else:
            df = dm.get_forex_data(request.symbol, request.timeframe, request.days)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Veri bulunamadi")
        
        strategy = {
            "nodes": request.nodes,
            "edges": request.edges,
        }
        
        executor = StrategyExecutor()
        result = executor.execute(strategy, df)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pine/run")
async def run_pine_script(request: PineScriptRunRequest):
    """Pine Script kodunu çalıştır ve backtest et"""
    try:
        from data.data_manager import DataManager
        from pine_script.runner import PineScriptRunner
        
        dm = DataManager()
        if request.source == "crypto":
            df = dm.get_crypto_data(request.symbol, request.timeframe, request.days)
        else:
            df = dm.get_forex_data(request.symbol, request.timeframe, request.days)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Veri bulunamadi")
        
        runner = PineScriptRunner()
        result = runner.run(request.pine_code, df)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pine/presets")
async def get_pine_presets():
    """Hazır Pine Script presetlerini listele"""
    from pine_script.runner import TradingViewIndicatorPresets
    presets = TradingViewIndicatorPresets.list_presets()
    return {"presets": presets}


@router.get("/pine/presets/{preset_name}")
async def get_pine_preset(preset_name: str):
    """Belirli bir Pine Script presetini getir"""
    from pine_script.runner import TradingViewIndicatorPresets
    code = TradingViewIndicatorPresets.get_preset(preset_name)
    if code is None:
        raise HTTPException(status_code=404, detail="Preset bulunamadi")
    return {"name": preset_name, "code": code}


@router.post("/pine/parse")
async def parse_pine_script(request: PineScriptRunRequest):
    """Pine Script kodunu parse et ve Python koduna dönüştür"""
    try:
        from pine_script.parser import PineScriptParser
        
        parser = PineScriptParser()
        result = parser.parse(request.pine_code)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/strategies/{strategy_id}/run")
async def run_saved_strategy(strategy_id: str, request: StrategyRunRequest):
    """Kayıtlı stratejiyi çalıştır"""
    strategy = load_strategy(strategy_id)
    if strategy is None:
        raise HTTPException(status_code=404, detail="Strateji bulunamadi")
    
    try:
        from data.data_manager import DataManager
        
        dm = DataManager()
        if request.source == "crypto":
            df = dm.get_crypto_data(request.symbol, request.timeframe, request.days)
        else:
            df = dm.get_forex_data(request.symbol, request.timeframe, request.days)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Veri bulunamadi")
        
        if strategy.get("mode") == "code" and strategy.get("pine_code"):
            from pine_script.runner import PineScriptRunner
            runner = PineScriptRunner()
            result = runner.run(strategy["pine_code"], df)
        else:
            executor = StrategyExecutor()
            result = executor.execute(strategy, df)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
