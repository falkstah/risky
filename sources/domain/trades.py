from dataclasses import dataclass, field
from typing import Literal

@dataclass
class Calculation_Error(Exception):
    def __init__(self, message: str):
        super().__init__(message)

@dataclass
class Take_Profit_Target:
    price: float | None = None
    profit: float | None = None
    close_percent: float | None = None
    triggered: bool | None = None

@dataclass
class Entry_Level:
    price: float | None = None
    position_share: float | None = None

@dataclass
class Tranche_Parameters:
    # Inputs
    liq_delta_to_SL_delta_ratio: float | None = None
    risk: float | None = None
    maintainance_margin_rate: float | None = None
    maintainance_deduction: float | None = None
    p_SL: float | None = None
    max_lvg: float | None = None
    max_margin: float | None = None  #trading logik nutzt nur 80% anteil davon, um Überbesicherung zu erzwingen
    isolated_margin: float | None = None
    p_liquidation: float | None = None
    p: float | None = None
    risiko_euro: float  | None = None
    rel_risk: float  | None = None

    # Calculated Values
    sl_delta: float  | None = None
    tp_delta: float  | None = None
    dirsign: float  | None = None
    n_pos_value: float  | None = None
    lvg: float  | None = None
    initial_margin: float  | None = None
    maintainance_margin: float  | None = None
    rel_maintainance_margin: float  | None = None
    rel_asset_gain_at_TP: float  | None = None
    rrr: float  | None = None
    potential_profit: float  | None = None
    current_direction: Literal['long', 'short'] | None = None
    tp_active: bool = False
    loss: float  | None = None
    equity: float  | None = None

@dataclass
class Tranche:
    #classes
    tranche_parameters: Tranche_Parameters | None = None
    tp_target: Take_Profit_Target | None = None
    entry_level: Entry_Level | None = None

@dataclass
class Trade_Parameters:
    #static trade specific variables
    total_max_lvg: float  | None = None
    total_risk: float  | None = None
    total_max_margin: float  = 0.0
    liq_delta_to_SL_delta_ratio: float  | None = None
    maintainance_margin_rate: float  | None = None
    maintainance_deduction: float  | None = None
    current_asset_price: float  | None = None
    buffer_SL: float  | None = None
    pull_SL: float  | None = None
    order_type: Literal["single limit", "single market", "single post only", "k1m6a box"]  | None = None
    trailing_SL_percent: float  | None = None
    trailing_sl_enabled: bool = False
    current_sl_price: float  | None = None
    p_SL: float  | None = None
    total_potential_trade_profit: float  | None = None
    total_pos_size: float  | None = None
    tp_mode: Literal["global_TPs", "tranche_bound_TPs"]  | None = None
    potential_total_trade_profit: float  | None = None
    #dynamic
    total_cumulated_profit: float  | None = None

@dataclass
class Trade:
    #classes
    trade_parameters: Trade_Parameters | None = None
    tranches: list[Tranche] | None = None
    global_tp_targets: list[Take_Profit_Target] | None = None
