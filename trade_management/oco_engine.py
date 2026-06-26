"""
BlackBird Tarzı Trade Yönetim Motoru
OCO Order Sets, Trailing Stops, Dynamic Planning
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class OrderSide(Enum):
    LONG = "long"
    SHORT = "short"

class OrderSetStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    TP_HIT = "tp_hit"
    SL_HIT = "sl_hit"
    CANCELLED = "cancelled"

class TrailingMode(Enum):
    FIXED = "fixed"                  # Sabit mesafe
    ATR = "atr"                       # ATR bazlı dinamik
    BREAK_EVEN = "break_even"         # Kâra geçince maliyete çek
    STEP = "step"                     # Kademeli (belirli kârda trigger)


@dataclass
class OCOOrderSet:
    """One-Cancels-Other: Entry + Stop Loss + Take Profit"""
    name: str
    side: OrderSide
    entry_price: float
    stop_loss: float
    take_profit: float
    position_pct: float = 1.0  # Toplam pozisyonun yüzde kaçını yönetir (0.5 = %50)
    status: OrderSetStatus = OrderSetStatus.PENDING
    filled_at: Optional[datetime] = None
    trailing_mode: TrailingMode = TrailingMode.FIXED
    trailing_distance: float = 0.0
    trailing_atr_mult: float = 2.0
    break_even_trigger_atr: float = 1.0

@dataclass
class TradeState:
    """Canlı trade durumu takibi"""
    entry_price: float
    side: OrderSide
    size: float
    entry_time: datetime
    stop_loss: float
    take_profit: float
    max_favorable_price: float
    max_adverse_price: float
    order_sets: List[OCOOrderSet] = field(default_factory=list)


class TradeManagementEngine:
    """BlackBird tarzı trade yönetim motoru"""
    
    def __init__(self, initial_balance: float = 10000.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position = 0.0
        self.trades: List[Dict] = []
        self.active_order_sets: List[OCOOrderSet] = []

    def create_oco_set(
        self, side: str, entry: float, sl: float, tp: float,
        position_pct: float = 1.0, name: str = "Set1"
    ) -> OCOOrderSet:
        """Yeni bir OCO emir seti oluştur"""
        s = OrderSide.LONG if side.lower() == "long" else OrderSide.SHORT
        return OCOOrderSet(
            name=name, side=s, entry_price=entry, stop_loss=sl, take_profit=tp,
            position_pct=position_pct, status=OrderSetStatus.PENDING
        )

    def calculate_dynamic_sizing(self, balance: float, risk_pct: float, entry: float, stop: float) -> float:
        """Dynamic Planning: Risk yüzdesine göre pozisyon boyutu"""
        risk_amount = balance * risk_pct
        per_unit_risk = abs(entry - stop)
        if per_unit_risk == 0: return 0
        return risk_amount / per_unit_risk

    def update_trailing_stops(self, current_price: float, current_atr: float, trade: TradeState):
        """Trailing Actions: Stop-loss'u dinamik olarak güncelle"""
        for oco in trade.order_sets:
            if oco.status != OrderSetStatus.ACTIVE:
                continue
            
            if trade.side == OrderSide.LONG:
                # Kârda mıyız?
                in_profit = current_price > trade.entry_price
                
                if oco.trailing_mode == TrailingMode.ATR:
                    new_sl = current_price - (oco.trailing_atr_mult * current_atr)
                    if new_sl > oco.stop_loss:
                        oco.stop_loss = new_sl
                
                elif oco.trailing_mode == TrailingMode.BREAK_EVEN:
                    if in_profit and (current_price - trade.entry_price) > oco.break_even_trigger_atr * current_atr:
                        oco.stop_loss = max(oco.stop_loss, trade.entry_price)
                
                elif oco.trailing_mode == TrailingMode.STEP:
                    # Her 1 ATR kârda stop'u 1 ATR yukarı taşı
                    profit = current_price - trade.entry_price
                    steps = int(profit / current_atr)
                    new_sl = trade.entry_price + (steps - 1) * current_atr
                    if new_sl > oco.stop_loss:
                        oco.stop_loss = new_sl
                
                elif oco.trailing_mode == TrailingMode.FIXED:
                    new_sl = current_price - oco.trailing_distance
                    if new_sl > oco.stop_loss:
                        oco.stop_loss = new_sl
            
            elif trade.side == OrderSide.SHORT:
                in_profit = current_price < trade.entry_price
                
                if oco.trailing_mode == TrailingMode.ATR:
                    new_sl = current_price + (oco.trailing_atr_mult * current_atr)
                    if new_sl < oco.stop_loss or oco.stop_loss == 0:
                        oco.stop_loss = new_sl
                
                elif oco.trailing_mode == TrailingMode.BREAK_EVEN:
                    if in_profit and (trade.entry_price - current_price) > oco.break_even_trigger_atr * current_atr:
                        if oco.stop_loss == 0 or oco.stop_loss > trade.entry_price:
                            oco.stop_loss = trade.entry_price

    def check_exits(self, current_price: float, trade: TradeState) -> List[str]:
        """OCO ve Exit sinyallerini kontrol et, tetiklenenleri işaretle"""
        triggered = []
        for oco in trade.order_sets:
            if oco.status != OrderSetStatus.ACTIVE:
                continue
            
            if trade.side == OrderSide.LONG:
                if current_price <= oco.stop_loss:
                    oco.status = OrderSetStatus.SL_HIT
                    triggered.append(f"{oco.name} - SL Hit")
                elif current_price >= oco.take_profit:
                    oco.status = OrderSetStatus.TP_HIT
                    triggered.append(f"{oco.name} - TP Hit")
            
            elif trade.side == OrderSide.SHORT:
                if current_price >= oco.stop_loss:
                    oco.status = OrderSetStatus.SL_HIT
                    triggered.append(f"{oco.name} - SL Hit")
                elif current_price <= oco.take_profit:
                    oco.status = OrderSetStatus.TP_HIT
                    triggered.append(f"{oco.name} - TP Hit")
        
        return triggered