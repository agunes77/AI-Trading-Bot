from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_price: Optional[float] = None
    filled_quantity: float = 0.0
    commission: float = 0.0
    order_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    filled_at: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class Position:
    symbol: str
    side: OrderSide
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    opened_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)


@dataclass
class AccountBalance:
    total_balance: float
    available_balance: float
    margin_used: float = 0.0
    unrealized_pnl: float = 0.0
    currency: str = "USDT"


class BaseBroker(ABC):
    def __init__(self, name: str):
        self.name = name
        self.connected = False

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def get_balance(self) -> AccountBalance:
        pass

    @abstractmethod
    def get_positions(self) -> list[Position]:
        pass

    @abstractmethod
    def place_order(self, order: Order) -> Order:
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        pass

    @abstractmethod
    def get_order(self, order_id: str) -> Optional[Order]:
        pass

    @abstractmethod
    def get_ticker(self, symbol: str) -> dict:
        pass

    @abstractmethod
    def get_ohlcv(self, symbol: str, timeframe: str, limit: int) -> 'pd.DataFrame':
        pass

    def is_connected(self) -> bool:
        return self.connected

    def get_name(self) -> str:
        return self.name
