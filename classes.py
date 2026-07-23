from dataclasses import dataclass
from typing import Literal

@dataclass
class TradeParameters:
    # Inputs
    liq_delta_to_SL_delta_ratio: float
    risk: float
    maintainance_margin_rate: float
    maintainance_deduction: float
    p_entry: float
    p_SL: float
    p_TP: float
    p_liquidation: float = 0.0
    p: float = 0.0
    risiko_euro: float = 0.0
    rel_risk: float = 0.0
    
    # Calculated Values
    sl_delta: float = 0.0
    n_pos_value: float = 0.0
    lvg: float = 0.0
    initial_margin: float = 0.0
    maintainance_margin: float = 0.0
    rel_maintainance_margin: float = 0.0
    rel_asset_gain_at_TP: float = 0.0
    rrr: float = 0.0
    potential_profit: float = 0.0
    current_direction: Literal['long', 'short'] | None = None
    tp_active: bool = False
