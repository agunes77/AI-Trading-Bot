import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data_cache"

for d in [MODELS_DIR, LOGS_DIR, DATA_DIR]:
    d.mkdir(exist_ok=True)

BINANCE_CONFIG = {
    "api_key": os.getenv("BINANCE_API_KEY", ""),
    "api_secret": os.getenv("BINANCE_API_SECRET", ""),
    "sandbox": os.getenv("BINANCE_SANDBOX", "true").lower() == "true",
    "default_timeframe": os.getenv("BINANCE_TIMEFRAME", "1h"),
    "symbols": os.getenv("BINANCE_SYMBOLS", "BTC/USDT,ETH/USDT,BNB/USDT").split(","),
}

MT5_CONFIG = {
    "login": int(os.getenv("MT5_LOGIN", "0")),
    "password": os.getenv("MT5_PASSWORD", ""),
    "server": os.getenv("MT5_SERVER", ""),
    "path": os.getenv("MT5_PATH", r"C:\Program Files\MetaTrader 5\terminal64.exe"),
    "default_timeframe": os.getenv("MT5_TIMEFRAME", "H1"),
    "symbols": os.getenv("MT5_SYMBOLS", "EURUSD,GBPUSD,USDJPY").split(","),
}

RL_CONFIG = {
    "algorithm": os.getenv("RL_ALGORITHM", "PPO"),
    "total_timesteps": int(os.getenv("RL_TIMESTEPS", "100000")),
    "learning_rate": float(os.getenv("RL_LR", "3e-4")),
    "batch_size": int(os.getenv("RL_BATCH_SIZE", "64")),
    "n_steps": int(os.getenv("RL_N_STEPS", "2048")),
    "gamma": float(os.getenv("RL_GAMMA", "0.99")),
    "model_path": os.getenv("RL_MODEL_PATH", str(MODELS_DIR / "trading_agent")),
}

RISK_CONFIG = {
    "max_position_pct": float(os.getenv("RISK_MAX_POSITION_PCT", "0.02")),
    "max_daily_loss_pct": float(os.getenv("RISK_MAX_DAILY_LOSS_PCT", "0.05")),
    "max_weekly_loss_pct": float(os.getenv("RISK_MAX_WEEKLY_LOSS_PCT", "0.10")),
    "max_open_trades": int(os.getenv("RISK_MAX_OPEN_TRADES", "3")),
    "stop_loss_pct": float(os.getenv("RISK_STOP_LOSS_PCT", "0.02")),
    "take_profit_pct": float(os.getenv("RISK_TAKE_PROFIT_PCT", "0.04")),
    "trailing_stop_pct": float(os.getenv("RISK_TRAILING_STOP_PCT", "0.015")),
    "max_correlation": float(os.getenv("RISK_MAX_CORRELATION", "0.7")),
}

BACKTEST_CONFIG = {
    "initial_balance": float(os.getenv("BT_INITIAL_BALANCE", "10000.0")),
    "commission_pct": float(os.getenv("BT_COMMISSION_PCT", "0.001")),
    "slippage_pct": float(os.getenv("BT_SLIPPAGE_PCT", "0.0005")),
}
