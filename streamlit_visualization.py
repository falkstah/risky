# -*- coding: utf-8 -*-
import streamlit as st
import altair as alt

import pandas as pd

#logic functions
from classes import Trade, TradeParameters, Tranche, Tranche_Parameters, TakeProfitTarget, EntryLevel
from trading_logic import calculate_buffered_tp1_close_percent

st.title("Too_Risky - Crypto live lvg and liquidation manager")
st.text("Optimized for execution speed.")

#trade specific values

def init_trade_inputs():
    if "entry_levels" not in st.session_state:
        st.session_state.entry_levels = [{"price": 0.0, "margin_percent": 0.0}]
    if "tp_targets" not in st.session_state:
        st.session_state.tp_targets = [{"price": 0.0, "close_percent": 0.0}]
    if "trailing_SL_percent" not in st.session_state:
        st.session_state.trailing_SL_percent = 0.0
    if "current_price" not in st.session_state:
        st.session_state.current_price = 0.0
    if "buffer_SL" not in st.session_state:
        st.session_state.buffer_SL = 0.0
    if "buffer_SL_close_pct" not in st.session_state:
        st.session_state.buffer_SL_close_pct = 0.0
    if "pull_SL" not in st.session_state:
        st.session_state.pull_SL = 0.0
    if "order_type" not in st.session_state:
        st.session_state.order_type = "single limit"


def add_entry_target():
    st.session_state.entry_levels.append({"price": 0.0, "margin_percent": 0.0})


def remove_entry_target():
    if len(st.session_state.entry_levels) > 1:
        st.session_state.entry_levels.pop()


def add_tp_target():
    st.session_state.tp_targets.append({"price": 0.0, "close_percent": 50.0})


def remove_tp_target():
    if len(st.session_state.tp_targets) > 1:
        st.session_state.tp_targets.pop()


def get_trade_parameters():
    print("Enter parameters: ")
    init_trade_inputs()

    trade_parameters = TradeParameters(
        liq_delta_to_SL_delta_ratio=float(st.number_input("liq_delta_to_SL_delta_ratio: ", value = 4.00, min_value = 1.50, step = 0.25)),
        total_risk=float(st.number_input("risk: ", value = 10, min_value = 0, step = 1)),
        maintainance_margin_rate=float(st.number_input("maintainance_margin_rate: ", value = 0.02, min_value = 0.0, step = 0.001)),
        maintainance_deduction=float(st.number_input("maintainance_deduction: ", value = 0.0, min_value = 0.0, step = 0.001)),
        total_max_lvg =float(st.number_input("max_leverage: ", value = 10.0, min_value = 1.0, step = 0.5)),
        total_max_margin =float(st.number_input("max_margin: ", value = 100.0, min_value = 1.0, step = 1.0)),
        p_SL=get_SL()
    )

    return trade_parameters

def get_SL():
  p_SL = st.number_input("SL: ", value=0.0, min_value=0.0, step=0.01)
  if p_SL is None or p_SL < 0:
    p_SL = 0.0
  return float(p_SL)

def current_direction_label(current_direction):
  if current_direction == "long":
    st.success("Long")
  elif current_direction == "short":
    st.error("Short")
  else:
    st.warning("Trade direction not consistent. Please check your input parameters.")


def update_tp_targets_triggered(trade: Trade):
    if not trade.tranches.tranche_parameters.current_direction:
        return trade

    for target in trade.tp_targets:
        if trade.parameters.current_direction == "long":
            target.triggered = trade.current_asset_price >= target.price
        elif trade.parameters.current_direction == "short":
            target.triggered = trade.current_asset_price <= target.price
    return trade


def fast_order_table(trade: Trade):
    params = trade.trade_parameters
    with st.container(border=True):
        st.subheader("📊 Fast Order Table")
        # Wir nutzen Spalten für eine saubere Anordnung nebeneinander
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("lvg", f"{tranche.tranche_parameters.lvg} x")
        col2.metric("isolated margin", f"{round(tranche.tranche_parameters.isolated_margin, 2)} $")
        col3.metric("p_liquidation", f"{round(tranche.tranche_parameters.p_liquidation, 2)} $")
        col4.metric("n_pos_value", f"{round(tranche.tranche_parameters.n_pos_value, 2)} $")

    st.divider() # Visuelle Trennlinie zwischen den Abschnitten


def render_trade_controls(trade: Trade):
    init_trade_inputs()

    #Initializing input lists in st:
    if "entry_levels" not in st.session_state:
            st.session_state.entry_levels = [{"price": 0.01, "position_share": 100.0}]
    if "tp_targets" not in st.session_state:
            st.session_state.tp_targets = [{"price": 0.01, "close_percent": 50.0, "triggered": False}]

    with st.container(border=True):
        st.subheader("🎯 Trade Ziele & Trailing SL")

        entry_col1, entry_col2 = st.columns(2)
        with entry_col1:
            if st.button("Weitere Entry hinzufügen", key="add_entry_button"):
                add_entry_target()
        with entry_col2:
            if st.button("Entry entfernen", key="remove_entry_button"):
                remove_entry_target()

        tp_col1, tp_col2 = st.columns(2)
        with tp_col1:
            if st.button("Weitere TP hinzufügen", key="add_tp_button"):
                add_tp_target()
        with tp_col2:
            if st.button("TP entfernen", key="remove_tp_button"):
                remove_tp_target()

  
        for index, target in enumerate(st.session_state.entry_levels):
            price_key = f"entry_price_{index}"
            share_key = f"position_share_{index}"
            
            # 1. Wert im Session State initialisieren, falls noch nicht geschehen
            if price_key not in st.session_state:
                st.session_state[price_key] = float(target["price"])
            if share_key not in st.session_state:
                st.session_state[share_key] = float(target["position_share"])

            # 1. Sicherstellen, dass der Wert existiert und mind. den min_value (0.01) hat
            if price_key not in st.session_state or st.session_state[price_key] < 0.01:
                st.session_state[price_key] = max(0.01, float(target["price"]))
                
            if share_key not in st.session_state or st.session_state[share_key] < 0.01:
                st.session_state[share_key] = max(0.01, float(target["position_share"]))

            # 2. Widgets rein über den Key steuern (ohne value-Parameter)
            st.session_state[price_key] = st.number_input(
                f"Entry Level {index + 1} Preis:",
                min_value=0.01,
                step=0.01,
                key=price_key
            )
            
            st.session_state[share_key] = st.number_input(
                f"Entry Level {index + 1} Share:",
                min_value=0.01,
                step=0.01,
                key=share_key
            )
            
            # 3. Direkt in das Target-Dictionary zurückschreiben
            target["price"] = st.session_state[price_key]
            target["position_share"] = st.session_state[share_key]


        tp_targets: list[TakeProfitTarget] = []
        for index, target in enumerate(st.session_state.tp_targets):
            price_key = f"tp_price_{index}"
            pct_key = f"_close_percent_{index}"
            price = st.number_input(
                f"TP {index + 1} Preis:",
                value=target["price"],
                min_value=0.01,
                step=0.01,
                key=price_key,
            )

            close_percent = st.number_input(
                f"TP {index + 1} Schließung (%):",
                value=target["close_percent"],
                min_value=0.0,
                max_value=100.0,
                step=1.0,
                key=pct_key,
            )
            st.session_state.tp_targets[index] = {"price": price, "close_percent": close_percent}
            tp_targets.append(TakeProfitTarget(price=price, close_percent= close_percent))

        trailing_SL_percent = st.number_input(
            "Trailing SL (%):",
            value=st.session_state.trailing_SL_percent,
            min_value=0.0,
            step=0.1,
            key="input_trailing_SL_percent",
        )
        st.session_state.trailing_SL_percent = float(trailing_SL_percent)
        pull_SL = st.number_input(
            "Pull SL Preis:",
            value=st.session_state.pull_SL,
            min_value=0.0,
            step=0.01,
            key="input_pull_SL",
        )
        st.session_state.pull_SL = float(pull_SL)
        current_price = st.number_input(
            "Aktueller Asset-Preis:",
            value=st.session_state.current_price,
            min_value=0.0,
            step=0.01,
            key="input_current_price",
        )
        st.session_state.current_price = float(current_price)
        order_type = st.selectbox(
            "Order Type:",
            ["single limit", "single market", "single post only", "k1m6a box"],
            index=["single limit", "single market", "single post only", "k1m6a box"].index(st.session_state.order_type),
            key="input_order_type",
        )
        buffer_SL = st.number_input(
            "Buffer SL Preis:",
            value=st.session_state.buffer_SL,
            min_value=0.0,
            step=0.01,
            key="input_buffer_SL",
        )
        st.session_state.buffer_SL = float(buffer_SL)
        current_sl_price = st.number_input(
            "Aktueller SL Preis:",
            value=trade.trade_parameters.p_SL,
            min_value=0.0,
            step=0.01,
            key="input_current_sl_price",
        )

        if st.button("Calculate TP1 close_perecnt for buffer_SL", key="calc_buffer_tp1"):
            try:
                st.session_state.buffer_SL_close_pct = trade.tranches[0].tp_target.close_percent
            except Exception as exc:
                st.error(f"Berechnung fehlgeschlagen: {exc}")

        trade.tranches.entry_levels = st.session_state.entry_levels
        trade.tranches.tp_targets = tp_targets
        trade.trade_parameters.current_asset_price = st.session_state.current_asset_price
        trade.trade_parameters.buffer_SL = st.session_state.buffer_SL
        trade.trade_parameters.pull_SL = st.session_state.pull_SL
        trade.trade_parameters.order_type = st.session_state.order_type
        trade.trade_parameters.trailing_SL_percent = st.session_state.trailing_SL_percent
        trade.trade_parameters.trailing_sl_enabled = st.session_state.trailing_SL_percent > 0.0
        trade.trade_parameters.current_sl_price = float(current_sl_price)

        if st.session_state.buffer_SL_close_pct:
            st.info(f"Empfohlener TP1 Close: {round(st.session_state.buffer_SL_close_pct, 2)} %")

        trade = update_tp_targets_triggered(trade)

        if trade.tranches.entry_levels:
            st.markdown("**Entry Levels:**")
            for target in trade.tranches.entry_levels:
                st.write(f"- Entry Level bei {target.price} mit {target.position_share}% Margin")

        if tp_targets:
            st.markdown("**Aktuelle TP Targets:**")
            for target in tp_targets:
                tp_profit = 0.0
                if target.price and trade.trade_parameters.n_pos_value:
                    profit = (trade.tranches[0].dirsign * (target.price - target.price) / target.price) * abs(trade.tranches[0].tranche_parameters.n_pos_value)
                    tp_profit = target.close_percent / 100.0 * profit
                status = "✅ Erreicht" if target.triggered else "– offen"
                st.write(f"- TP bei {target.price} mit {target.close_percent}% Schließung ({status})")
                st.caption(f"Partial profit: ${round(tp_profit, 2)}")

        if trade.trade_parameters.trailing_sl_enabled:
            st.info(f"Trailing SL ist aktiviert: {trade.trade_parameters.trailing_SL_percent}%")

    return trade


def overview_table(trade: Trade):
  tranche1 = trade.tranches[0]
  #table1, currently for tranche 1
  with st.container(border=True):

      st.subheader("📊 Overview")
      
      # Wir nutzen Spalten für eine saubere Anordnung nebeneinander
      col1, col2, col3, col4, col5 = st.columns(5)
      col1.metric("SL Delta", f"{round(tranche1.tranche_parameters.sl_delta, 2)} $")
      col2.metric("Risk", f"{round(tranche1.tranche_parameters.risk, 2)} $")
      col3.metric("Relative Risk", f"{round(tranche1.tranche_parameters.rel_risk, 2)} $")
      col4.metric("Initial Margin", f"{round(tranche1.tranche_parameters.initial_margin, 2)} $")
      col5.metric("potential_profit", f"{round(tranche1.tranche_parameters.potential_profit, 2)} $")

  st.divider() # Visuelle Trennlinie zwischen den Abschnitten

  #table2:
  with st.container(border=True):
      st.subheader("💰 Risk Feedback")
      
      col1, col2, col3, col4, col5 = st.columns(5)
      col1.metric("Risiko", f"{round(tranche1.tranche_parameters.risk, 2)} €")
      col2.metric("rrr", f"{round(tranche1.tranche_parameters.rrr, 1)}")
      col3.metric("relative Gain", f"{round(tranche1.tranche_parameters.rel_asset_gain_at_TP * 100, 2)}%")
      col4.metric("Wartungsmarge", f"{round(tranche1.tranche_parameters.maintainance_margin, 2)} €")
      col5.metric("rel asset gain at TP", f"{round(tranche1.tranche_parameters.rel_asset_gain_at_TP * 100, 2)}%")

  if trade.tranche1.tp_target:
      with st.container(border=True):
          st.subheader("🎯 TP-Status")
          for target in trade.tranche1.tp_targets:
              status = "✅ Erreicht" if target.triggered else "– offen"
              st.write(f"- TP bei {target.price} | {target.close_percent}% Schließung | {status}")

  st.divider()


def visualize_trade(trade: Trade):
  tranche.tranche_parameters = trade.parameters
  st.title("Trade Visualizer")
  st.write(f"Direction: {tranche.tranche_parameters.current_direction.capitalize()}" if tranche.tranche_parameters.current_direction else "Direction unknown")

  # --- 2. DIE LOGIK & DER BALKEN (Nutzt einfach die Variablen von oben) ---
  try:
    balken_unten = 0.0

    #ba top
    if trade.tp_targets[0].price > 0:  # hence, tp exists
      if tranche.tranche_parameters.dirsign > 0:  # long case
        balken_oben = trade.tp_targets[0].price if tranche.tranche_parameters.tp_active else trade.entry_levels[0].price
      elif tranche.tranche_parameters.dirsign < 0:  # short case
        balken_oben = trade.tp_targets[0].price if tranche.tranche_parameters.tp_active else trade.entry_levels[0].price
      else:
        balken_oben = tranche.tranche_parameters.p_liquidation
    else:
        balken_oben = max(trade.entry_levels[0].price, tranche.tranche_parameters.p_liquidation)  # covers short and long case

    # Daten fürs Chart zusammenbauen
    zone_data = pd.DataFrame({
        'y_min': [balken_unten],
        'y_max': [balken_oben],
        'Zone': ['Preisbereich']
    })

    preise = [trade.entry_levels[0].price, tranche.tranche_parameters.p_SL, tranche.tranche_parameters.p_liquidation]
    labels = ['Entry', 'Stop Loss', 'Liquidation']
    typen = ['entry', 'sl', 'liq']

    if tranche.tranche_parameters.tp_active:
        preise.append(trade.tp_targets[0].price)
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

    chart = alt.layer(area, rule, text).properties(height=500, width=200)

    # In Streamlit anzeigen
    st.altair_chart(chart, use_container_width=True)
  except Exception as exc:
    st.warning(f"Error in visualizing trade: {exc}")
