#for calculations
import math
import numbers
from dataclasses import fields
import pandas as pd
from classes import Trade, TradeParameters
#import ccxt
#import pandas_ta as ta

#2. manage SL pulls and TPs for whole position
def calculate_all(trade: Trade):
  #sanitizes trade attributes first and then the attributes in trade-Ojekt params:
  sanitize_inputs(trade)
  sanitize_inputs(trade.parameters)

  #1. calculate all params for each partial entry (ladder) of a trade with one given SL
  #entry meint ein ListenELement von entry_levels
  for entry in trade.entry_levels:
    params = calculate_tranche_allocations(trade)

    #Calculate:
    trade = calculate_initial_risk(trade, entry)
    trade = calculate_exit_and_tp_structure(trade, entry)
    trade = calculate_dynamic_state(trade, entry)

  return trade

def sanitize_inputs(item):
  if isinstance(item, Trade):
      field_names = [field.name for field in fields(Trade)]
      skip_fields = {"parameters", "entry_levels", "tp_targets", "order_type", "current_direction", "tp_active"}
  elif isinstance(item, TradeParameters):
      field_names = [field.name for field in fields(TradeParameters)]
      skip_fields = {"current_direction", "tp_active"}
  else:
      field_names = getattr(item, "__dataclass_fields__", {})
      skip_fields = set()

  for field_name in field_names:
      if field_name in skip_fields:
          continue

      value = getattr(item, field_name, None)
      if value is None:
          setattr(item, field_name, 0.0)
          continue

      if isinstance(value, str):
          if not value.strip():
              setattr(item, field_name, 0.0)
              continue
          try:
              setattr(item, field_name, float(value.strip()))
          except ValueError:
              setattr(item, field_name, 0.0)
          continue

      if isinstance(value, bool):
          continue

      if isinstance(value, numbers.Real):
          continue

      try:
          setattr(item, field_name, float(value))
      except (TypeError, ValueError):
          setattr(item, field_name, 0.0)

def calculate_tranche_allocations(trade):
  trade.parameters.risk = trade.params.position_share * trade.total_risk
  trade.parameters.max_margin = trade.params.position_share * trade.max_margin  #faktor buffer für überbeischerung wird in schleife für jeden entry einzeln eingebaut, nicht schon in trade
  #TPs are managed globally with FiFo principle (exchange standard)

  #SL is gloabal and same for all tranches at the moment, but can be changed later here
  trade.parameters.p_SL = trade.p_SL

  return trade.parameters

def calculate_initial_risk(trade: Trade, entry):
  params = trade.parameters

  # 1) Directional basics
  if entry == 0.0:
    print("P_Entry is 0.0, cannot calculate trade parameters.")
    return trade

  try:
      entry.price = float(entry.price)
      params.p_SL = float(params.p_SL)
  except (TypeError, ValueError):
      raise TypeError("Entry price and Stop Loss price must be numeric values.")

  params.dirsign = calculate_dirsign(params, entry)
  params.sl_delta = calculate_SL_delta(params, entry)
  if params.sl_delta == 0:
      raise ValueError("SL_delta = 0")

  params.current_direction = get_trade_direction(params)
  params.tp_active = calculate_tp_active(params, entry)
  params.rel_risk = calculate_rel_risk(params, entry)

  return trade


def calculate_exit_and_tp_structure(trade: Trade, entry):
  params = trade.parameters
  params.p_liquidation = match_liquidation_price_to_SL(params, entry)
  params.TP_delta = calculate_TP_delta(params, entry)
  return trade


def calculate_dynamic_state(trade: Trade, entry):
  params = trade.parameters
  params.lvg, params.risk = find_max_lvg(params)
  params.max_margin = find_max_margin(params)
  params.initial_margin = calculate_initial_margin(params)
  params.risk, params.initial_margin = check_initial_margin(params)

  params.n_pos_value = calculate_n_pos_value(params)
  params.maintainance_margin = calculate_maintainance_margin(params)
  params.rel_maintainance_margin = calculate_rel_maintainance_margin(params)
  params.isolated_margin = params.max_margin

  params.rel_asset_gain_at_TP, params.rrr, params.potential_profit, params.equity = evaluate_trade(params, entry)
  return trade

#margins
#receive fom DEX
#maintainance_margin_rate  # = minimum relative portion of position size that must always be available as equity, otherwise forced liquidation (relative counterpart to absolute maintenance margin); often not as high, worst case assumption
#maintainance_deduction       # "0" is conservative

#initial margin calculation
def calculate_dirsign(params: TradeParameters, entry):
  entry.price = getattr(params, "p_entry", None)
  p_SL = getattr(params, "p_SL", None)

  if entry.price is None or p_SL is None:
    raise ValueError("Entry price and Stop Loss price must both be set.")
  if not isinstance(entry.price, numbers.Real) or not isinstance(p_SL, numbers.Real):
    raise TypeError("Entry price and Stop Loss price must be numeric values.")

  if entry.price > p_SL:
    return 1
  elif entry.price < p_SL:
    return -1
  else:
    raise ValueError("Entry and Stop Loss must not be equal.")


def calculate_SL_delta(params: TradeParameters, entry):
  entry.price = getattr(params, "p_entry", None)
  p_SL = getattr(params, "p_SL", None)
  if entry.price is None or p_SL is None:
    raise ValueError("Entry price and Stop Loss price must both be set.")
  return abs(entry.price - p_SL)

def calculate_TP_delta(params: TradeParameters, entry):
  entry.price = getattr(params, "entry.price", None)
  p_TP = getattr(params, "p_TP", None)
  if entry.price is None or p_TP is None:
    raise ValueError("Entry price and Take Profit price must both be set.")
  return abs(entry.price - p_TP)

  #small partial TP1 allows: moving SL under previous Low to ain more buffer. 
  # This function calculates the tp1-size so that buffer_SL hit would stop trade out (p.ex. under a low) without a loss (by risking Tp1 gains)
  # (increae of V if buffer_SL is pulled further to entry could also be interesting, i.e. pyramid entry)
def calculate_buffered_tp1_close_percent(trade: Trade, entry):
  params = trade.parameters
  entry.price = getattr(params, "entry.price", None)
  p_TP = getattr(params, "p_TP", None)
  buffer_SL = getattr(trade, "buffer_SL", None)

  #useless when it will be included in sanitier:
  if entry.price is None or p_TP is None or buffer_SL is None:
    raise ValueError("Entry price, TP price and buffer SL must be set.")

  TP_delta = params.TP_delta
  buffer_delta = abs(buffer_SL - entry.price)

  if TP_delta == 0.0:
    raise ValueError("TP price must differ from entry price.")
  if buffer_delta == 0.0:
    return 0.0

  # Buffer SL must be on the correct side of entry for the trade direction.
  if params.current_direction is None:
    params.current_direction = get_trade_direction(params)
  if params.current_direction == "long" and buffer_SL >= entry.price:
    raise ValueError("Buffer SL must be below entry for a long trade.")
  if params.current_direction == "short" and buffer_SL <= entry.price:
    raise ValueError("Buffer SL must be above entry for a short trade.")

  #profit(TP1) = close_fraction * n_pos_value * (TP1 - entry.price)
  #unclosed_pos_rest = (1 - x) * n_pos_value
  #Loss(buffer_SL) = uncloses_pos_rest * n_pos_value * (entry.price - buffer_SL)
  #Profit(TP1) == Loss(buffer_SL)  -> solve for close_fraction: close_fraction = buffer_delta / (TP1 - buffer_SL)
  #with TP1 - buffer_SL = TP_delta + buffer_delta:
  close_fraction = buffer_delta / (TP_delta + buffer_delta)
  return float(close_fraction)


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

def calculate_rel_risk(params: TradeParameters, entry):
  return abs(params.sl_delta) / entry.price

def calculate_initial_margin(params: TradeParameters):
  return params.risk / (params.rel_risk * params.lvg) # initial margin >= maintainance_margin (immer)

def calculate_initial_margin_rate(lvg):
  return 1 / lvg

#live calculation; sign matches trade direction, abs(n_pos_value) is used for position calculations that do not depend on direction
def calculate_n_pos_value(params: TradeParameters):
  return params.dirsign * params.risk / params.rel_risk # = initial_margin * lvg - thus couples lvg and initial_margin; n_pos_value < 0 <==> short

def calculate_max_lvg(params: TradeParameters):
  return math.floor(1 / params.maintainance_margin_rate)

#can differ or long and short even for same sl_delta and liq distance, which is against Intuiton; not symmetrical!!! hat's no error
def max_lvg_for_given_liquidation(params: TradeParameters):
  if params.current_direction == "long":
    lvg = math.floor(1 / (1 + params.maintainance_margin_rate + params.maintainance_deduction - params.p_liquidation / params.p_entry))  # = general p_liq formula solved for lvg; formula can get < 1
  elif params.current_direction == "short":
    lvg = math.floor(1 / (1 + params.maintainance_margin_rate + params.maintainance_deduction -  params.p_entry / params.p_liquidation))
  else: lvg = 0
  return lvg 

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
def calculate_maintainance_margin(params: TradeParameters):
  return abs(params.n_pos_value) * params.maintainance_margin_rate + params.maintainance_deduction # Maintenance margin is a positive requirement; direction is already encoded in n_pos_value

def calculate_rel_maintainance_margin(params: TradeParameters):
  #only useful during the trade, because margin changes and rel_maintainance_margin may no longer equal MMR
  return params.maintainance_margin / abs(params.n_pos_value) # = maintainance_margin_rate if maintainance_margin_deduction == 0

def p_liq_exchange_forced(params: TradeParameters, entry):
  return entry.price * (1 - params.maintainance_margin)


#Strategy Feedback
def calculate_tp_active(trade):
  if trade.tp_targets[0].price <= 0:
    return False
  if trade.params.dirsign > 0:
    return trade.tp_targets[0].price > trade.entry_levels[0].price
  if trade.params.dirsign < 0:
    return trade.tp_targets[0].price < trade.entry_levels[0].price
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
def match_liquidation_price_to_SL(params: TradeParameters, entry):
    return max(entry.price - params.liq_delta_to_SL_delta_ratio * params.sl_delta * params.dirsign, 0) #SL_delta is now the absolute distance; dirsign restores the long/short sign

#def match_lvg_to_liquidation_price(params: TradeParameters):
#  return 1 / (1 + params.maintainance_margin_rate - params.p_liquidation * (1 + params.maintainance_margin_rate) / params.p_entry)  # = general p_liq formula solved for lvg; formula can get < 1

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
def evaluate_trade(params: TradeParameters, entry):
  rel_asset_gain_at_TP = params.TP_delta / entry.price
  rrr = params.TP_delta / params.sl_delta
  potential_profit = params.risk * rrr
  equity = calculate_equity(params)
  return rel_asset_gain_at_TP, rrr, potential_profit, equity

def calulate_profit_at_price_p(params: TradeParameters, p, entry):
  if p >= entry.price:
    return params.dirsign * abs(p - entry.price) / entry.price * abs(params.n_pos_value) #for long and short (pos value)
  else:
    return -1 * params.dirsign * abs(p - entry.price) / entry.price * abs(params.n_pos_value) #for long and short (pos value)

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
      "p_SL": 11.0,
      "p_TP": 8.0,
      "max_lvg": 10.0,
      "max_margin": 100.0,
  }
  defaults.update(overrides)

  #takes given params with default values as Fallback (in parantheses)
  #tp, entry to be added!!!
  params = TradeParameters(
      liq_delta_to_SL_delta_ratio=float(defaults.get("liq_delta_to_SL_delta_ratio", 4.0)),
      risk=float(defaults.get("risk", 10.0)),
      maintainance_margin_rate=float(defaults.get("maintainance_margin_rate", 0.02)),
      maintainance_deduction=float(defaults.get("maintainance_deduction", 0.0)),
      p_SL=float(defaults.get("p_SL", 11.0)),
      max_lvg=float(defaults.get("max_lvg", 10.0)),
      max_margin=float(defaults.get("max_margin", 100.0)),
  )
  trade = Trade(parameters=params)
  return calculate_all(trade)

#for debugging run this function with Debugger till Breakpoint:
#debug_calculate_all()