from dataclasses import dataclass, field
from typing import Literal

@dataclass
class TakeProfitTarget:
    price: float = 0.01
    close_percent: float = 100.0
    triggered: bool = False

@dataclass
class EntryLevel:
    price: float = 0.01
    position_share: float = 100.0

@dataclass
class TradeParameters:
    # Inputs
    liq_delta_to_SL_delta_ratio: float
    risk: float
    maintainance_margin_rate: float
    maintainance_deduction: float
    p_SL: float
    max_lvg: float = 10.0
    max_margin: float = 100.0   #trading logik nutzt nur 80% anteil davon, um Überbesicherung zu erzwingen
    isolated_margin: float = 0.0
    p_liquidation: float = 0.0
    p: float = 0.0
    risiko_euro: float = 0.0
    rel_risk: float = 0.0

    # Calculated Values
    sl_delta: float = 0.0
    TP_delta: float = 0.0
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
class Trade:
    #classes
    parameters: TradeParameters

    #lists
    entry_levels: list[EntryLevel] = field(default_factory=list)
    tp_targets: list[TakeProfitTarget] = field(default_factory=list)

    #default value fields
    total_risk: float = 0.0
    total_max_margin = 0.0
    current_price: float = 0.0
    buffer_SL: float = 0.0
    pull_SL: float = 0.0
    order_type: Literal["single limit", "single market", "single post only", "k1m6a box"] = "single limit"
    trailing_SL_percent: float = 0.0
    trailing_sl_enabled: bool = False
    current_sl_price: float = 0.0
    p_SL: float = 0.0
