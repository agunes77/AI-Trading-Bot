"""
TradingAgents LLM API Router
Multi-agent LLM karar motoru endpoint'leri
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

router = APIRouter()


class AnalysisRequest(BaseModel):
    ticker: str
    date: Optional[str] = None
    llm_provider: str = "openai"
    deep_think_model: Optional[str] = None
    quick_think_model: Optional[str] = None
    max_debate_rounds: int = 2


class ExecutionRequest(BaseModel):
    ticker: str
    date: Optional[str] = None
    source: str = "crypto"
    auto_execute: bool = False


@router.get("/status")
async def get_trading_agents_status():
    """TradingAgents durumu"""
    try:
        from agent.trading_agents_llm import TRADING_AGENTS_AVAILABLE
        return {
            "available": TRADING_AGENTS_AVAILABLE,
            "message": "TradingAgents hazir" if TRADING_AGENTS_AVAILABLE else "tradingagents paketi yuklu degil"
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


@router.get("/providers")
async def get_llm_providers():
    """Desteklenen LLM provider'lari listele"""
    return {
        "providers": [
            {"id": "openai", "name": "OpenAI", "models": ["gpt-5.5", "gpt-5.4", "gpt-5.4-mini"]},
            {"id": "anthropic", "name": "Anthropic", "models": ["claude-opus-4-8", "claude-sonnet-4-5"]},
            {"id": "google", "name": "Google", "models": ["gemini-3.1-pro", "gemini-3.1-flash"]},
            {"id": "deepseek", "name": "DeepSeek", "models": ["deepseek-r1", "deepseek-v3"]},
            {"id": "ollama", "name": "Ollama (Local)", "models": ["llama3.1", "qwen2.5"]},
            {"id": "openai_compatible", "name": "OpenAI Compatible", "models": ["custom"]},
        ]
    }


@router.post("/analyze")
async def analyze_with_trading_agents(request: AnalysisRequest):
    """TradingAgents ile analiz yap"""
    try:
        from agent.trading_agents_llm import TradingAgentsLLM, TRADING_AGENTS_AVAILABLE
        
        if not TRADING_AGENTS_AVAILABLE:
            raise HTTPException(status_code=503, detail="TradingAgents paketi yuklu degil")
        
        config = {
            "llm_provider": request.llm_provider,
            "max_debate_rounds": request.max_debate_rounds,
        }
        
        if request.deep_think_model:
            config["deep_think_llm"] = request.deep_think_model
        if request.quick_think_model:
            config["quick_think_llm"] = request.quick_think_model
        
        llm = TradingAgentsLLM(config=config)
        result = llm.analyze(request.ticker, request.date)
        
        return result
        
    except ImportError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_trading_agents_decision(request: ExecutionRequest):
    """TradingAgents kararini al ve uygula"""
    try:
        from agent.trading_agents_llm import TradingAgentsLLM, TradingAgentsBridge, TRADING_AGENTS_AVAILABLE
        from execution.risk_manager import RiskManager
        
        if not TRADING_AGENTS_AVAILABLE:
            raise HTTPException(status_code=503, detail="TradingAgents paketi yuklu degil")
        
        llm = TradingAgentsLLM()
        risk_manager = RiskManager()
        
        if request.source == "crypto":
            from broker.crypto_broker import CryptoBroker
            broker = CryptoBroker()
        elif request.source == "forex":
            from broker.forex_broker import ForexBroker
            broker = ForexBroker()
        else:
            raise HTTPException(status_code=400, detail=f"Kaynak desteklenmiyor: {request.source}")
        
        if not broker.connect():
            raise HTTPException(status_code=503, detail="Broker baglantisi basarisiz")
        
        bridge = TradingAgentsBridge(llm, risk_manager, broker)
        result = bridge.execute_decision(request.ticker, request.date)
        
        broker.disconnect()
        
        return result
        
    except ImportError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def get_agents_info():
    """TradingAgents agent bilgileri"""
    return {
        "agents": [
            {
                "name": "Fundamentals Analyst",
                "role": "Sirket finansallari ve performans metriklerini degerlendirir",
                "icon": "trending-up"
            },
            {
                "name": "Sentiment Analyst",
                "role": "Haber, StockTwits, Reddit duygu analizini yapar",
                "icon": "message-circle"
            },
            {
                "name": "News Analyst",
                "role": "Global haberleri ve makroekonomik gostergeleri izler",
                "icon": "newspaper"
            },
            {
                "name": "Technical Analyst",
                "role": "Teknik indikatorler ile alim-satim sinyalleri uretir",
                "icon": "bar-chart-2"
            },
            {
                "name": "Bullish Researcher",
                "role": "Yukarisini savunan arastirmaci",
                "icon": "arrow-up"
            },
            {
                "name": "Bearish Researcher",
                "role": "Asagisini savunan arastirmaci",
                "icon": "arrow-down"
            },
            {
                "name": "Trader",
                "role": "Analiz raporlarini birlestirip alim-satim karari verir",
                "icon": "briefcase"
            },
            {
                "name": "Risk Management",
                "role": "Piyasa volatilitesi ve likidite riskini degerlendirir",
                "icon": "shield"
            },
            {
                "name": "Portfolio Manager",
                "role": "Son karari verir ve islemi onaylar/reddeder",
                "icon": "award"
            }
        ]
    }
