"""
Strateji Depolama
Stratejileri JSON olarak kaydetme ve yükleme
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from utils.logger import logger
from config.settings import BASE_DIR


STRATEGIES_DIR = BASE_DIR / "strategies"
STRATEGIES_DIR.mkdir(exist_ok=True)


def save_strategy(strategy_id: str, strategy_data: Dict) -> bool:
    """Stratejiyi kaydet"""
    try:
        strategy_data["updated_at"] = datetime.utcnow().isoformat()
        
        if "created_at" not in strategy_data:
            strategy_data["created_at"] = strategy_data["updated_at"]
        
        file_path = STRATEGIES_DIR / f"{strategy_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(strategy_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Strateji kaydedildi: {strategy_id}")
        return True
    except Exception as e:
        logger.error(f"Strateji kaydetme hatası: {e}")
        return False


def load_strategy(strategy_id: str) -> Optional[Dict]:
    """Stratejiyi yükle"""
    try:
        file_path = STRATEGIES_DIR / f"{strategy_id}.json"
        if not file_path.exists():
            return None
        
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Strateji yükleme hatası: {e}")
        return None


def list_strategies() -> List[Dict]:
    """Tüm stratejileri listele"""
    strategies = []
    try:
        for file_path in STRATEGIES_DIR.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    strategies.append({
                        "id": file_path.stem,
                        "name": data.get("name", "İsimsiz"),
                        "description": data.get("description", ""),
                        "created_at": data.get("created_at"),
                        "updated_at": data.get("updated_at"),
                        "node_count": len(data.get("nodes", [])),
                    })
            except Exception as e:
                logger.warning(f"Strateji okuma hatası {file_path}: {e}")
    except Exception as e:
        logger.error(f"Strateji listeleme hatası: {e}")
    
    return sorted(strategies, key=lambda x: x.get("updated_at", ""), reverse=True)


def delete_strategy(strategy_id: str) -> bool:
    """Stratejiyi sil"""
    try:
        file_path = STRATEGIES_DIR / f"{strategy_id}.json"
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Strateji silindi: {strategy_id}")
            return True
        return False
    except Exception as e:
        logger.error(f"Strateji silme hatası: {e}")
        return False
