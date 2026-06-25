import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime
from broker.base_broker import (
    BaseBroker, Order, Position, AccountBalance,
    OrderSide, OrderType, OrderStatus
)
from utils.logger import logger
from config.settings import MT5_CONFIG

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

TIMEFRAME_MAP = {
    "M1": None, "M5": None, "M15": None, "M30": None,
    "H1": None, "H4": None, "D1": None, "W1": None,
}


def _get_mt5_timeframe(tf_str: str):
    if mt5 is None:
        return None
    mapping = {
        "M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15, "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1, "W1": mt5.TIMEFRAME_W1,
    }
    return mapping.get(tf_str, mt5.TIMEFRAME_H1)


class ForexBroker(BaseBroker):
    def __init__(self, config: dict = None):
        super().__init__("MetaTrader5")
        self.config = config or MT5_CONFIG

    def connect(self) -> bool:
        if mt5 is None:
            logger.error("MetaTrader5 kutuphanesi bulunamadi. Sadece Windows'ta calisir.")
            return False

        try:
            if not mt5.initialize(
                path=self.config.get("path", r"C:\Program Files\MetaTrader 5\terminal64.exe"),
                login=self.config.get("login", 0),
                password=self.config.get("password", ""),
                server=self.config.get("server", ""),
            ):
                logger.error(f"MT5 baglanti hatasi: {mt5.last_error()}")
                return False

            self.connected = True
            logger.info(f"{self.name} baglantisi basarili: {self.config.get('server')}")
            return True
        except Exception as e:
            logger.error(f"{self.name} baglanti hatasi: {e}")
            return False

    def disconnect(self) -> None:
        if mt5 and self.connected:
            mt5.shutdown()
        self.connected = False
        logger.info(f"{self.name} baglantisi kesildi")

    def get_balance(self) -> AccountBalance:
        if not self.connected:
            return AccountBalance(0, 0)

        try:
            info = mt5.account_info()
            if info is None:
                return AccountBalance(0, 0)

            return AccountBalance(
                total_balance=info.balance,
                available_balance=info.equity - info.margin,
                margin_used=info.margin,
                unrealized_pnl=info.profit,
                currency=info.currency
            )
        except Exception as e:
            logger.error(f"Bakiye alinamadi: {e}")
            return AccountBalance(0, 0)

    def get_positions(self) -> list[Position]:
        if not self.connected:
            return []

        positions = []
        try:
            mt5_positions = mt5.positions_get()
            if mt5_positions is None:
                return []

            for p in mt5_positions:
                positions.append(Position(
                    symbol=p.symbol,
                    side=OrderSide.BUY if p.type == 0 else OrderSide.SELL,
                    quantity=p.volume,
                    entry_price=p.price_open,
                    current_price=p.price_current,
                    unrealized_pnl=p.profit,
                    realized_pnl=0,
                    stop_loss=p.sl if p.sl > 0 else None,
                    take_profit=p.tp if p.tp > 0 else None,
                    opened_at=datetime.fromtimestamp(p.time),
                    metadata={"ticket": p.ticket, "magic": p.magic}
                ))

            return positions
        except Exception as e:
            logger.error(f"Pozisyonlar alinamadi: {e}")
            return []

    def place_order(self, order: Order) -> Order:
        if not self.connected:
            order.status = OrderStatus.REJECTED
            return order

        try:
            symbol_info = mt5.symbol_info(order.symbol)
            if symbol_info is None:
                logger.error(f"Sembol bulunamadi: {order.symbol}")
                order.status = OrderStatus.REJECTED
                return order

            if not symbol_info.visible:
                mt5.symbol_select(order.symbol, True)

            tick = mt5.symbol_info_tick(order.symbol)
            price = tick.ask if order.side == OrderSide.BUY else tick.bid

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": order.symbol,
                "volume": order.quantity,
                "type": mt5.ORDER_TYPE_BUY if order.side == OrderSide.BUY else mt5.ORDER_TYPE_SELL,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": "AI_Trader",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            if order.stop_loss:
                request["sl"] = order.stop_loss
            if order.take_profit:
                request["tp"] = order.take_profit

            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order reddedildi: {result.comment}")
                order.status = OrderStatus.REJECTED
                return order

            order.order_id = str(result.order)
            order.status = OrderStatus.FILLED
            order.filled_price = price
            order.filled_quantity = order.quantity
            order.filled_at = datetime.utcnow()

            logger.info(f"Order yerlestirildi: {order.symbol} {order.side.value} {order.quantity} @ {price}")
            return order

        except Exception as e:
            logger.error(f"Order hatasi: {e}")
            order.status = OrderStatus.REJECTED
            return order

    def cancel_order(self, order_id: str) -> bool:
        if not self.connected:
            return False

        try:
            request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": int(order_id),
            }
            result = mt5.order_send(request)
            return result.retcode == mt5.TRADE_RETCODE_DONE
        except Exception as e:
            logger.error(f"Order iptal hatasi: {e}")
            return False

    def get_order(self, order_id: str) -> Optional[Order]:
        if not self.connected:
            return None

        try:
            orders = mt5.orders_get(ticket=int(order_id))
            if orders is None or len(orders) == 0:
                return None

            o = orders[0]
            return Order(
                symbol=o.symbol,
                side=OrderSide.BUY if o.type == 0 else OrderSide.SELL,
                order_type=OrderType.LIMIT,
                quantity=o.volume_current,
                price=o.price_open,
                status=OrderStatus.PENDING,
                order_id=str(o.ticket)
            )
        except Exception as e:
            logger.error(f"Order alinamadi: {e}")
            return None

    def get_ticker(self, symbol: str) -> dict:
        if not self.connected:
            return {}

        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return {}

            return {
                "symbol": symbol,
                "bid": tick.bid,
                "ask": tick.ask,
                "last": (tick.bid + tick.ask) / 2,
                "spread": tick.ask - tick.bid,
                "time": datetime.fromtimestamp(tick.time),
            }
        except Exception as e:
            logger.error(f"Ticker alinamadi {symbol}: {e}")
            return {}

    def get_ohlcv(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        if not self.connected:
            return pd.DataFrame()

        try:
            tf = _get_mt5_timeframe(timeframe)
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, limit)

            if rates is None or len(rates) == 0:
                return pd.DataFrame()

            df = pd.DataFrame(rates)
            df["time"] = pd.to_datetime(df["time"], unit="s")
            df.rename(columns={"time": "timestamp", "tick_volume": "volume"}, inplace=True)
            df.set_index("timestamp", inplace=True)
            df = df[["open", "high", "low", "close", "volume"]]
            return df
        except Exception as e:
            logger.error(f"OHLCV alinamadi {symbol}: {e}")
            return pd.DataFrame()
