#for calculations
import math
import pandas as pd
from classes import TradeParameters
#import ccxt
#import pandas_ta as ta

def calculate_all(params: TradeParameters):
    # main

    # Calculating basic parameters
    params.sl_delta = calculate_SL_delta(params)
    if params.sl_delta == 0: # this would lead to division by zero in the following calculations
        raise ValueError("SL_delta = 0")

    rel_risk = calculate_rel_risk(params)
    params.rel_risk = rel_risk

    # UI view:
    params.current_direction = get_trade_direction(params)
    params.tp_active = calculate_tp_active(params)

    # hardcoded paramteres for simplicity
    params.liq_delta_to_SL_delta_ratio = 4 # means the primitive buffer (Liq distance is set to 4 times SL distance to prevent liq from high volatility whicks)

    # Calculating Final Parameters to input in exchange menu
    params.p_liquidation = match_liquidation_price_to_SL(params)
    params.lvg = match_lvg_to_liquidation_price(params)
    params.lvg = check_lvg(params.lvg)

    params.initial_margin = calculate_initial_margin(params)

    # correcting risk to limit initial_margin
    old_risk = params.risk
    params.risk = check_initial_margin(params, params.initial_margin)
    if params.risk != old_risk:
        raise ValueError("Risk was primitively reduced. Please re-enter parameters.")

    params.n_pos_value = calculate_n_pos_value(params)

    params.maintainance_margin = calculate_maintainance_margin(params, params.n_pos_value)
    params.rel_maintainance_margin = calculate_rel_maintainance_margin(params)

    # risk feedback
    params.rel_asset_gain_at_TP, params.rrr, params.potential_profit = evaluate_trade(params)

    valid_calculations = test_liquidation_behaviour(params, params.initial_margin)
    print("valid calculations: ", valid_calculations)

    return params


#margins
#receive fom DEX
#maintainance_margin_rate  # = minimaler rel. Anteil an Positionsgröße, der als Eigenkapital stets verfügbar sein muss, sonst Zwangsliquidation (rel. Pendant zur absoluten Mainainance  Margin); oft nicht so hoch, worst case Annahme
#maintainance_deduction       # "0" ist konsevativ

#initial margin calculation
def calculate_SL_delta(params: TradeParameters):
  if params.p_entry == params.p_SL:
    print("Entry and SL are equal. Please check your input parameters.")
  return params.p_entry - params.p_SL

def get_trade_direction(params: TradeParameters):
  if params.sl_delta > 0:
    return "long"
  elif params.sl_delta < 0:
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
  return params.initial_margin * params.lvg

#Risiko: wenn Kurs gegen mich läuft sinkt mein Kontostand = hinterlegte Margin schrumpft -> bei maintainance margin <= 2%*n_pos_value: Zwangsliquidation
#->live updates für folgende Werte nötig:
def calculate_maintainance_margin(params: TradeParameters, n_pos_value):
  return n_pos_value * params.maintainance_margin_rate + params.maintainance_deduction # Deduction-Abzug ist ein Entgegenkommen des Brokers für effizientere Liquidation

def calculate_rel_maintainance_margin(params: TradeParameters):
  return params.maintainance_margin / params.n_pos_value # = maintainance_margin_rate if maintainance_margin_deduction == 0

#safety calculus
#evaluating trading setups
def evaluate_trade(params: TradeParameters):
  rel_asset_gain_at_TP = (params.p_TP - params.p_entry) / params.p_entry
  rrr = (params.p_TP - params.p_entry) / (params.p_entry - params.p_SL)
  potential_profit = params.risk * rrr
  return rel_asset_gain_at_TP, rrr, potential_profit

def calculate_tp_active(params: TradeParameters):
  if params.p_TP <= 0:
    return False
  if params.sl_delta > 0:
    return params.p_TP > params.p_entry
  if params.sl_delta < 0:
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
    return max(params.p_entry - params.liq_delta_to_SL_delta_ratio * params.sl_delta, 0) #SL_delta VZ berücksichtigt long/short; max-Funtion, weil Liquidations-Preis minimal bei 0 sein kann, da Preis >= 0

def match_lvg_to_liquidation_price(params: TradeParameters):
  return 1 / (1 + params.maintainance_margin_rate - params.p_liquidation * (1 + params.maintainance_margin_rate) / params.p_entry)  # = general p_liq formula solved for lvg; formula can get < 1

#risk correction functions

def check_lvg(lvg):
  if lvg > 10:
    print("Lvg will be stopped at 10")
    lvg = 10
  elif lvg < 1:
    print("Lvg < 1. Spot buy. (Positionsrisiko könnte kleiner als gewünschtes Risiko werden?).")
    lvg = 1
  return lvg

def check_initial_margin(params: TradeParameters, initial_margin):
  if initial_margin > 100:
    print("margin-demand too high. Lower the risk!")
    new_risk = float(input("new risk: "))
    return new_risk
  else:
    return params.risk

def check_rrr(rrr):
  if rrr < 2:
    print("rrr is small.")

def calulate_profit_at_price_p(params: TradeParameters, p):
  return (p - params.p_entry) / params.p_entry * params.n_pos_value #for long and short (pos value)

def calculate_equity(initial_margin, loss):
  return initial_margin - loss

def test_liquidation_behaviour(params: TradeParameters, initial_margin):
  loss_at_p_liquidation = -1 * calulate_profit_at_price_p(params, params.p_liquidation)
  print("loss at liquidation price: ", loss_at_p_liquidation, " - should be a little more than 4 times the risk, bc of liq buffer. But of course maximum is full initial_margin whe lvg = 1")
  maintainance_margin_at_p_liquidation = initial_margin - loss_at_p_liquidation

  if maintainance_margin_at_p_liquidation > params.maintainance_margin_rate * params.n_pos_value and round(loss_at_p_liquidation, 0) == round(params.risk, 0):
    print("Calculation success.")
    valid_caluclation = True
  else:
    print("Calculation Error.")
    valid_caluclation = False
  return valid_caluclation