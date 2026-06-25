"""
TradingAgents LLM Multi-Agent Entegrasyonu
TradingAgents framework'ü sistemimize entegre eder.
"""
import os
from typing import Optional, Dict, Any
from datetime import datetime
from utils.logger import logger

try:
    from tradingagents.graph.trading_graph import TradingAgentsGraph
    from tradingagents.default_config import DEFAULT_CONFIG
    TRADING_AGENTS_AVAILABLE = True
except ImportError:
    TRADING_AGENTS_AVAILABLE = False
    logger.warning("tradingagents paketi yuklu degil. pip install tradingagents")


class TradingAgentsLLM:
    """TradingAgents LLM Multi-Agent Karar Motoru"""
    
    def __init__(self, config: Optional[Dict] = None):
        if not TRADING_AGENTS_AVAILABLE:
            raise ImportError("tradingagents paketi yuklu degil")
        
        self.config = config or DEFAULT_CONFIG.copy()
        self.graph = None
        self._init_graph()
    
    def _init_graph(self):
        """TradingAgents graph'ini başlat"""
        try:
            self.graph = TradingAgentsGraph(debug=False, config=self.config)
            logger.info("TradingAgents LLM motoru basarili")
        except Exception as e:
            logger.error(f"TradingAgents baslatma hatasi: {e}")
            raise
    
    def analyze(self, ticker: str, date: Optional[str] = None) -> Dict[str, Any]:
        """
        TradingAgents ile detaylı analiz yap
        
        Args:
            ticker: Sembol (örn: "AAPL", "BTC-USD", "EURUSD")
            date: Analiz tarihi (YYYY-MM-DD formatında)
        
        Returns:
            Karar ve analiz detayları
        """
        if not self.graph:
            raise RuntimeError("TradingAgents graph baslatilmamis")
        
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            logger.info(f"TradingAgents analiz basliyor: {ticker} @ {date}")
            state, decision = self.graph.propagate(ticker, date)
            
            result = {
                "ticker": ticker,
                "date": date,
                "decision": decision,
                "state": self._extract_state(state),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"TradingAgents karar: {decision}")
            return result
            
        except Exception as e:
            logger.error(f"TradingAgents analiz hatasi: {e}")
            return {
                "ticker": ticker,
                "date": date,
                "decision": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_state(self, state: Dict) -> Dict:
        """State'ten önemli bilgileri çıkar"""
        return {
            "technical_analysis": state.get("technical_analysis", {}),
            "fundamental_analysis": state.get("fundamental_analysis", {}),
            "sentiment_analysis": state.get("sentiment_analysis", {}),
            "news_analysis": state.get("news_analysis", {}),
            "research_debate": state.get("research_debate", {}),
            "trader_decision": state.get("trader_decision", {}),
            "risk_assessment": state.get("risk_assessment", {}),
            "portfolio_decision": state.get("portfolio_manager", {}),
        }
    
    def update_config(self, **kwargs):
        """Config'i güncelle"""
        self.config.update(kwargs)
        self._init_graph()
        logger.info(f"TradingAgents config guncellendi: {kwargs}")


class TradingAgentsBridge:
    """
    TradingAgents ile mevcut sistem arasında köprü
    LLM kararlarını bizim risk yönetimi ve broker sistemimize bağlar
    """
    
    def __init__(self, llm: TradingAgentsLLM, risk_manager, broker):
        self.llm = llm
        self.risk_manager = risk_manager
        self.broker = broker
    
    def execute_decision(self, ticker: str, date: Optional[str] = None) -> Dict[str, Any]:
        """
        TradingAgents kararını al ve uygula
        
        1. LLM analizi yap
        2. Risk kontrolü yap
        3. Broker üzerinden işlem yap
        """
        analysis = self.llm.analyze(ticker, date)
        
        if analysis.get("decision") == "ERROR":
            return {"status": "error", "message": analysis.get("error")}
        
        decision = analysis["decision"]
        
        if decision == "BUY":
            return self._execute_buy(ticker, analysis)
        elif decision == "SELL":
            return self._execute_sell(ticker, analysis)
        else:
            return {"status": "hold", "decision": decision, "analysis": analysis}
    
    def _execute_buy(self, ticker: str, analysis: Dict) -> Dict[str, Any]:
        """BUY kararını uygula"""
        can_trade, reason = self.risk_manager.can_open_trade(ticker)
        
        if not can_trade:
            return {
                "status": "blocked",
                "decision": "BUY",
                "reason": reason,
                "analysis": analysis
            }
        
        balance = self.broker.get_balance()
        position_size = self.risk_manager.calculate_position_size(balance["available"], ticker)
        
        order = self.broker.place_order(ticker, "BUY", position_size)
        
        return {
            "status": "executed",
            "decision": "BUY",
            "order": order,
            "analysis": analysis
        }
    
    def _execute_sell(self, ticker: str, analysis: Dict) -> Dict[str, Any]:
        """SELL kararını uygula"""
        positions = self.broker.get_positions()
        position = next((p for p in positions if p["symbol"] == ticker), None)
        
        if not position:
            return {
                "status": "no_position",
                "decision": "SELL",
                "message": "Satis yapilacak pozisyon yok",
                "analysis": analysis
            }
        
        order = self.broker.place_order(ticker, "SELL", position["quantity"])
        
        return {
            "status": "executed",
            "decision": "SELL",
            "order": order,
            "analysis": analysis
        }
