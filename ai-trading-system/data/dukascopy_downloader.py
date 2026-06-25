"""
Dukascopy Veri Indirme Modulu
dukascopy-node CLI kullanarak gecmis tick verisi indirir
"""
import subprocess
import json
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from utils.logger import logger
from config.settings import DATA_DIR


class DukascopyDownloader:
    """Dukascopy'den gecmis veri indirme"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or DATA_DIR / "dukascopy"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._check_dukascopy_installed()
    
    def _check_dukascopy_installed(self):
        """dukascopy-node'un yuklu olup olmadigini kontrol et"""
        try:
            result = subprocess.run(
                ["npx", "dukascopy-node", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info(f"dukascopy-node bulundu: {result.stdout.strip()}")
                return True
        except Exception as e:
            logger.warning(f"dukascopy-node bulunamadi: {e}")
        
        logger.warning("dukascopy-node yuklu degil. npm install -g dukascopy-node ile yukleyin.")
        return False
    
    def download(
        self,
        instrument: str,
        start_date: str,
        end_date: str,
        timeframe: str = "tick",
        format: str = "csv"
    ) -> Optional[Path]:
        """
        Dukascopy'den veri indir
        
        Args:
            instrument: Enstrüman (örn: "EURUSD", "BTCUSD", "AAPL")
            start_date: Başlangıç tarihi (YYYY-MM-DD)
            end_date: Bitiş tarihi (YYYY-MM-DD)
            timeframe: "tick", "minutely", "hourly", "daily"
            format: "csv" veya "json"
        
        Returns:
            İndirilen dosyanın yolu
        """
        output_file = self.output_dir / f"{instrument}_{start_date}_{end_date}_{timeframe}.{format}"
        
        if output_file.exists():
            logger.info(f"Veri zaten mevcut: {output_file}")
            return output_file
        
        cmd = [
            "npx", "dukascopy-node",
            "-i", instrument,
            "-d", start_date,
            "-to", end_date,
            "-t", timeframe,
            "-f", format,
            "-o", str(self.output_dir)
        ]
        
        try:
            logger.info(f"Dukascopy indirme basliyor: {instrument} ({start_date} - {end_date})")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error(f"Dukascopy indirme hatasi: {result.stderr}")
                return None
            
            logger.info(f"Dukascopy indirme tamamlandi: {output_file}")
            return output_file
            
        except subprocess.TimeoutExpired:
            logger.error("Dukascopy indirme zaman asimina ugradi")
            return None
        except Exception as e:
            logger.error(f"Dukascopy indirme hatasi: {e}")
            return None
    
    def load_data(self, file_path: Path) -> Optional[pd.DataFrame]:
        """İndirilen veriyi pandas DataFrame'e yükle"""
        if not file_path.exists():
            logger.error(f"Dosya bulunamadi: {file_path}")
            return None
        
        try:
            if file_path.suffix == ".csv":
                df = pd.read_csv(file_path)
            elif file_path.suffix == ".json":
                df = pd.read_json(file_path)
            else:
                logger.error(f"Desteklenmeyen format: {file_path.suffix}")
                return None
            
            df = self._normalize_dataframe(df)
            logger.info(f"Veri yuklendi: {len(df)} satir")
            return df
            
        except Exception as e:
            logger.error(f"Veri yukleme hatasi: {e}")
            return None
    
    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """DataFrame'i standart formata dönüştür"""
        column_mapping = {
            "timestamp": "timestamp",
            "time": "timestamp",
            "date": "timestamp",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
            "bid": "bid",
            "ask": "ask",
        }
        
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.set_index("timestamp")
        
        df = df.sort_index()
        
        return df
    
    def get_available_instruments(self) -> List[str]:
        """Mevcut enstrümanları listele"""
        try:
            result = subprocess.run(
                ["npx", "dukascopy-node", "--instruments"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                instruments = result.stdout.strip().split("\n")
                return [i.strip() for i in instruments if i.strip()]
        except Exception as e:
            logger.error(f"Enstrüman listesi alinamadi: {e}")
        
        return []
    
    def list_downloaded_data(self) -> List[Dict]:
        """İndirilmiş verileri listele"""
        files = list(self.output_dir.glob("*.*"))
        
        data_list = []
        for file in files:
            if file.suffix in [".csv", ".json"]:
                stat = file.stat()
                data_list.append({
                    "filename": file.name,
                    "path": str(file),
                    "size_mb": stat.st_size / (1024 * 1024),
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return sorted(data_list, key=lambda x: x["modified"], reverse=True)
    
    def delete_data(self, filename: str) -> bool:
        """İndirilmiş veriyi sil"""
        file_path = self.output_dir / filename
        
        if not file_path.exists():
            logger.error(f"Dosya bulunamadi: {file_path}")
            return False
        
        try:
            file_path.unlink()
            logger.info(f"Veri silindi: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Veri silme hatasi: {e}")
            return False


class DataManager:
    """Merkezi veri yönetimi"""
    
    def __init__(self):
        self.dukascopy = DukascopyDownloader()
    
    def fetch_data(
        self,
        source: str,
        instrument: str,
        start_date: str,
        end_date: str,
        timeframe: str = "hourly"
    ) -> Optional[pd.DataFrame]:
        """
        Veri kaynağından veri çek
        
        Args:
            source: "dukascopy", "binance", "mt5"
            instrument: Enstrüman
            start_date: Başlangıç tarihi
            end_date: Bitiş tarihi
            timeframe: Zaman dilimi
        
        Returns:
            pandas DataFrame
        """
        if source == "dukascopy":
            return self._fetch_dukascopy(instrument, start_date, end_date, timeframe)
        elif source == "binance":
            return self._fetch_binance(instrument, start_date, end_date, timeframe)
        elif source == "mt5":
            return self._fetch_mt5(instrument, start_date, end_date, timeframe)
        else:
            logger.error(f"Bilinmeyen veri kaynagi: {source}")
            return None
    
    def _fetch_dukascopy(self, instrument: str, start_date: str, end_date: str, timeframe: str) -> Optional[pd.DataFrame]:
        file_path = self.dukascopy.download(instrument, start_date, end_date, timeframe)
        if file_path:
            return self.dukascopy.load_data(file_path)
        return None
    
    def _fetch_binance(self, instrument: str, start_date: str, end_date: str, timeframe: str) -> Optional[pd.DataFrame]:
        try:
            from data.crypto_data import CryptoDataFetcher
            fetcher = CryptoDataFetcher()
            
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            
            df = fetcher.fetch_historical(instrument, timeframe, start, end)
            return df
        except Exception as e:
            logger.error(f"Binance veri cekme hatasi: {e}")
            return None
    
    def _fetch_mt5(self, instrument: str, start_date: str, end_date: str, timeframe: str) -> Optional[pd.DataFrame]:
        try:
            from data.forex_data import ForexDataFetcher
            fetcher = ForexDataFetcher()
            
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            
            df = fetcher.fetch_historical(instrument, timeframe, start, end)
            return df
        except Exception as e:
            logger.error(f"MT5 veri cekme hatasi: {e}")
            return None
    
    def list_all_data(self) -> Dict[str, List[Dict]]:
        """Tüm indirilmiş verileri listele"""
        return {
            "dukascopy": self.dukascopy.list_downloaded_data()
        }
    
    def delete_data(self, source: str, filename: str) -> bool:
        """Veri sil"""
        if source == "dukascopy":
            return self.dukascopy.delete_data(filename)
        else:
            logger.error(f"Bilinmeyen veri kaynagi: {source}")
            return False
