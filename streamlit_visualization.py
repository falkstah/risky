# -*- coding: utf-8 -*-
import streamlit as st
import altair as alt

import pandas as pd

#logic functions
from classes import TradeParameters, Trade, TakeProfitTarget

st.title("Too_Risky - Crypto live lvg and liquidation manager")
st.text("Optimized for execution speed.")

#trade specific values

def init_trade_inputs():
    if "tp_targets" not in st.session_state:
        st.session_state.tp_targets = [{"price": 0.0, "close_percent": 0.0}]
    if "trailing_SL_percent" not in st.session_state:
        st.session_state.trailing_SL_percent = 0.0
    if "current_price" not in st.session_state:
        st.session_state.current_price = 0.0


def add_tp_target():
    st.session_state.tp_targets.append({"price": 0.0, "close_percent": 0.0})


def get_trade_parameters():
    print("Enter parameters: ")
    init_trade_inputs()

    params = TradeParameters(
        liq_delta_to_SL_delta_ratio=float(st.number_input("liq_delta_to_SL_delta_ratio: ", value = 4.00, min_value = 1.50, step = 0.25)),
        risk=float(st.number_input("risk: ", value = 10, min_value = 0, step = 1)),
        maintainance_margin_rate=float(st.number_input("maintainance_margin_rate: ", value = 0.02, min_value = 0.0, step = 0.001)),
        maintainance_deduction=float(st.number_input("maintainance_deduction: ", value = 0.0, min_value = 0.0, step = 0.001)),
        max_lvg=float(st.number_input("max_leverage: ", value = 10.0, min_value = 1.0, step = 0.5)),
        max_margin=float(st.number_input("max_margin: ", value = 100.0, min_value = 1.0, step = 1.0)),
        p_entry=get_entry(),
        p_SL=get_SL(),
        p_TP=get_TP()
    )

    return params

def get_entry():
  p_entry = st.number_input("entry: ", value=0.01, min_value=0.0, step=0.01) #nicht params-p_entry, weil die Zuordnung in get_trade_parameters() erfolgt
  if p_entry is None or p_entry <= 0:
    p_entry = 0.01
  return float(p_entry)


def get_SL():
  p_SL = st.number_input("SL: ", value=0.0, min_value=0.0, step=0.01)
  if p_SL is None or p_SL < 0:
    p_SL = 0.0
  return float(p_SL)


def get_TP():
  p_TP = st.number_input("TP: ", value=0.0, min_value=0.0, step=0.01)
  if p_TP is None or p_TP <= 0:
    p_TP = 0.0
  return float(p_TP)

def current_direction_label(current_direction):
  if current_direction == "long":
    st.success("Long")
  elif current_direction == "short":
    st.error("Short")
  else:
    st.warning("Trade direction not consistent. Please check your input parameters.")


def update_tp_targets_triggered(trade: Trade):
    if not trade.parameters.current_direction:
        return trade

    for target in trade.tp_targets:
        if trade.parameters.current_direction == "long":
            target.triggered = trade.current_price >= target.price
        elif trade.parameters.current_direction == "short":
            target.triggered = trade.current_price <= target.price
    return trade


def fast_order_table(trade: Trade):
    params = trade.parameters
    with st.container(border=True):
        st.subheader("📊 Fast Order Table")
        # Wir nutzen Spalten für eine saubere Anordnung nebeneinander
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("lvg", f"{params.lvg} x")
        col2.metric("isolated margin", f"{round(params.isolated_margin, 2)} $")
        col3.metric("p_liquidation", f"{round(params.p_liquidation, 2)} $")
        col4.metric("n_pos_value", f"{round(params.n_pos_value, 2)} $")

    st.divider() # Visuelle Trennlinie zwischen den Abschnitten


def render_trade_controls(trade: Trade):
    init_trade_inputs()

    with st.container(border=True):
        st.subheader("🎯 Trade Ziele & Trailing SL")

        if st.button("Weitere TP hinzufügen", key="add_tp_button"):
            add_tp_target()

        tp_targets: list[TakeProfitTarget] = []
        for index, target in enumerate(st.session_state.tp_targets):
            price_key = f"tp_price_{index}"
            pct_key = f"tp_close_pct_{index}"
            price = st.number_input(
                f"TP {index + 1} Preis:",
                value=target["price"],
                min_value=0.0,
                step=0.01,
                key=price_key,
            )
            close_pct = st.number_input(
                f"TP {index + 1} Schließung (%):",
                value=target["close_percent"],
                min_value=0.0,
                max_value=100.0,
                step=1.0,
                key=pct_key,
            )
            st.session_state.tp_targets[index] = {"price": price, "close_percent": close_pct}
            tp_targets.append(TakeProfitTarget(price=price, close_percent=close_pct))

        trailing_SL_percent = st.number_input(
            "Trailing SL (%):",
            value=st.session_state.trailing_SL_percent,
            min_value=0.0,
            step=0.1,
            key="trailing_SL_percent",
        )
        st.session_state.trailing_SL_percent = float(trailing_SL_percent)
        current_price = st.number_input(
            "Aktueller Asset-Preis:",
            value=st.session_state.current_price,
            min_value=0.0,
            step=0.01,
            key="current_price",
        )
        st.session_state.current_price = float(current_price)
        current_sl_price = st.number_input(
            "Aktueller SL Preis:",
            value=trade.parameters.p_SL,
            min_value=0.0,
            step=0.01,
            key="current_sl_price",
        )

        trade.tp_targets = tp_targets
        trade.current_price = st.session_state.current_price
        trade.current_price = st.session_state.current_price
        trade.trailing_SL_percent = st.session_state.trailing_SL_percent
        trade.trailing_sl_enabled = st.session_state.trailing_SL_percent > 0.0
        trade.current_sl_price = float(current_sl_price)

        trade = update_tp_targets_triggered(trade)

        if tp_targets:
            st.markdown("**Aktuelle TP Targets:**")
            for target in tp_targets:
                status = "✅ Erreicht" if target.triggered else "– offen"
                st.write(f"- TP bei {target.price} mit {target.close_percent}% Schließung ({status})")

        if trade.trailing_sl_enabled:
            st.info(f"Trailing SL ist aktiviert: {trade.trailing_SL_percent}%")

    return trade


def overview_table(trade: Trade):
  params = trade.parameters
  #table1
  with st.container(border=True):

      st.subheader("📊 Overview")
      
      # Wir nutzen Spalten für eine saubere Anordnung nebeneinander
      col1, col2, col3, col4, col5 = st.columns(5)
      col1.metric("SL Delta", f"{round(params.sl_delta, 2)} $")
      col2.metric("Risk", f"{round(params.risk, 2)} $")
      col3.metric("Relative Risk", f"{round(params.rel_risk, 2)} $")
      col4.metric("Initial Margin", f"{round(params.initial_margin, 2)} $")
      col5.metric("potential_profit", f"{round(params.potential_profit, 2)} $")

  st.divider() # Visuelle Trennlinie zwischen den Abschnitten

  #table2:
  with st.container(border=True):
      st.subheader("💰 Risk Feedback")
      
      col1, col2, col3, col4, col5 = st.columns(5)
      col1.metric("Risiko", f"{round(params.risk, 2)} €")
      col2.metric("rrr", f"{round(params.rrr, 1)}")
      col3.metric("relative Gain", f"{round(params.rel_asset_gain_at_TP * 100, 2)}%")
      col4.metric("Wartungsmarge", f"{round(params.maintainance_margin, 2)} €")
      col5.metric("rel asset gain at TP", f"{round(params.rel_asset_gain_at_TP * 100, 2)}%")

  if trade.tp_targets:
      with st.container(border=True):
          st.subheader("🎯 TP-Status")
          for target in trade.tp_targets:
              status = "✅ Erreicht" if target.triggered else "– offen"
              st.write(f"- TP bei {target.price} | {target.close_percent}% Schließung | {status}")

  st.divider()


def visualize_trade(trade: Trade):
  params = trade.parameters
  st.title("Trade Visualizer")
  st.write(f"Direction: {params.current_direction.capitalize()}" if params.current_direction else "Direction unknown")

  # --- 2. DIE LOGIK & DER BALKEN (Nutzt einfach die Variablen von oben) ---
  try:
    balken_unten = 0.0

    #ba top
    if params.p_TP > 0:  # hence, tp exists
      if params.dirsign > 0:  # long case
        balken_oben = params.p_TP if params.tp_active else params.p_entry
      elif params.dirsign < 0:  # short case
        balken_oben = params.p_TP if params.tp_active else params.p_entry
      else:
        balken_oben = params.p_liquidation
    else:
        balken_oben = max(params.p_entry, params.p_liquidation)  # covers short and long case

    # Daten fürs Chart zusammenbauen
    zone_data = pd.DataFrame({
        'y_min': [balken_unten],
        'y_max': [balken_oben],
        'Zone': ['Preisbereich']
    })

    preise = [params.p_entry, params.p_SL, params.p_liquidation]
    labels = ['Entry', 'Stop Loss', 'Liquidation']
    typen = ['entry', 'sl', 'liq']

    if params.tp_active:
        preise.append(params.p_TP)
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
        color=alt.Color('Typ', scale={'domain': ['entry', 'sl', 'liq', 'tp'], 'range': ['#10b981', '#ef4444', '#8b5cf6', '#3b82f6']}, legend=None),
        tooltip=['Label', 'Preis']
    )
    text = rule.mark_text(align='left', dx=5, dy=-5).encode(text='Label')

    chart = alt.layer(area, rule, text).properties(height=500, width=200).interactive()

    # In Streamlit anzeigen
    st.altair_chart(chart, use_container_width=True)
  except Exception as exc:
    st.warning(f"Error in visualizing trade: {exc}")
