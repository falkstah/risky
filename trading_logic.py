#for calculations
import math
import numbers
import pandas as pd
from classes import TradeParameters
#import ccxt
#import pandas_ta as ta

def calculate_all(params: TradeParameters):
    # 1) Directional basics
    if params.p_entry is None or params.p_SL is None:
        raise ValueError("Entry price or Stop Loss price is not set")

    try:
        params.p_entry = float(params.p_entry)
        params.p_SL = float(params.p_SL)
    except (TypeError, ValueError):
        raise TypeError("Entry price and Stop Loss price must be numeric values.")

    params.dirsign = calculate_dirsign(params)

    params.sl_delta = calculate_SL_delta(params)
    if params.sl_delta == 0:  # this would lead to division by zero in the following calculations
        raise ValueError("SL_delta = 0")

    params.rel_risk = calculate_rel_risk(params)
    params.current_direction = get_trade_direction(params)
    params.tp_active = calculate_tp_active(params)

    # 2) Desired liquidation price from entry and SL
    params.p_liquidation = match_liquidation_price_to_SL(params)

    # 3) Derive leverage from the liquidation target and apply constraints
    params.lvg = calculate_lvg(params)

    # 4) Initial margin and maintenance margin
    params.initial_margin = calculate_initial_margin(params)
    params.risk = check_initial_margin(params, params.initial_margin)
    params.initial_margin = calculate_initial_margin(params)

    # 5) Position and maintenance metrics
    params.n_pos_value = calculate_n_pos_value(params)
    params.maintainance_margin = calculate_maintainance_margin(params, params.n_pos_value)
    params.rel_maintainance_margin = calculate_rel_maintainance_margin(params)

    # 6) Risk feedback evaluation
    params.rel_asset_gain_at_TP, params.rrr, params.potential_profit = evaluate_trade(params)

    return params


#margins
#receive fom DEX
#maintainance_margin_rate  # = minimaler rel. Anteil an Positionsgröße, der als Eigenkapital stets verfügbar sein muss, sonst Zwangsliquidation (rel. Pendant zur absoluten Mainainance  Margin); oft nicht so hoch, worst case Annahme
#maintainance_deduction       # "0" ist konsevativ

#initial margin calculation
def calculate_dirsign(params: TradeParameters):
  p_entry = getattr(params, "p_entry", None)
  p_SL = getattr(params, "p_SL", None)

  if p_entry is None or p_SL is None:
    raise ValueError("Entry price and Stop Loss price must both be set.")
  if not isinstance(p_entry, numbers.Real) or not isinstance(p_SL, numbers.Real):
    raise TypeError("Entry price and Stop Loss price must be numeric values.")

  if p_entry > p_SL:
    return 1
  elif p_entry < p_SL:
    return -1
  else:
    raise ValueError("Entry and Stop Loss must not be equal.")


def calculate_SL_delta(params: TradeParameters):
  p_entry = getattr(params, "p_entry", None)
  p_SL = getattr(params, "p_SL", None)
  if p_entry is None or p_SL is None:
    raise ValueError("Entry price and Stop Loss price must both be set.")
  return abs(p_entry - p_SL)


def get_trade_direction(params: TradeParameters):
  dirsign = getattr(params, "dirsign", None)
  if dirsign is None:
    raise ValueError("dirsign must be calculated before determining trade direction.")

  if dirsign > 0:
    return "long"
  elif dirsign < 0:
    return "short"
  else:
    print("Trade direction not consistent. Please check your input parameters.")
  return None

def calculate_rel_risk(params: TradeParameters):
  return abs(params.p_entry - params.p_SL) / params.p_entry

def calculate_initial_margin(params: TradeParameters):
  return params.risk / (params.rel_risk * params.lvg) # initial margin >= maintainance_margin (immer)

def calculate_initial_margin_rate(lvg):
  return 1 / lvg

#live calculation
def calculate_n_pos_value(params: TradeParameters):
  return params.dirsign * params.risk / params.rel_risk # = initial_margin * lvg - koppelt somit lvg und initial_margin; n_pos_value < 0 <==> short

def calculate_max_lvg(params: TradeParameters):
  return 1 / params.maintainance_margin_rate

def max_lvg_for_given_liquidation(params: TradeParameters):
  return params.p_entry / (params.p_entry - params.p_liquidation) * (1 + params.maintainance_margin_rate) - params.maintainance_margin_rate

def calculate_lvg(params: TradeParameters):
  max_lvg = find_max_lvg(params)
  return check_lvg(max_lvg, params.max_leverage)


def find_max_lvg(params: TradeParameters):
  max_allowed_lvg = calculate_max_lvg(params)
  max_lvg_liq = max_lvg_for_given_liquidation(params)
  #both formulas give upper lvg limits, hence the smaller one has to be chosen:
  return min(max_allowed_lvg, max_lvg_liq, params.max_leverage)

def p_liq_exchange_forced(params: TradeParameters):
  return params.p_entry * (1 - params.maintainance_margin)

#Risiko: wenn Kurs gegen mich läuft sinkt mein Kontostand = hinterlegte Margin schrumpft -> bei maintainance margin <= 2%*n_pos_value: Zwangsliquidation
#->live updates für folgende Werte nötig:
def calculate_maintainance_margin(params: TradeParameters, n_pos_value):
  return abs(n_pos_value) * params.maintainance_margin_rate + params.maintainance_deduction # Maintenance margin is a positive requirement; direction is already encoded in n_pos_value

def calculate_rel_maintainance_margin(params: TradeParameters):
  return params.maintainance_margin / abs(params.n_pos_value) # = maintainance_margin_rate if maintainance_margin_deduction == 0

#safety calculus
#evaluating trading setups
def evaluate_trade(params: TradeParameters):
  rel_asset_gain_at_TP = (params.p_TP - params.p_entry) / params.p_entry
  rrr = (params.p_TP - params.p_entry) / (params.dirsign * params.sl_delta)
  potential_profit = params.risk * rrr
  return rel_asset_gain_at_TP, rrr, potential_profit

def calculate_tp_active(params: TradeParameters):
  if params.p_TP <= 0:
    return False
  if params.dirsign > 0:
    return params.p_TP > params.p_entry
  if params.dirsign < 0:
    return params.p_TP < params.p_entry
  return False

#exchange = ccxt.bybit()
k = 1.5 # sicherheitsmultiplikator
#live atr erstmal überbrückt, weil bybit google IP-Anfragrn blockiert
#used to match the liq price to current volatility:
def get_live_ATR(symbol = 'BTC/USDT', timeframe = '4h', length = 14):
  #ohlcv = "open, high, low, close, volume", fetch = retrieve
  #ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit = length + 1)  # +1, weil ATR_formel schon für die TR der ersten Kerze Referenzwert von vorheriger Kerze braucht

  #Umwandeln in DataFrame
  #df = pd.DataFrame(ohlcv, columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume'])

  #ATR Calculation
  #atr = ta.atr(df['high'], df['low'], df['close'], length = length)

  #returning only the latest atr of the generated atr list
  return 0
  #return atr.iloc[-1]

#buffer = k * get_live_ATR('BTC/USDT', '4h', 14)
#buffer = k
#lvg = buffer...

#management-dependent calulations (here: simplicity biased)

#conservatively hardcoded liq buffer to skip API-task
def match_liquidation_price_to_SL(params: TradeParameters):
    return max(params.p_entry - params.liq_delta_to_SL_delta_ratio * params.sl_delta * params.dirsign, 0) #SL_delta is now the absolute distance; dirsign restores the long/short sign

def match_lvg_to_liquidation_price(params: TradeParameters):
  return 1 / (1 + params.maintainance_margin_rate - params.p_liquidation * (1 + params.maintainance_margin_rate) / params.p_entry)  # = general p_liq formula solved for lvg; formula can get < 1

#risk correction functions

def check_lvg(lvg, max_leverage: float = 10.0):
  if lvg > max_leverage:
    print(f"Lvg will be stopped at {max_leverage}")
    lvg = max_leverage
  elif lvg < 1:
    print("Lvg < 1. Spot buy. (Positionsrisiko könnte kleiner als gewünschtes Risiko werden?).")
    lvg = 1
  return lvg

def check_initial_margin(params: TradeParameters, initial_margin):
  max_margin = max(params.max_margin, 1.0)
  if initial_margin > max_margin:
    print(f"margin-demand too high. Reducing risk to fit max_margin={max_margin}")
    return max_margin * params.rel_risk * params.lvg
  else:
    return params.risk

def check_rrr(rrr):
  if rrr < 2:
    print("rrr is small.")

def calulate_profit_at_price_p(params: TradeParameters, p):
  return (p - params.p_entry) / params.p_entry * params.n_pos_value #for long and short (pos value)

def calculate_equity(initial_margin, loss):
  return initial_margin - loss