"""
Veri Yonetimi API Router
Dukascopy ve diger veri kaynaklari icin endpoint'ler
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

router = APIRouter()


class DownloadRequest(BaseModel):
    source: str = "dukascopy"
    instrument: str
    start_date: str
    end_date: str
    timeframe: str = "hourly"


class DataInfo(BaseModel):
    filename: str
    path: str
    size_mb: float
    created: str
    modified: str


@router.get("/sources")
async def get_data_sources():
    """Mevcut veri kaynaklarini listele"""
    return {
        "sources": [
            {
                "id": "dukascopy",
                "name": "Dukascopy",
                "description": "1000+ enstrüman, tick verisi, 1990'dan bugüne",
                "instruments_count": 1000,
                "since_year": 1990,
                "formats": ["csv", "json"],
                "timeframes": ["tick", "minutely", "hourly", "daily"]
            },
            {
                "id": "binance",
                "name": "Binance",
                "description": "Kripto para borsasi, OHLCV verisi",
                "instruments_count": 500,
                "since_year": 2017,
                "formats": ["json"],
                "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"]
            },
            {
                "id": "mt5",
                "name": "MetaTrader 5",
                "description": "Forex broker verisi",
                "instruments_count": 100,
                "since_year": 2010,
                "formats": ["json"],
                "timeframes": ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]
            }
        ]
    }


@router.get("/dukascopy/instruments")
async def get_dukascopy_instruments():
    """Dukascopy mevcut enstrümanlarini listele"""
    try:
        from data.dukascopy_downloader import DukascopyDownloader
        downloader = DukascopyDownloader()
        instruments = downloader.get_available_instruments()
        return {
            "instruments": instruments,
            "count": len(instruments)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download")
async def download_data(request: DownloadRequest, background_tasks: BackgroundTasks):
    """Veri indir (arka planda)"""
    try:
        from data.dukascopy_downloader import DataManager
        
        manager = DataManager()
        
        background_tasks.add_task(
            manager.fetch_data,
            request.source,
            request.instrument,
            request.start_date,
            request.end_date,
            request.timeframe
        )
        
        return {
            "status": "started",
            "message": f"{request.instrument} verisi indiriliyor...",
            "source": request.source,
            "instrument": request.instrument,
            "date_range": f"{request.start_date} - {request.end_date}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/downloaded")
async def list_downloaded_data():
    """Indirilmis verileri listele"""
    try:
        from data.dukascopy_downloader import DataManager
        manager = DataManager()
        data = manager.list_all_data()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/downloaded/{source}")
async def list_source_data(source: str):
    """Belirli kaynaktan indirilmis verileri listele"""
    try:
        from data.dukascopy_downloader import DataManager
        manager = DataManager()
        data = manager.list_all_data()
        return data.get(source, [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/downloaded/{source}/{filename}")
async def delete_data(source: str, filename: str):
    """Indirilmis veriyi sil"""
    try:
        from data.dukascopy_downloader import DataManager
        manager = DataManager()
        success = manager.delete_data(source, filename)
        
        if success:
            return {"status": "deleted", "filename": filename}
        else:
            raise HTTPException(status_code=404, detail="Dosya bulunamadi")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview/{source}/{filename}")
async def preview_data(source: str, filename: str, rows: int = 100):
    """Indirilmis verinin onizlemesini goster"""
    try:
        from data.dukascopy_downloader import DataManager
        from pathlib import Path
        
        manager = DataManager()
        
        if source == "dukascopy":
            file_path = manager.dukascopy.output_dir / filename
            df = manager.dukascopy.load_data(file_path)
        else:
            raise HTTPException(status_code=400, detail=f"Kaynak desteklenmiyor: {source}")
        
        if df is None:
            raise HTTPException(status_code=404, detail="Veri yuklenemedi")
        
        preview = df.head(rows).reset_index()
        
        return {
            "filename": filename,
            "source": source,
            "total_rows": len(df),
            "preview_rows": len(preview),
            "columns": list(df.columns),
            "data": preview.to_dict(orient="records")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
