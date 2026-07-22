# -*- coding: utf-8 -*-
import streamlit as st
import altair as alt

import pandas as pd

#logic functions
from trading_logic import calculate_all

st.title("Too_Risky - Crypto live lvg and liquidation manager")
st.text("Opimized for execution speed.")

#trade specific values
def get_trade_parameters():
  print("Enter parameters: ")
  liq_delta_to_SL_delta_ratio = max(float(st.number_input("liq_delta_to_SL_delta_ratio: ", value = 4, step = 0.25)), 1)
  risk = max(float(st.number_input("risk: ", value = 10, step = 1)), 0)
  maintainance_margin_rate = max(float(st.number_input("maintainance_margin_rate: ", value = 0.02, step = 0.001)), 0)
  maintainance_deduction = max(float(st.number_input("maintainance_deduction: ", value = 0.0, step = 0.001)), 0)

  p_entry = st.number_input("entry: ", value = None, min_value = 0.01, step = 0.01)
  if p_entry is None or p_entry < 0:
    p_entry = 0.01

  p_SL = st.number_input("SL: ", value = None, min_value = 0.00, step = 0.01)
  if p_SL is None or p_SL < 0:
    p_SL = 0.00

  return liq_delta_to_SL_delta_ratio, risk, maintainance_margin_rate, maintainance_deduction, p_entry, p_SL

def get_TP():
  p_TP = st.number_input("TP: ", value = None, step = 0.01)
  if p_TP is None or p_TP <= 0:
    p_TP = 0
  return p_TP

def current_direction_label(current_direction):
  if current_direction == "long":
    st.success("Long")
  elif current_direction == "short":
    st.error("Short")
  else:
    st.warning("Trade direction not consistent. Please check your input parameters.")

def fast_order_table(p_entry, p_SL, p_TP, p_liquidation, lvg, n_pos_value, initial_margin, maintainance_margin, rrr, rel_asset_gain_at_TP, potential_profit):
  with st.container(border=True):
  
  
  
        st.subheader("📊 Fast Order Table")
        
        # Wir nutzen Spalten für eine saubere Anordnung nebeneinander
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("lvg", f"{round(lvg, 0)} x")
        col2.metric("isolated margin", f"{round(initial_margin, 2)} $")
        col3.metric("p_liquidation", f"{round(p_liquidation, 2)} $")
        col4.metric("n_pos_value", f"{round(n_pos_value, 2)} $")
  
  st.divider() # Visuelle Trennlinie zwischen den Abschnitten

def overview_table(p_entry, p_SL, p_TP, p_liquidation, lvg, n_pos_value, initial_margin, maintainance_margin, rrr, rel_asset_gain_at_TP, potential_profit):
  #table1
  with st.container(border=True):

      st.subheader("📊 Overview")
      
      # Wir nutzen Spalten für eine saubere Anordnung nebeneinander
      col1, col2, col3, col4, col5 = st.columns(5)
      col1.metric("SL Delta", f"{round(SL_delta, 2)} $")
      col2.metric("Risk", f"{round(risk, 2)} $")
      col3.metric("Relative Risk", f"{round(rel_risk, 2)} $")
      col4.metric("Initial Margin", f"{round(initial_margin, 2)} $")
      col5.metric("potential_profit", f"{round(potential_profit, 2)} $")

  st.divider() # Visuelle Trennlinie zwischen den Abschnitten

  #table2:
  with st.container(border=True):
      st.subheader("💰 Risk Feedback")
      
      col1, col2, col3, col4, col5 = st.columns(5)
      col1.metric("Risiko", f"{round(risk, 2)} €")
      col2.metric("rrr", f"{round(rrr, 1)}")
      col3.metric("relative Gain", f"{round(rel_asset_gain_at_TP * 100, 2)}%")
      col4.metric("Wartungsmarge", f"{round(maintainance_margin, 2)} €")
      col5.metric("rel asset gain at TP", f"{round(rel_asset_gain_at_TP * 100, 2)}%")

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
risk, maintainance_margin_rate, maintainance_deduction, p_entry, p_SL = get_trade_parameters()
p_TP = get_TP()
SL_delta, rel_risk, current_direction, p_liquidation, lvg, initial_margin, n_pos_value, maintainance_margin, rel_maintainance_margin, rel_asset_gain_at_TP, rrr, potential_profit = calculate_all(liq_delta_to_SL_delta_ratio, risk, maintainance_margin_rate, Maintainance_deduction, p_entry, p_SL)
current_direction_label(current_direction)

fast_order_table(p_entry, p_SL, p_TP, p_liquidation, lvg, n_pos_value, initial_margin, maintainance_margin, rrr, rel_asset_gain_at_TP, potential_profit)
visualize_trade(p_entry, p_TP, p_SL, current_direction, p_liquidation)
overview_table(p_entry, p_SL, p_TP, p_liquidation, lvg, n_pos_value, initial_margin, maintainance_margin, rrr, rel_asset_gain_at_TP, potential_profit)