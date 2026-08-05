from dataclasses import dataclass, field
from typing import Literal

@dataclass
class Take_Profit_Target:
    price: float = 0.01
    profit: float = 0.0
    close_percent: float = 50.0
    triggered: bool = False

@dataclass
class Entry_Level:
    price: float = 0.01
    position_share: float = 100.0

@dataclass
class Tranche_Parameters:
    # Inputs
    liq_delta_to_SL_delta_ratio: float = 4.0
    risk: float = 10.0
    maintainance_margin_rate: float = 0.02
    maintainance_deduction: float = 0.00
    p_SL: float = 0.00
    max_lvg: float = 10.0
    max_margin: float = 100.0   #trading logik nutzt nur 80% anteil davon, um Überbesicherung zu erzwingen
    isolated_margin: float = 0.0
    p_liquidation: float = 0.0
    p: float = 0.0
    risiko_euro: float = 0.0
    rel_risk: float = 0.0

    # Calculated Values
    sl_delta: float = 0.0
    tp_delta: float = 0.0
    dirsign: float = 0.0
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
    loss: float = 0.0
    equity: float = 0.0

@dataclass
class Tranche:
    #classes
    tranche_parameters: Tranche_Parameters = field(default_factory = Tranche_Parameters)
    tp_target: Take_Profit_Target = field(default_factory = Take_Profit_Target)
    entry_level: Entry_Level = field(default_factory = Entry_Level)

@dataclass
class Trade_Parameters:
    #static trade specific variables
    total_max_lvg: float = 10.0
    total_risk: float = 0.0
    total_max_margin: float  = 0.0
    liq_delta_to_SL_delta_ratio: float = 4.0
    maintainance_margin_rate: float = 0.02
    maintainance_deduction: float = 0.00
    current_asset_price: float = 0.0
    buffer_SL: float = 0.0
    pull_SL: float = 0.0
    order_type: Literal["single limit", "single market", "single post only", "k1m6a box"] = "single limit"
    trailing_SL_percent: float = 0.0
    trailing_sl_enabled: bool = False
    current_sl_price: float = 0.0
    p_SL: float = 0.0
    total_potential_trade_profit: float = 0.0
    total_pos_size: float = 0.0
    tp_mode: Literal["global_TPs", "tranche_bound_TPs"] = "global_TPs"
    potential_total_trade_profit: float = 0.0
    #dynamic
    total_cumulated_profit: float = 0.0

@dataclass
class Trade:
    #classes
    trade_parameters: Trade_Parameters = field(default_factory = Trade_Parameters)
    tranches: list[Tranche] = field(default_factory = lambda : [Tranche()])     #calable function lambda guarantees a minimum of one tranche, since every trade needs at least one entry-level (which is linked to a tranche)
    global_tp_targets: list[Take_Profit_Target] = field(default_factory = list)
