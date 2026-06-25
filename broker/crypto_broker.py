import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime
from broker.base_broker import (
    BaseBroker, Order, Position, AccountBalance,
    OrderSide, OrderType, OrderStatus
)
from utils.logger import logger
from config.settings import BINANCE_CONFIG

try:
    import ccxt
except ImportError:
    ccxt = None


class CryptoBroker(BaseBroker):
    def __init__(self, config: dict = None):
        super().__init__("Binance")
        self.config = config or BINANCE_CONFIG
        self.exchange = None

    def connect(self) -> bool:
        if ccxt is None:
            logger.error("ccxt kutuphanesi yuklu degil")
            return False

        try:
            self.exchange = ccxt.binance({
                "apiKey": self.config["api_key"],
                "secret": self.config["api_secret"],
                "enableRateLimit": True,
                "options": {"defaultType": "spot"},
            })

            if self.config.get("sandbox", True):
                self.exchange.set_sandbox_mode(True)
                logger.info("Binance sandbox (testnet) modu aktif")

            self.exchange.load_markets()
            self.connected = True
            logger.info(f"{self.name} baglantisi basarili")
            return True
        except Exception as e:
            logger.error(f"{self.name} baglanti hatasi: {e}")
            return False

    def disconnect(self) -> None:
        self.exchange = None
        self.connected = False
        logger.info(f"{self.name} baglantisi kesildi")

    def get_balance(self) -> AccountBalance:
        if not self.connected:
            return AccountBalance(0, 0)

        try:
            balance = self.exchange.fetch_balance()
            total = balance.get("total", {})
            free = balance.get("free", {})
            used = balance.get("used", {})

            usdt_total = total.get("USDT", 0)
            usdt_free = free.get("USDT", 0)
            usdt_used = used.get("USDT", 0)

            return AccountBalance(
                total_balance=usdt_total,
                available_balance=usdt_free,
                margin_used=usdt_used,
                currency="USDT"
            )
        except Exception as e:
            logger.error(f"Bakiye alinamadi: {e}")
            return AccountBalance(0, 0)

    def get_positions(self) -> list[Position]:
        if not self.connected:
            return []

        positions = []
        try:
            balance = self.exchange.fetch_balance()
            total = balance.get("total", {})

            for symbol, amount in total.items():
                if symbol == "USDT" or amount <= 0:
                    continue

                try:
                    ticker = self.exchange.fetch_ticker(f"{symbol}/USDT")
                    current_price = ticker.get("last", 0)

                    positions.append(Position(
                        symbol=f"{symbol}/USDT",
                        side=OrderSide.BUY,
                        quantity=amount,
                        entry_price=current_price,
                        current_price=current_price,
                        unrealized_pnl=0
                    ))
                except:
                    pass

            return positions
        except Exception as e:
            logger.error(f"Pozisyonlar alinamadi: {e}")
            return []

    def place_order(self, order: Order) -> Order:
        if not self.connected:
            order.status = OrderStatus.REJECTED
            return order

        try:
            params = {
                "symbol": order.symbol,
                "side": order.side.value,
                "amount": order.quantity,
            }

            if order.order_type == OrderType.MARKET:
                result = self.exchange.create_market_buy_order(
                    order.symbol, order.quantity
                ) if order.side == OrderSide.BUY else self.exchange.create_market_sell_order(
                    order.symbol, order.quantity
                )
            elif order.order_type == OrderType.LIMIT:
                result = self.exchange.create_limit_buy_order(
                    order.symbol, order.quantity, order.price
                ) if order.side == OrderSide.BUY else self.exchange.create_limit_sell_order(
                    order.symbol, order.quantity, order.price
                )
            else:
                order.status = OrderStatus.REJECTED
                return order

            order.order_id = result.get("id")
            order.status = OrderStatus.FILLED if result.get("status") == "closed" else OrderStatus.PENDING
            order.filled_price = result.get("average") or result.get("price")
            order.filled_quantity = result.get("filled", 0)
            order.commission = result.get("fee", {}).get("cost", 0)
            order.filled_at = datetime.utcnow()

            logger.info(f"Order yerlestirildi: {order.symbol} {order.side.value} {order.quantity} @ {order.filled_price}")
            return order

        except Exception as e:
            logger.error(f"Order hatasi: {e}")
            order.status = OrderStatus.REJECTED
            return order

    def cancel_order(self, order_id: str) -> bool:
        if not self.connected:
            return False

        try:
            self.exchange.cancel_order(order_id)
            logger.info(f"Order iptal edildi: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Order iptal hatasi: {e}")
            return False

    def get_order(self, order_id: str) -> Optional[Order]:
        if not self.connected:
            return None

        try:
            result = self.exchange.fetch_order(order_id)
            return Order(
                symbol=result.get("symbol"),
                side=OrderSide.BUY if result.get("side") == "buy" else OrderSide.SELL,
                order_type=OrderType.MARKET if result.get("type") == "market" else OrderType.LIMIT,
                quantity=result.get("amount", 0),
                status=OrderStatus.FILLED if result.get("status") == "closed" else OrderStatus.PENDING,
                filled_price=result.get("average"),
                filled_quantity=result.get("filled", 0),
                order_id=order_id
            )
        except Exception as e:
            logger.error(f"Order alinamadi: {e}")
            return None

    def get_ticker(self, symbol: str) -> dict:
        if not self.connected:
            return {}

        try:
            return self.exchange.fetch_ticker(symbol)
        except Exception as e:
            logger.error(f"Ticker alinamadi {symbol}: {e}")
            return {}

    def get_ohlcv(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        if not self.connected:
            return pd.DataFrame()

        try:
            raw = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)
            return df
        except Exception as e:
            logger.error(f"OHLCV alinamadi {symbol}: {e}")
            return pd.DataFrame()
