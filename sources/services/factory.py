#helps trades.py to config parameters (subjective defaults): 
# #p.ex. every trade's tranche list contains at least one (or number from settings) tranche(s) as default

# sources/services/factory.py

from config.settings import (
    ENTRY_DEFAULTS,
    TP_DEFAULTS,
    TRANCHE_INPUT_DEFAULTS,
    TRADE_DEFAULTS,
    TRADE_STRUCTURE_DEFAULTS
)

from sources.domain.trades import (
    Trade,
    Trade_Parameters,
    Tranche,
    Tranche_Parameters,
    Entry_Level,
    Take_Profit_Target
)

# ---------------------------------------------------------
# Trade-Parameter Factory
# ---------------------------------------------------------
def create_trade_parameters() -> Trade_Parameters:
    params = Trade_Parameters()
    for key, value in TRADE_DEFAULTS.items():
        setattr(params, key, value)
    return params


# ---------------------------------------------------------
# Tranche-Parameter Factory
# ---------------------------------------------------------
def create_tranche_parameters() -> Tranche_Parameters:
    params = Tranche_Parameters()
    for key, value in TRANCHE_INPUT_DEFAULTS.items():
        setattr(params, key, value)
    return params


# ---------------------------------------------------------
# Entry-Level Factory
# ---------------------------------------------------------
def create_entry_level() -> Entry_Level:
    return Entry_Level(**ENTRY_DEFAULTS)


# ---------------------------------------------------------
# TP-Target Factory
# ---------------------------------------------------------
def create_tp_target() -> Take_Profit_Target:
    return Take_Profit_Target(triggered = False, **TP_DEFAULTS)


# ---------------------------------------------------------
# Tranche Factory
# ---------------------------------------------------------
def create_tranche() -> Tranche:
    tranche_params = create_tranche_parameters()
    entry = create_entry_level()
    tp = create_tp_target()
    return Tranche(
        tranche_parameters=tranche_params,
        entry_level=entry,
        tp_target=tp
    )


# ---------------------------------------------------------
# Trade Factory
# ---------------------------------------------------------
def create_trade() -> Trade:
    trade_params = create_trade_parameters()

    tranches = [
        create_tranche()
        for _ in range(TRADE_STRUCTURE_DEFAULTS["initial_tranches"])
    ]

    tp_targets = [
        create_tp_target()
        for _ in range(TRADE_STRUCTURE_DEFAULTS["initial_global_tp_targets"])
    ]

    return Trade(
        trade_parameters=trade_params,
        tranches=tranches,
        global_tp_targets=tp_targets
    )
