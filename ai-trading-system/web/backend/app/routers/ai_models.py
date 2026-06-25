from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

router = APIRouter()

class TrainRequest(BaseModel):
    source: str
    symbol: str
    algorithm: str = "PPO"
    timeframe: str = "1h"
    days: int = 365
    timesteps: int = 100000

class ModelInfo(BaseModel):
    name: str
    algorithm: str
    created_at: Optional[str] = None
    performance: Optional[dict] = None

@router.get("/models")
async def list_models():
    try:
        from config.settings import MODELS_DIR
        
        models = []
        if MODELS_DIR.exists():
            for f in MODELS_DIR.glob("*.zip"):
                models.append({
                    "name": f.stem,
                    "path": str(f),
                    "size_mb": f.stat().st_size / (1024 * 1024),
                    "created_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                })
        
        return {"models": models, "count": len(models)}
    except Exception as e:
        return {"models": [], "error": str(e)}

@router.post("/train")
async def train_model(request: TrainRequest):
    try:
        from data.data_manager import DataManager
        from features.technical_indicators import FeatureEngineer
        from agent.rl_agent import RLAgent
        from config.settings import MODELS_DIR
        
        dm = DataManager()
        if request.source == "crypto":
            df = dm.get_crypto_data(request.symbol, request.timeframe, request.days)
        else:
            df = dm.get_forex_data(request.symbol, request.timeframe, request.days)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Veri bulunamadi")
        
        fe = FeatureEngineer()
        df_features = fe.add_all_indicators(df)
        feature_cols = [c for c in fe.get_feature_columns() if c in df_features.columns]
        df_clean = df_features.dropna(subset=feature_cols)
        
        split = int(len(df_clean) * 0.8)
        train_df = df_clean.iloc[:split]
        eval_df = df_clean.iloc[split:]
        
        agent = RLAgent(algorithm=request.algorithm)
        agent.train(
            df=train_df,
            feature_columns=feature_cols,
            total_timesteps=request.timesteps,
            eval_df=eval_df,
        )
        
        model_name = f"agent_{request.symbol.replace('/', '_')}_{request.algorithm}"
        model_path = str(MODELS_DIR / model_name)
        agent.save(model_path)
        
        return {
            "success": True,
            "message": f"Model egitildi ve kaydedildi: {model_name}",
            "model_path": model_path,
            "train_size": len(train_df),
            "eval_size": len(eval_df),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model/{model_name}")
async def get_model_info(model_name: str):
    try:
        from config.settings import MODELS_DIR
        
        model_path = MODELS_DIR / f"{model_name}.zip"
        if not model_path.exists():
            raise HTTPException(status_code=404, detail="Model bulunamadi")
        
        return {
            "name": model_name,
            "path": str(model_path),
            "size_mb": model_path.stat().st_size / (1024 * 1024),
            "created_at": datetime.fromtimestamp(model_path.stat().st_mtime).isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/model/{model_name}")
async def delete_model(model_name: str):
    try:
        from config.settings import MODELS_DIR
        
        model_path = MODELS_DIR / f"{model_name}.zip"
        if model_path.exists():
            model_path.unlink()
            return {"success": True, "message": f"Model silindi: {model_name}"}
        else:
            raise HTTPException(status_code=404, detail="Model bulunamadi")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
