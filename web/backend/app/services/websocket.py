from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import asyncio
import json
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@router.websocket("/prices")
async def websocket_prices(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        from data.crypto_data import CryptoDataFetcher
        
        fetcher = CryptoDataFetcher()
        symbols = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT"]
        
        while True:
            for symbol in symbols:
                try:
                    ticker = fetcher.fetch_ticker(symbol)
                    if ticker:
                        await websocket.send_json({
                            "type": "price_update",
                            "symbol": symbol,
                            "price": ticker.get("last", 0),
                            "change_24h": ticker.get("percentage", 0),
                            "volume_24h": ticker.get("quoteVolume", 0),
                            "timestamp": datetime.utcnow().isoformat(),
                        })
                except:
                    pass
            
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)

@router.websocket("/trades")
async def websocket_trades(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.send_json({
                "type": "trade_update",
                "message": "Trade verileri suan bos",
                "timestamp": datetime.utcnow().isoformat(),
            })
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)
