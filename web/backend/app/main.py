from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.routers import dashboard, prices, strategies, trades, ai_models, ensemble, news, risk, data, trading_agents, strategy_builder
from app.services.websocket import router as ws_router

app = FastAPI(title="AI Trading System API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(prices.router, prefix="/api/prices", tags=["prices"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["strategies"])
app.include_router(trades.router, prefix="/api/trades", tags=["trades"])
app.include_router(ai_models.router, prefix="/api/ai", tags=["ai"])
app.include_router(ensemble.router, prefix="/api/ensemble", tags=["ensemble"])
app.include_router(news.router, prefix="/api/news", tags=["news"])
app.include_router(risk.router, prefix="/api/risk", tags=["risk"])
app.include_router(data.router, prefix="/api/data", tags=["data"])
app.include_router(trading_agents.router, prefix="/api/trading-agents", tags=["trading-agents"])
app.include_router(strategy_builder.router, prefix="/api/strategy-builder", tags=["strategy-builder"])
app.include_router(ws_router, prefix="/ws", tags=["websocket"])

frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api")
async def api_root():
    return {"message": "AI Trading System API", "version": "2.0.0"}


if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(frontend_dist / "index.html")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
else:
    @app.get("/")
    async def root():
        return {"message": "AI Trading System API", "version": "2.0.0", "docs": "/docs"}
