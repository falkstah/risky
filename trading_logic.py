#for calculations
import math
import pandas as pd
#import ccxt
#import pandas_ta as ta

def calculate_all(liq_delta_to_SL_delta_ratio, risk, maintainance_margin_rate, maintainance_deduction, p_entry, p_SL, p_TP):
    #main

    #Calculating basic parameters
    SL_delta = calculate_SL_delta(p_entry, p_SL)
    if SL_delta == 0: #this would lead to division by zero in the following calculations
        raise ValueError("SL_delta = 0")

    rel_risk = calculate_rel_risk(p_entry, p_SL)

    #UI view:
    current_direction = get_trade_direction(calculate_SL_delta(p_entry, p_SL))
    

    #hardcoded paramteres for simplicity
    liq_delta_to_SL_delta_ratio = 4 #means the primitive buffer (Liq distance is et to 4 times SL distance to prevent liq from high volatility whicks)

    #Calculating Final Parameters to input in exchange menu
    p_liquidation = match_liquidation_price_to_SL(liq_delta_to_SL_delta_ratio, p_entry, SL_delta)
    lvg = match_lvg_to_liquidation_price(p_entry, p_liquidation, maintainance_margin_rate)

    #lvg Correction
    lvg = check_lvg(lvg)

    #Calculating Margins
    initial_margin = calculate_initial_margin(risk, rel_risk, lvg)

    #correcting risk too limit initial_margin
    old_risk = risk
    risk = check_initial_margin(risk, initial_margin)
    if risk != old_risk:  # rechnet nur weiter, wenn risk unverändert, sonst beginnt Prozess von vorne, ist ineffizient, weil Entry und Sl ja eigtl nicth nochmal neu gebraucht werden
        raise ValueError("Risk was primitively reduced. Please re-enter parameters.")

    n_pos_value = calculate_n_pos_value(lvg, initial_margin)  #bought USDC-amount

    maintainance_margin = calculate_maintainance_margin(n_pos_value, maintainance_margin_rate, maintainance_deduction)
    rel_maintainance_margin = calculate_rel_maintainance_margin(maintainance_margin, n_pos_value)

    #input ends, when all risks killed (i.e. code run through until here without while continuation)
    valid_parameters = True

    #risk feedback
    rel_asset_gain_at_TP, rrr, potential_profit = evaluate_trade(risk, p_entry, p_TP, p_SL)

    valid_calculations = test_liquidation_behaviour(liq_delta_to_SL_delta_ratio, risk, p_entry, p_SL, p_liquidation, initial_margin)
    print("valid calculations: ", valid_calculations)
    
    return SL_delta, rel_risk, current_direction, p_liquidation, lvg, initial_margin, n_pos_value, maintainance_margin, rel_maintainance_margin, rel_asset_gain_at_TP, rrr, potential_profit


#margins
#receive fom DEX
#maintainance_margin_rate  # = minimaler rel. Anteil an Positionsgröße, der als Eigenkapital stets verfügbar sein muss, sonst Zwangsliquidation (rel. Pendant zur absoluten Mainainance  Margin); oft nicht so hoch, worst case Annahme
#maintainance_deduction       # "0" ist konsevativ

#initial margin calculation
def calculate_SL_delta(p_entry, p_SL):
  if p_entry == p_SL:
    print("Entry and SL are equal. Please check your input parameters.")
  return p_entry - p_SL

def get_trade_direction(SL_delta):
  if SL_delta > 0:
    return "long"
  elif SL_delta < 0:
    return "short"
  else:
    print("Trade direction not consistent. Please check your input parameters.")
    return None

def calculate_rel_risk(p_entry, p_SL):
  return abs(p_entry-p_SL)/p_entry

def calculate_initial_margin(risk, rel_risk, lvg):
  return risk / (rel_risk * lvg) # initial margin >= maintainance_margin (immer)

def calculate_initial_margin_rate(lvg):
  return 1 / lvg

#live calculation
def calculate_n_pos_value(lvg, initial_margin):
  return initial_margin * lvg

#Risiko: wenn Kurs gegen mich läuft sinkt mein Kontostand = hinterlegte Margin schrumpft -> bei maintainance margin <= 2%*n_pos_value: Zwangsliquidation
#->live updates für folgende Werte nötig:
def calculate_maintainance_margin(n_pos_value, maintainance_margin_rate, maintainance_deduction):
  return n_pos_value * maintainance_margin_rate + maintainance_deduction # Deduction-Abzug ist ein Entgegenkommen des Brokers für effizientere Liquidation

def calculate_rel_maintainance_margin(maintainance_margin, n_pos_value):
  return maintainance_margin / n_pos_value # = maintainance_margin_rate if maintainance_margin_deduction == 0

#safety calculus
#evaluating trading setups
def evaluate_trade(risk, p_entry, p_TP, p_SL):
  rel_asset_gain_at_TP = (p_TP - p_entry)/p_entry
  rrr = (p_TP - p_entry) / (p_entry - p_SL)
  potential_profit = risk * rrr
  return rel_asset_gain_at_TP, rrr, potential_profit

  #cases:
#Liquidation_through_Hard_Stop: p_SL
#Maintainance_Margin_Liquidation


#volatility-dependent margin liquidation buffer
# terminal setup installation for ATR calculation: (delete # for first run)
#!pip install ccxt pandas pandas-ta
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
def match_liquidation_price_to_SL(liq_delta_to_SL_delta_ratio, p_entry, SL_delta):
    return max(p_entry - liq_delta_to_SL_delta_ratio * SL_delta, 0) #SL_delta VZ berücksichtigt long/short; max-Funtion, weil Liquidations-Preis minimal bei 0 sein kann, da Preis >= 0

def match_lvg_to_liquidation_price(p_entry, p_liquidation, maintainance_margin_rate):
  return 1 / (1 + maintainance_margin_rate - p_liquidation * (1 + maintainance_margin_rate) / p_entry)  # = general p_liq formula solved for lvg; formula can get < 1

#risk correction functions

def check_lvg(lvg):
  if lvg > 10:
    print("Lvg will be stopped at 10")
    lvg = 10
  elif lvg < 1:
    print("Lvg < 1. Spot buy. (Positionsrisiko könnte kleiner als gewünschtes Risiko werden?).")
    lvg = 1
  return lvg

def check_initial_margin(risk, initial_margin):
  if initial_margin > 100:
    print("margin-demand too high. Lower the risk!")
    new_risk = float(input("new risk: "))
    return new_risk
  else:
    return risk

def check_rrr(rrr):
  if rrr < 2:
    print("rrr is small.")

def calulate_profit_at_price_p(p_entry, p, n_pos_value):
  return (p - p_entry) / p_entry * n_pos_value #for long and short (pos value)

def calculate_equity(initial_margin, loss):
  return initial_margin - loss

def test_liquidation_behaviour(liq_delta_to_SL_delta_ratio, risk, p_entry, p_SL, n_pos_value, p_liquidation, initial_margin, maintainance_margin_rate):
  loss_at_p_liquidation = -1 * calulate_profit_at_price_p(p_entry, p_liquidation, n_pos_value)
  print("loss at liquidation price: ", loss_at_p_liquidation, " - should be a little more than 4 times the risk, bc of liq buffer. But of course maximum is full initial_margin whe lvg = 1")
  maintainance_margin_at_p_liquidation = initial_margin - loss_at_p_liquidation

  if maintainance_margin_at_p_liquidation >  maintainance_margin_rate * n_pos_value and round(loss_at_p_liquidation, 0) == round(risk, 0):
    print("Calculation success.")
    valid_caluclation = True
  else:
    print("Calculation Error.")
    valid_caluclation = False
  return valid_caluclation