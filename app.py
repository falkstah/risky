# -*- coding: utf-8 -*-
import math
import pandas as pd
#import ccxt
#import pandas_ta as ta

import streamlit as st
import altair as alt

st.title("Too_Risky - Crypto live lvg and liquidation manager")
st.text("Opimized for execution speed.")
#margins
#receive fom DEX
#maintainance_margin_rate  # = minimaler rel. Anteil an Positionsgröße, der als Eigenkapital stets verfügbar sein muss, sonst Zwangsliquidation (rel. Pendant zur absoluten Mainainance  Margin); oft nicht so hoch, worst case Annahme
#maintainance_deduction       # "0" ist konsevativ

#initial margin calculation
def calculate_SL_delta(p_entry, p_SL):
  if p_entry == p_SL:
    print("Entry and SL are equal. Please check your input parameters.")
  return p_entry - p_SL

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
def calculate_maintainance_margin(n_pos_value, maintainance_margin, maintainance_deduction):
  return n_pos_value * maintainance_margin_rate + maintainance_deduction # Deduction-Abzug ist ein Entgegenkommen des Brokers für effizientere Liquidation

def calculate_rel_maintainance_margin(maintainance_margin, n_pos_value):
  return maintainance_margin / n_pos_value # = maintainance_margin_rate if maintainance_margin_deduction == 0

#safety calculus
#evaluating trading setups
def evaluate_trade(p_entry, p_TP, p_SL, lvg):
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
def match_liquidation_price_to_SL(p_entry, p_SL):
    return max(p_entry - Liq_Delta_to_SL_Delta_ratio * SL_delta, 0) #SL_delta VZ berücksichtigt long/short; max-Funtion, weil Liquidations-Preis minimal bei 0 sein kann, da Preis >= 0

def match_lvg_to_liquidation_price(p_entry, p_SL, p_liquidation, maintainance_margin_rate):
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

def check_initial_margin(old_risk, initial_margin):
  if initial_margin > 100:
    print("margin-demand too high. Lower the risk!")
    new_risk = float(input("new risk: "))
    return new_risk
  else:
    return risk

def check_rrr(rrr):
  if rrr < 2:
    print("rrr is small.")

def calulate_profit_at_price_p(p_entry, p):
  return (p - p_entry) / p_entry * n_pos_value #for long and short (pos value)

def calculate_equity(p_entry, p_SL, n_pos_value, maintainance_margin, loss):
  return initial_margin - loss

def test_liquidation_behaviour(p_entry, p_SL, p_liquidation, initial_margin, Liq_Delta_to_SL_Delta_ratio):
  loss_at_p_liquidation = -1 * calulate_profit_at_price_p(p_entry, p_liquidation)
  print("loss at liquidation price: ", loss_at_p_liquidation, " - should be a little more than 4 times the risk, bc of liq buffer. But of course maximum is full initial_margin whe lvg = 1")
  maintainance_margin_at_p_liquidation = initial_margin - loss_at_p_liquidation

  if maintainance_margin_at_p_liquidation >  maintainance_margin_rate* n_pos_value and round(loss_at_p_liquidation, 0) == round(risk, 0):
    print("Calculation success.")
    valid_caluclation = True
  else:
    print("Calculation Error.")
    valid_caluclation = False
  return valid_caluclation


#trade specific values
def get_trade_parameters():
  print("Enter parameters: ")
  risk = max(float(st.number_input("risk: ", value = 10, min_value = 0.01, step = 0.01)), 0)
  maintainance_margin_rate = max(float(st.number_input("maintainance_margin_rate: ", value = 0.02, min_value = 0.001, step = 0.001)), 0)
  maintainance_deduction = max(float(st.number_input("maintainance_deduction: ", value = 0.0, min_value = 0.001, step = 0.001)), 0)
  p_entry = max( float(st.number_input("entry: ", value = None, min_value = 0.01, step = 0.01)), 0)
  p_SL = max( float(st.number_input("SL: ", value = None, min_value = 0.00, step = 0.01)), 0)
  return risk, maintainance_margin_rate, maintainance_deduction, p_entry, p_SL

def get_TP():
  p_TP = max(float(st.number_input("TP: ", min_value = 0.01, step = 0.01)), 0)
  return p_TP

def get_trade_direction(SL_delta):
  if SL_delta > 0:
    return "long"
  elif SL_delta < 0:
    return "short"
  else:
    print("Trade direction not consistent. Please check your input parameters.")
    return None

def current_direction_label(current_direction):
  if current_direction == "long":
    st.success("Long")
  elif current_direction == "short":
    st.error("Short")
  else:
    st.warning("Trade direction not consistent. Please check your input parameters.")

def parameters_table(p_entry, p_SL, p_TP, p_liquidation, lvg, n_pos_value, initial_margin, maintainance_margin, rrr, rel_asset_gain_at_TP, potential_profit):
  #table1:
  with st.container(border=True):
  
  
  
        st.subheader("📊 Fast Order Table")
        
        # Wir nutzen Spalten für eine saubere Anordnung nebeneinander
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("lvg", f"{lvg} x")
        col2.metric("isolated margin", f"{initial_margin} $")
        col3.metric("p_liquidation", f"{p_liquidation} $")
        col4.metric("n_pos_value", f"{n_pos_value} $")
  
  st.divider() # Visuelle Trennlinie zwischen den Abschnitten
  
  with st.container(border=True):

      st.subheader("📊 Overview")
      
      # Wir nutzen Spalten für eine saubere Anordnung nebeneinander
      col1, col2, col3, col4, col5 = st.columns(5)
      col1.metric("SL Delta", f"{SL_delta} $")
      col2.metric("Risk", f"{risk} $")
      col3.metric("Relative Risk", f"{rel_risk} $")
      col4.metric("Initial Margin", f"{initial_margin} $")
      col5.metric("potential_profit", f"{potential_profit} $")

  st.divider() # Visuelle Trennlinie zwischen den Abschnitten

  #table2:
  with st.container(border=True):
      st.subheader("💰 Risk Feedback")
      
      col1, col2, col3, col4, col5 = st.columns(5)
      col1.metric("Risiko", f"{risk} €")
      col2.metric("rrr", f"{rrr}")
      col3.metric("relative Gain", f"{rel_asset_gain_at_TP * 100:.2f}%")
      col4.metric("Wartungsmarge", f"{maintainance_margin} €")
      col5.metric("rel asset gain at TP", f"{rel_asset_gain_at_TP * 100:.2f}%")

  st.divider()


def visualize_trade(p_entry, p_TP, p_SL, current_direction, p_liquidation):
  st.title("Trade Visualizer")

  # --- 2. DIE LOGIK & DER BALKEN (Nutzt einfach die Variablen von oben) ---
  is_long = p_entry > p_SL
  direction_text = "LONG 🟢" if is_long else "SHORT 🔴"

  try:
    balken_unten = 0.0

    #ba top
    tp_aktiv = False
    if p_TP > 0:  #hence, tp exists
      if SL_delta > 0:  # long case
        if p_TP > p_entry:  #valid TP
          balken_oben = p_TP 
          tp_aktiv = True
        else: #invalid TP
          balken_oben = p_entry

      elif SL_delta < 0:  # short case
        if p_TP < p_entry:  #valid TP
          balken_oben = p_TP
          tp_aktiv = True
        else: #invalid TP
          balken_oben = p_entry
      else:
        balken_oben = p_liquidation  
        tp_aktiv = True
    else:
        balken_oben = max(p_entry, p_liquidation)  #covers short and long case

    # Daten fürs Chart zusammenbauen
    zone_data = pd.DataFrame({
        'y_min': [balken_unten],
        'y_max': [balken_oben],
        'Zone': ['Preisbereich']
    })

    preise = [p_entry, p_SL, p_liquidation]
    labels = ['Entry', 'Stop Loss', 'Liquidation']
    typen = ['entry', 'sl', 'liq']

    if tp_aktiv:
        preise.append(p_TP)
        labels.append('Take Profit')
        typen.append('tp')

    lines_data = pd.DataFrame({
        'Preis': preise,
        'Label': labels,
        'Typ': typen
    })

    # Chart zeichnen
    base = alt.Chart(zone_data).encode(x=alt.X('Zone', title=None, axis=None))
    area = base.mark_rect(opacity=0.2, color='#3b82f6').encode(
        y=alt.Y('y_min', title='Preis in USDT', scale=alt.Scale(domain=[0, balken_oben * 1.05])),
        y2='y_max'
    )
    rule = alt.Chart(lines_data).mark_rule(strokeWidth=2).encode(
        y=alt.Y('Preis'),
        color=alt.Color('Typ', scale={'domain': ['entry', 'sl', 'tp'], 'range': ['#10b981', '#ef4444', '#3b82f6']}, legend=None),
        tooltip=['Label', 'Preis']
    )
    text = rule.mark_text(align='left', dx=5, dy=-5).encode(text='Label')

    chart = alt.layer(area, rule, text).properties(height=500, width=200).interactive()

    # In Streamlit anzeigen
    st.altair_chart(chart, use_container_width=True)
  except:
    st.warning("Error in visualizing trade. Please check your input parameters.")


#main


#at the moment, one time input for fixed parameters:
risk, maintainance_margin_rate, maintainance_deduction, p_entry, p_SL= get_trade_parameters()
#Calculating basic parameters
SL_delta = calculate_SL_delta(p_entry, p_SL)
if SL_delta == 0: #this would lead to division by zero in the following calculations
  print("SL_delta is zero. Please check your input parameters.")
  st.stop()

rel_risk = calculate_rel_risk(p_entry, p_SL)

#UI view:
current_direction = get_trade_direction(calculate_SL_delta(p_entry, p_SL))
current_direction_label(current_direction)

valid_parameters = False
while not valid_parameters:
  #hardcoded paramteres for simplicity
  Liq_Delta_to_SL_Delta_ratio = 4 #means the primitive buffer (Liq distance is et to 4 times SL distance to prevent liq from high volatility whicks)
  maintainance_margin_rate = 0.02
  maintainance_deduction = 0

  #Calculating Final Parameters to input in exchange menu
  p_liquidation = match_liquidation_price_to_SL(p_entry, p_SL)
  lvg = match_lvg_to_liquidation_price(p_entry, p_SL, p_liquidation, maintainance_margin_rate)

  #lvg Correction
  lvg = check_lvg(lvg)

  #Calculating Margins
  initial_margin = calculate_initial_margin(risk, rel_risk, lvg)

  #correcting risk too limit initial_margin
  old_risk = risk
  risk = check_initial_margin(risk, initial_margin)
  if risk != old_risk:  # rechnet nur weiter, wenn risk unverändert, sonst beginnt Prozess von vorne, ist ineffizient, weil Entry und Sl ja eigtl nicth nochmal neu gebraucht werden
    continue

  n_pos_value = calculate_n_pos_value(lvg, initial_margin)  #bought USDC-amount

  maintainance_margin = calculate_maintainance_margin(n_pos_value, maintainance_margin_rate, maintainance_deduction)
  rel_maintainance_margin = calculate_rel_maintainance_margin(maintainance_margin, n_pos_value)

  #input ends, when all risks killed (i.e. code run through until here without while continuation)
  valid_parameters = True

#fast Order Output:
print(f"""
  Input Check:
  p_entry:              {round(p_entry, 2)}
  p_SL:                 {round(p_SL, 2)}

  Calculated Parameters:
  lvg:                  {round(lvg, 2)}
  n_pos_value:          {round(n_pos_value, 2)}

  Management:
  risk:                 {round(risk, 2)}
  initial_margin:       {round(initial_margin, 2)}
  maintainance_margin:  {round(maintainance_margin, 2)}

      """)

#Output

#risk feedback
p_TP = get_TP()
rel_asset_gain_at_TP, rrr, potential_profit = evaluate_trade(p_entry, p_TP, p_SL, lvg)

parameters_table(p_entry, p_SL, p_TP, p_liquidation, lvg, n_pos_value, initial_margin, maintainance_margin, rrr, rel_asset_gain_at_TP, potential_profit)
visualize_trade(p_entry, p_TP, p_SL, current_direction, p_liquidation)

print(f"""
  Input Check:
  p_entry:              {round(p_entry, 2)}
  p_SL:                 {round(p_SL, 2)}
  p_TP:                 {round(p_TP, 2)}

  Calculated Parameters:
  lvg:                  {round(lvg, 2)}
  n_pos_value:          {round(n_pos_value, 2)}

  Management:
  initial_margin:       {round(initial_margin, 2)}
  maintainance_margin:  {round(maintainance_margin, 2)}
  p_liquidation:        {round(p_liquidation, 2)}

  rrr:                  {round(rrr, 2)}
  rel_asset_gain_at_TP: {round(rel_asset_gain_at_TP * 100, 2)}%
  equity at liquidation: {round(calculate_equity(p_entry, p_SL, n_pos_value, maintainance_margin, p_liquidation), 2)}

      """)

valid_calculations = test_liquidation_behaviour(p_entry, p_SL, p_liquidation, initial_margin, Liq_Delta_to_SL_Delta_ratio)
print("valid calculations: ", valid_calculations)