#for calculations
import math
import numbers
import pandas as pd
from classes import Trade, TradeParameters
#import ccxt
#import pandas_ta as ta

def calculate_all(trade: Trade):
    trade = calculate_initial_risk(trade)
    trade = calculate_exit_and_tp_structure(trade)
    trade = calculate_dynamic_state(trade)
    return trade

def sanitize_inputs(params: TradeParameters):
    field_names = getattr(params, "__dataclass_fields__", {})
    for field_name in field_names:
        if field_name in {"current_direction", "tp_active"}:
            continue

        value = getattr(params, field_name, None)
        if value is None:
            setattr(params, field_name, 0.0)
            continue

        if isinstance(value, str):
            if not value.strip():
                setattr(params, field_name, 0.0)
                continue
            try:
                setattr(params, field_name, float(value.strip()))
            except ValueError:
                setattr(params, field_name, 0.0)
            continue

        if isinstance(value, bool):
            continue

        if isinstance(value, numbers.Real):
            continue

        try:
            setattr(params, field_name, float(value))
        except (TypeError, ValueError):
            setattr(params, field_name, 0.0)


def calculate_initial_risk(trade: Trade):
    params = trade.parameters
    sanitize_inputs(params)

    # 1) Directional basics
    if params.p_entry == 0.0:
      print("P_Entry is 0.0, cannot calculate trade parameters.")
      return trade

    try:
        params.p_entry = float(params.p_entry)
        params.p_SL = float(params.p_SL)
    except (TypeError, ValueError):
        raise TypeError("Entry price and Stop Loss price must be numeric values.")

    params.dirsign = calculate_dirsign(params)
    params.sl_delta = calculate_SL_delta(params)
    if params.sl_delta == 0:
        raise ValueError("SL_delta = 0")

    params.current_direction = get_trade_direction(params)
    params.tp_active = calculate_tp_active(params)
    params.rel_risk = calculate_rel_risk(params)

    return trade


def calculate_exit_and_tp_structure(trade: Trade):
    params = trade.parameters
    params.p_liquidation = match_liquidation_price_to_SL(params)
    params.TP_delta = calculate_TP_delta(params)
    return trade


def calculate_dynamic_state(trade: Trade):
    params = trade.parameters
    params.lvg, params.risk = find_max_lvg(params)
    params.max_margin = find_max_margin(params)
    params.initial_margin = calculate_initial_margin(params)
    params.risk, params.initial_margin = check_initial_margin(params)

    params.n_pos_value = calculate_n_pos_value(params)
    params.maintainance_margin = calculate_maintainance_margin(params, params.n_pos_value)
    params.rel_maintainance_margin = calculate_rel_maintainance_margin(params)
    params.isolated_margin = params.max_margin

    params.rel_asset_gain_at_TP, params.rrr, params.potential_profit, params.equity = evaluate_trade(params)
    return trade



#margins
#receive fom DEX
#maintainance_margin_rate  # = minimum relative portion of position size that must always be available as equity, otherwise forced liquidation (relative counterpart to absolute maintenance margin); often not as high, worst case assumption
#maintainance_deduction       # "0" is conservative

#initial margin calculation
def calculate_dirsign(params: TradeParameters):
  sanitize_inputs(params)
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

def calculate_TP_delta(params: TradeParameters):
  p_entry = getattr(params, "p_entry", None)
  p_TP = getattr(params, "p_TP", None)
  if p_entry is None or p_TP is None:
    raise ValueError("Entry price and Take Profit price must both be set.")
  return abs(p_entry - p_TP)


def calculate_buffered_tp1_close_percent(trade: Trade):
  params = trade.parameters
  p_entry = getattr(params, "p_entry", None)
  p_TP = getattr(params, "p_TP", None)
  buffer_SL = getattr(trade, "buffer_SL", None)

  if p_entry is None or p_TP is None or buffer_SL is None:
    raise ValueError("Entry price, TP price and buffer SL must be set.")

  tp_delta = abs(p_TP - p_entry)
  buffer_delta = abs(buffer_SL - p_entry)

  if tp_delta == 0.0:
    raise ValueError("TP price must differ from entry price.")
  if buffer_delta == 0.0:
    return 0.0

  # Buffer SL must be on the correct side of entry for the trade direction.
  if params.dirsign is None:
    params.dirsign = calculate_dirsign(params)
  if params.dirsign > 0 and buffer_SL >= p_entry:
    raise ValueError("Buffer SL must be below entry for a long trade.")
  if params.dirsign < 0 and buffer_SL <= p_entry:
    raise ValueError("Buffer SL must be above entry for a short trade.")

  close_fraction = buffer_delta / (tp_delta + buffer_delta)
  return float(close_fraction * 100.0)


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
  return abs(params.sl_delta) / params.p_entry

def calculate_initial_margin(params: TradeParameters):
  return params.risk / (params.rel_risk * params.lvg) # initial margin >= maintainance_margin (immer)

def calculate_initial_margin_rate(lvg):
  return 1 / lvg

#live calculation
def calculate_n_pos_value(params: TradeParameters):
  return params.dirsign * params.risk / params.rel_risk # = initial_margin * lvg - thus couples lvg and initial_margin; n_pos_value < 0 <==> short

def calculate_max_lvg(params: TradeParameters):
  return math.floor(1 / params.maintainance_margin_rate)

def max_lvg_for_given_liquidation(params: TradeParameters):
  print(params.maintainance_margin_rate, params.maintainance_deduction, params.p_liquidation, params.p_entry)
  return math.floor(1 / (1 + params.maintainance_margin_rate + params.maintainance_deduction - params.p_liquidation / params.p_entry))  # = general p_liq formula solved for lvg; formula can get < 1


def find_max_lvg(params: TradeParameters):
  max_allowed_lvg = calculate_max_lvg(params)
  max_lvg_liq = max_lvg_for_given_liquidation(params)
  #both formulas give upper lvg limits, hence the smaller one has to be chosen. But lvg >= 1 with max:
  lvg = math.floor(min(max_allowed_lvg, max_lvg_liq)) #floor guarantees that lvg does not force early liq
  return check_lvg(lvg, params)

#risk correction functions
def check_lvg(lvg, params):
  risk = params.risk
  if lvg > params.max_lvg:  # Assuming params.max_lvg is 10
    print(f"Warning: Calculated leverage {lvg} exceeds {params.max_lvg}. Risk will be made smaller to adjust.")
    lvg = params.max_lvg
    risk = reduce_risk(params)

  if lvg < 1:
    print("lvg < 1. Over secuing already guaranteed by find_max_margin. hence, buffer is too big. Risk too small.")
    lvg = 1
    #possibly risk has to be fitted
  return lvg, risk

def reduce_risk(params):
   return params.max_margin * params.max_lvg * params.rel_risk


#Risk: if price moves against me, my account balance decreases = posted margin shrinks -> if maintenance margin <= 2% * n_pos_value: forced liquidation
#->live updates necessary for the following values:
def calculate_maintainance_margin(params: TradeParameters, n_pos_value):
  return abs(n_pos_value) * params.maintainance_margin_rate + params.maintainance_deduction # Maintenance margin is a positive requirement; direction is already encoded in n_pos_value

def calculate_rel_maintainance_margin(params: TradeParameters):
  #only useful during the trade, because margin changes and rel_maintainance_margin may no longer equal MMR
  return params.maintainance_margin / abs(params.n_pos_value) # = maintainance_margin_rate if maintainance_margin_deduction == 0

def p_liq_exchange_forced(params: TradeParameters):
  return params.p_entry * (1 - params.maintainance_margin)


#Strategy Feedback
def calculate_tp_active(params: TradeParameters):
  if params.p_TP <= 0:
    return False
  if params.dirsign > 0:
    return params.p_TP > params.p_entry
  if params.dirsign < 0:
    return params.p_TP < params.p_entry
  return False


#exchange = ccxt.bybit()
#k = 1.5  safety multiplier
#live ATR temporarily bypassed because bybit blocks Google IP requests
#used to match the liq price to current volatility:
def get_live_ATR(symbol = 'BTC/USDT', timeframe = '4h', length = 14):
  #ohlcv = "open, high, low, close, volume", fetch = retrieve
  #ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit = length + 1)  # +1 because the ATR formula already needs the previous candle's reference value for the first TR

  #Convert to DataFrame
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

def find_max_margin(params):
   return 0.9 * params.max_margin #forces over securing margin, to avoid margin calls and forced liquidation
def check_initial_margin(params: TradeParameters):
  max_margin = max(params.max_margin, 1.0)
  if params.initial_margin > max_margin:
    print(f"margin-demand too high. Reducing risk to fit max_margin={max_margin}")
    risk = max_margin * params.rel_risk * params.lvg
    return risk, calculate_initial_margin(params)
  else:
    risk = params.risk
    initial_margin = params.initial_margin
    return risk, initial_margin
  
def check_rrr(rrr):
  if rrr < 2:
    print("rrr is small.")

#safety calculus
#evaluating trading setups
def evaluate_trade(params: TradeParameters):
  rel_asset_gain_at_TP = params.TP_delta / params.p_entry
  rrr = params.TP_delta / params.sl_delta
  potential_profit = params.risk * rrr
  equity = calculate_equity(params)
  return rel_asset_gain_at_TP, rrr, potential_profit, equity

def calulate_profit_at_price_p(params: TradeParameters, p):
  if p >= params.p_entry:
    return params.dirsign * abs(p - params.p_entry) / params.p_entry * params.n_pos_value #for long and short (pos value)
  else:
    return -1 * params.dirsign * abs(p - params.p_entry) / params.p_entry * params.n_pos_value #for long and short (pos value)

def calculate_equity(params):
  return params.initial_margin - params.loss


def debug_calculate_all(**overrides):
  #Create a TradeParameters object with default inputs and run calculate_all for debugging.
  defaults = {
      "liq_delta_to_SL_delta_ratio": 4.0,
      "risk": 10.0,
      "maintainance_margin_rate": 0.02,
      "maintainance_deduction": 0.0,
      "p_entry": 10.0,
      "p_SL": 9.0,
      "p_TP": 20.0,
      "max_lvg": 10.0,
      "max_margin": 100.0,
  }
  defaults.update(overrides)

  params = TradeParameters(
      liq_delta_to_SL_delta_ratio=float(defaults.get("liq_delta_to_SL_delta_ratio", 4.0)),
      risk=float(defaults.get("risk", 10.0)),
      maintainance_margin_rate=float(defaults.get("maintainance_margin_rate", 0.02)),
      maintainance_deduction=float(defaults.get("maintainance_deduction", 0.0)),
      p_entry=float(defaults.get("p_entry", 10.0)),
      p_SL=float(defaults.get("p_SL", 9.0)),
      p_TP=float(defaults.get("p_TP", 20.0)),
      max_lvg=float(defaults.get("max_lvg", 10.0)),
      max_margin=float(defaults.get("max_margin", 100.0)),
  )
  trade = Trade(parameters=params)
  return calculate_all(trade)

#for debugging run this function with Debugger till Breakpoint:
debug_calculate_all()