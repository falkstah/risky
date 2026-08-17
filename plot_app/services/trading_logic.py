#for calculations
import math
import numbers
from typing import Any
from dataclasses import dataclass, is_dataclass, fields
import pandas as pd
from plot_app.domain.trades import Calculation_Error, Trade, Trade_Parameters, Tranche, Tranche_Parameters, Take_Profit_Target, Entry_Level
#import ccxt
#import pandas_ta as ta

#functions that guarantee sfe math:
#div0 protection
def checked_div(numerator: float, denominator: float):
  if denominator == 0:
    raise Calculation_Error("div by 0.")
  return numerator / denominator

#fast solution without complex error handling:
def safe_div(numerator: float, denominator: float, fallback: float):
    if denominator == 0:
        return fallback
    return numerator / denominator

#2. manage SL pulls and TPs for whole position
def calculate_all(trade: Trade):
  #sanitizes trade attributes first and then the attributes in trade-Ojekt tranche.tranche_parameters:
  if trade is None:
    raise ValueError("Trade object is None. Cannot perform calculations.")

  trade = sanitize_inputs(trade)

  #1. calculate all tranche.tranche_parameters for each partial entry (ladder) of a trade with one given SL
  #entry meint ein ListenELement von entry_levels
  for tranche in trade.tranches:
    tranche = calculate_tranche_allocations(trade, tranche)

    #Calculate:
    trade = calculate_initial_risk(trade, tranche)
    trade = calculate_exit_and_tp_structure(trade, tranche)
    trade = calculate_dynamic_state(trade, tranche)

  return trade

#recursiv sanitizer:
def sanitize_inputs(item: Any) -> Any:
    # 1. Prüfen, ob das Item überhaupt eine Dataclass ist
    if is_dataclass(item):
        for f in fields(item):
            value = getattr(item, f.name)
            # Rekursiver Aufruf für verschachtelte Dataclasses und Listen
            if is_dataclass(value) or isinstance(value, list):
                setattr(item, f.name, sanitize_inputs(value))
            else:
                setattr(item, f.name, clean_value(value))
        return item
    elif isinstance(item, list):
        return [sanitize_inputs(sub_item) for sub_item in item]
    else:
        return clean_value(item)
  

def clean_value(value):
    """Hilfsfunktion für die eigentliche Typumwandlung"""
    if value is None:
        return 0.0
    if isinstance(value, bool):
        return value
    if isinstance(value, numbers.Real):
        return float(value)
    if isinstance(value, str):
        return value  #changes nothing at the moment
    return 0.0


def calculate_tranche_allocations(trade, tranche):
  p = trade.trade_parameters  
  t = tranche.tranche_parameters

  #total max_lvg copying:
  t.max_lvg = share_total_max_lvg(trade, tranche)
  #risk and margin sharing
  t.risk = fair_share(tranche, p.total_risk)
  t.max_margin = fair_share(tranche, p.total_max_margin)  #faktor buffer für überbeischerung wird in schleife für jeden entry einzeln eingebaut, nicht schon in trade

  #TPs are managed globally with FiFo principle (exchange standard)

  #SL is global and indifferent to all tranches at the moment, but can be changed later here
  t.p_SL = p.p_SL

  return tranche

  def share_unused_risk(trade):
    #calculate unused risk from all tranches and share it to the (not fully realised) tranches according to their position_share
    total_used_risk = sum(tranche.tranche_parameters.risk for tranche in trade.tranches)
    unused_risk = trade.trade_parameters.total_risk - total_used_risk

    for tranche in trade.tranches:
        tranche.tranche_parameters.risk += fair_share(tranche, unused_risk)

    return trade
  #-> tranches with now new risk potential have to be recalced somehow?

#Sharing rule (Trade -> Tranches):
def fair_share(tranche, pool): 
    return tranche.entry_level.position_share * pool #(="risk- and potential-share")

def calculate_initial_risk(trade: Trade, tranche):

  # 1) Directional basics
  if tranche.entry_level.price == 0.0:
    print("P_Entry is 0.0, cannot calculate trade parameters.")
    return trade

  try:
      tranche.entry_level.price = float(tranche.entry_level.price)
      tranche.tranche_parameters.p_SL = float(tranche.tranche_parameters.p_SL)
  except (TypeError, ValueError):
      raise TypeError("Entry price and Stop Loss price must be numeric values.")

  tranche.tranche_parameters.dirsign = calculate_dirsign(tranche)
  tranche.tranche_parameters.sl_delta = calculate_SL_delta(trade, tranche)
  if tranche.tranche_parameters.sl_delta == 0:
      raise ValueError("SL_delta = 0")

  tranche.tranche_parameters.current_direction = get_trade_direction(trade, tranche)
  tranche.tranche_parameters.rel_risk = calculate_rel_risk(trade, tranche)

  return trade


def calculate_exit_and_tp_structure(trade: Trade, tranche):
  tranche.tranche_parameters = tranche.tranche_parameters
  tranche.tranche_parameters.p_liquidation = match_liquidation_price_to_SL(trade, tranche)
  tranche.tranche_parameters.tp_delta = calculate_tp_delta(trade, tranche)
  return trade


def calculate_dynamic_state(trade: Trade, tranche):
  tranche.tranche_parameters.lvg = find_max_lvg(trade, tranche)
  tranche.tranche_parameters.lvg, tranche.tranche_parameters.risk = check_lvg(trade, tranche)
  tranche.tranche_parameters.max_margin = find_max_margin(tranche)
  tranche.tranche_parameters.initial_margin = calculate_initial_margin(trade, tranche)
  tranche.tranche_parameters.risk, tranche.tranche_parameters.initial_margin = check_initial_margin(trade, tranche)

  tranche.tranche_parameters.n_pos_value = calculate_n_pos_value(trade, tranche)
  tranche.tranche_parameters.maintainance_margin = calculate_maintainance_margin(tranche)
  tranche.tranche_parameters.rel_maintainance_margin = calculate_rel_maintainance_margin(tranche)
  tranche.tranche_parameters.isolated_margin = tranche.tranche_parameters.max_margin

  tranche = evaluate_trade(trade)
  return trade

#margins
#receive fom DEX
#maintainance_margin_rate  # = minimum relative portion of position size that must always be available as equity, otherwise forced liquidation (relative counterpart to absolute maintenance margin); often not as high, worst case assumption
#maintainance_deduction       # "0" is conservative

#initial margin calculation
def calculate_dirsign(tranche):
  entry = getattr(tranche.entry_level, "price", None)
  p_SL = getattr(tranche.tranche_parameters, "p_SL", None)

  if entry is None or p_SL is None:
    raise ValueError("Entry price and Stop Loss price must both be set.")
  if not isinstance(entry, numbers.Real) or not isinstance(p_SL, numbers.Real):
    raise TypeError("Entry price and Stop Loss price must be numeric values.")

  if entry > p_SL:
    return 1
  elif entry < p_SL:
    return -1
  else:
    raise ValueError("Entry and Stop Loss must not be equal.")


def calculate_SL_delta(trade, tranche):
  entry = getattr(tranche.entry_level, "price", None)
  p_SL = getattr(tranche.tranche_parameters, "p_SL", None)
  if entry is None or p_SL is None:
    raise ValueError("Entry price and Stop Loss price must both be set.")
  return abs(entry - p_SL)

def calculate_tp_delta(trade, tranche):
  entry = getattr(tranche.entry_level, "price", None)
  p_TP = getattr(tranche.tp_target, "price", None)
  if entry is None or p_TP is None:
    raise ValueError("Entry price and Take Profit price must both be set.")
  return abs(entry - p_TP)

  #small partial TP1 allows: moving SL under previous Low to ain more buffer. 
  # This function calculates the tp1-size so that buffer_SL hit would stop trade out (p.ex. under a low) without a loss (by risking Tp1 gains)
  # (increae of V if buffer_SL is pulled further to entry could also be interesting, i.e. pyramid entry)
def calculate_buffered_tp1_close_percent(trade: Trade):
  tranche1 = trade.tranches[0]
  entry = tranche1.entry_level.price
  tranche1.tranche_parameters = tranche1.tranche_parameters
  tp1 = trade.global_tp_targets[0].price
  buffer_SL = trade.trade_parameters.buffer_SL

  #useless when it will be included in sanitier:
  if entry is None or tp1 is None or buffer_SL is None:
    raise ValueError("Entry price, TP price and buffer SL must be set.")

  tp_delta = tranche1.tranche_parameters.tp_delta
  buffer_delta = abs(buffer_SL - entry)

  if tp_delta == 0.0:
    raise ValueError("TP price must differ from entry price.")
  if buffer_delta == 0.0:
    return 0.0

  # Buffer SL must be on the correct side of entry for the trade direction.
  if tranche1.tranche_parameters.current_direction is None:
    tranche1.tranche_parameters.current_direction = get_trade_direction(trade, tranche1)
  if tranche1.tranche_parameters.current_direction == "long" and buffer_SL >= entry:
    raise ValueError("Buffer SL must be below entry for a long trade.")
  if tranche1.tranche_parameters.current_direction == "short" and buffer_SL <= entry:
    raise ValueError("Buffer SL must be above entry for a short trade.")

  #profit(TP1) = close_fraction * n_pos_value * (TP1 - entry)
  #unclosed_pos_rest = (1 - x) * n_pos_value
  #Loss(buffer_SL) = uncloses_pos_rest * n_pos_value * (entry - buffer_SL)
  #Profit(TP1) == Loss(buffer_SL)  -> solve for close_fraction: close_fraction = buffer_delta / (TP1 - buffer_SL)
  #with TP1 - buffer_SL = tp_delta + buffer_delta:
  close_fraction = buffer_delta / (tp_delta + buffer_delta)
  return float(close_fraction)


def get_trade_direction(trade, tranche):
  dirsign = getattr(tranche.tranche_parameters, "dirsign", None)
  if dirsign is None:
    raise ValueError("dirsign must be calculated before determining trade direction.")

  if dirsign > 0:
    return "long"
  elif dirsign < 0:
    return "short"
  else:
    print("Trade direction not consistent. Please check your input parameters.")
  return None

def calculate_rel_risk(trade, tranche):
  return abs(tranche.tranche_parameters.sl_delta) / tranche.entry_level.price

def calculate_initial_margin(trade, tranche):
  return tranche.tranche_parameters.risk / (tranche.tranche_parameters.rel_risk * tranche.tranche_parameters.lvg) # initial margin >= maintainance_margin (immer)

def calculate_initial_margin_rate(lvg):
  return 1 / lvg

#live calculation; sign matches trade direction, abs(n_pos_value) is used for position calculations that do not depend on direction
def calculate_n_pos_value(trade, tranche):
  return tranche.tranche_parameters.dirsign * tranche.tranche_parameters.risk / tranche.tranche_parameters.rel_risk # = initial_margin * lvg - thus couples lvg and initial_margin; n_pos_value < 0 <==> short

def share_total_max_lvg(trade, tranche):
  return trade.trade_parameters.total_max_lvg

def calculate_max_lvg(trade, tranche):
  return math.floor(1 / tranche.tranche_parameters.maintainance_margin_rate)

#can differ or long and short even for same sl_delta and liq distance, which is against Intuiton; not symmetrical!!! hat's no error
def max_lvg_for_given_liquidation(trade, tranche):
  entry = tranche.entry_level.price
  if tranche.tranche_parameters.current_direction == "long":
    lvg = math.floor(1 / (1 + tranche.tranche_parameters.maintainance_margin_rate + tranche.tranche_parameters.maintainance_deduction - tranche.tranche_parameters.p_liquidation / entry))  # = general p_liq formula solved for lvg; formula can get < 1
  elif tranche.tranche_parameters.current_direction == "short":
    lvg = math.floor(1 / (1 + tranche.tranche_parameters.maintainance_margin_rate + tranche.tranche_parameters.maintainance_deduction -  entry / tranche.tranche_parameters.p_liquidation))
  else: lvg = 0
  return lvg 

def find_max_lvg(trade, tranche):
  max_allowed_lvg = calculate_max_lvg(trade, tranche)
  max_lvg_liq = max_lvg_for_given_liquidation(trade, tranche)
  #both formulas give upper lvg limits, hence the smaller one has to be chosen. But lvg >= 1 with max:
  lvg = math.floor(min(max_allowed_lvg, max_lvg_liq)) #floor guarantees that lvg does not force early liq
  return lvg

#risk correction functions
def check_lvg(trade, tranche):
  risk = tranche.tranche_parameters.risk
  lvg = tranche.tranche_parameters.lvg
  if lvg > tranche.tranche_parameters.max_lvg:  # Assuming tranche.tranche_parameters.max_lvg is 10
    print(f"Warning: Calculated leverage {lvg} exceeds {tranche.tranche_parameters.max_lvg}. Risk will be made smaller to adjust.")
    lvg = tranche.tranche_parameters.max_lvg
    risk = reduce_risk(trade, tranche)

  if lvg < 1:
    print("lvg < 1. Over secuing already guaranteed by find_max_margin. hence, buffer is too big. Risk too small.")
    lvg = 1
    #possibly risk has to be fitted
  return lvg, risk

def reduce_risk(trade, tranche):
   return tranche.tranche_parameters.max_margin * tranche.tranche_parameters.max_lvg * tranche.tranche_parameters.rel_risk


#Risk: if price moves against me, my account balance decreases = posted margin shrinks -> if maintenance margin <= 2% * n_pos_value: forced liquidation
#->live updates necessary for the following values:
def calculate_maintainance_margin(tranche):
  return abs(tranche.tranche_parameters.n_pos_value) * tranche.tranche_parameters.maintainance_margin_rate + tranche.tranche_parameters.maintainance_deduction # Maintenance margin is a positive requirement; direction is already encoded in n_pos_value

def calculate_rel_maintainance_margin(tranche):
  #only useful during the trade, because margin changes and rel_maintainance_margin may no longer equal MMR
  if tranche.tranche_parameters.n_pos_value != 0:
    return tranche.tranche_parameters.maintainance_margin / abs(tranche.tranche_parameters.n_pos_value) # = maintainance_margin_rate if maintainance_margin_deduction == 0
  else:
    return 0.0  #avoids div by 0
  
def p_liq_exchange_forced(tranche):
  return tranche.entry_level.price * (1 - tranche.tranche_parameters.maintainance_margin)


#Strategy Feedback
#checks triggered for one of the ladder entries:
def check_global_TP_hits(trade, index):
  for tp in trade.global_tp_targets:
    tp.triggered = tp.price <= trade.trade_parameters.current_asset_price #bool, has to track all the values price had in meantime,  so not correct yet
  return trade

def is_tranche_TP_active(tranche):
  t = tranche.tp_target
  p = tranche.entry_level
  if t.price <= 0:
    return False
  if tranche.tranche_parameters.dirsign > 0:
    return t.price > p.price  #bool equation
  if tranche.tranche_parameters.dirsign < 0:
    return t.price < p.price
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
def match_liquidation_price_to_SL(trade, tranche):
    return max(tranche.entry_level.price - tranche.tranche_parameters.liq_delta_to_SL_delta_ratio * tranche.tranche_parameters.sl_delta * tranche.tranche_parameters.dirsign, 0) #SL_delta is now the absolute distance; dirsign restores the long/short sign

#def match_lvg_to_liquidation_price(tranche.tranche_parameters: Trade_Parameters):
#  return 1 / (1 + tranche.tranche_parameters.maintainance_margin_rate - tranche.tranche_parameters.p_liquidation * (1 + tranche.tranche_parameters.maintainance_margin_rate) / tranche.tranche_parameters.p_entry)  # = general p_liq formula solved for lvg; formula can get < 1

def find_max_margin(tranche):
   return 0.9 * tranche.tranche_parameters.max_margin #forces over securing margin, to avoid margin calls and forced liquidation

def check_initial_margin(trade, tranche):
  max_margin = max(tranche.tranche_parameters.max_margin, 1.0)
  if tranche.tranche_parameters.initial_margin > max_margin:
    print(f"margin-demand too high. Reducing risk to fit max_margin={max_margin}")
    risk = max_margin * tranche.tranche_parameters.rel_risk * tranche.tranche_parameters.lvg
    return risk, calculate_initial_margin(trade, tranche)
  else:
    risk = tranche.tranche_parameters.risk
    initial_margin = tranche.tranche_parameters.initial_margin
    return risk, initial_margin
  
def check_rrr(rrr):
  if rrr < 2:
    print("rrr is small.")

#safety calculus
#evaluating trading setups

def evaluate_trade(trade):
  for tranche in trade.tranches:
    tranche = evaluate_tranche(tranche)

  #still missing: global evaluation (evaluating cumulated effect of all tranches)
  return trade

def evaluate_tranche(tranche):
  t = tranche
  t.tranche_parameters.rel_asset_gain_at_TP = tranche.tranche_parameters.tp_delta / tranche.entry_level.price
  t.tranche_parameters.rrr = safe_div(tranche.tranche_parameters.tp_delta, tranche.tranche_parameters.sl_delta, 0.0)
  t.tranche_parameters.potential_profit = tranche.tranche_parameters.risk * t.tranche_parameters.rrr
  t.tranche_parameters.equity = calculate_tranche_equity(tranche)

  return t

def calulate_tranche_profit_at_price_p(tranche, p):
  entry = tranche.entry_level.price
  if p >= entry:
    return tranche.tranche_parameters.dirsign * abs(p - entry) / entry * abs(tranche.tranche_parameters.n_pos_value) #for long and short (pos value)
  else:
    return -1 * tranche.tranche_parameters.dirsign * abs(p - entry) / entry * abs(tranche.tranche_parameters.n_pos_value) #for long and short (pos value)

def update_asset_price(trade):
  for tranche in trade.tranches:
      if trade.trade_parameters.current_asset_price >= tranche.price:
        tranche.triggered = True


def calculate_total_trade_profit(trade):
  profit = 0.0
  for tp in trade.global_tp_targets:
    if tp.triggered:
      profit += tp.profit
  return profit

def calculate_potential_total_trade_profit(trade):
  profit = 0.0
  for tp in trade.global_tp_targets:
    profit += tp.profit
  return profit

def calculate_total_rrr(trade):
  total_rrr = trade.trade_parameters.total_potential_trade_profit / trade.trade_parameters.total_risk
  return total_rrr

def calculate_avg_entry_price(trade):
  number_of_entries = 0
  weighted_sum = 0
  for tranche in trade.tranches:
    number_of_entries += 1
    weighted_sum += tranche.tranche_parameters.n_pos_value * tranche.entry_level.price

  avg_entry_price = weighted_sum / number_of_entries
  return avg_entry_price

def calculate_equity(trade):
  t = trade
  for tranche in t.tranches:
    tranche.tranche_parameters.equity = calculate_tranche_equity(tranche)
  return t
    
def calculate_tranche_equity(tranche):
  return tranche.tranche_parameters.initial_margin - tranche.tranche_parameters.loss

'''
def debug_calculate_all(**overrides):
  #Create a Trade_Parameters object with default inputs and run calculate_all for debugging.
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

  #takes given tranche.tranche_parameters with default values as Fallback (in parantheses)
  #tp, entry to be added!!!
  tranche_parameters = Tranche_Parameters(
      liq_delta_to_SL_delta_ratio=float(defaults.get("liq_delta_to_SL_delta_ratio", 4.0)),
      risk=float(defaults.get("risk", 10.0)),
      maintainance_margin_rate=float(defaults.get("maintainance_margin_rate", 0.02)),
      maintainance_deduction=float(defaults.get("maintainance_deduction", 0.0)),
      p_SL=float(defaults.get("p_SL", 11.0)),
      max_lvg=float(defaults.get("max_lvg", 10.0)),
      max_margin=float(defaults.get("max_margin", 100.0)),
  )
  tranche = Tranche(tranche_parameters = Tranche_Parameters)
  trade = Trade()
  return calculate_all(trade)

#for debugging run this function with Debugger till Breakpoint:
#debug_calculate_all()

'''