# -*- coding: utf-8 -*-
import streamlit as st
import altair as alt

import pandas as pd

#logic functions
from classes import Trade, Trade_Parameters, Tranche, Tranche_Parameters, Take_Profit_Target, Entry_Level
from trading_logic import calculate_buffered_tp1_close_percent

st.title("Too_Risky - Crypto live lvg and liquidation manager")
st.text("Optimized for execution speed.")

#trade specific values

def init_session_state():
    #trade parameters inputs init:
    #uses trade_defaults of classes.py class
    if "input_trade" not in st.session_state:
        st.session_state.input_trade = Trade()

    if "key" not in st.session_state:
            st.session_state["key"] = 0
    #generiert fehler bei variablen mit min_value > 0, oder?

def get_trade_object_inputs():
    #Collect Trade Inputs in streamlit session state
    update_input_keys()
    
    get_trade_parameters()
    render_ladders()

    #send session state to object
    return get_trade_object_from_session_state()

#Start Info
def intro():
    st.title("Too_Risky - Crypto live lvg and liquidation manager")
    st.text("Opimized for execution speed.")

#last list element (hence tp/entry) will be popped, as is intuitiv
def add_tranche():
    trade = st.session_state.input_trade
    trade.tranches.append(Tranche())
    #tranche bound entry und TP created by tranche appendix as well

def remove_tranche():
    if len(st.session_state.trade.tranches) > 1:
        trade = st.session_state.input_trade
        trade.tranches.pop()
        #tranche bound entry and tp get popped with the tranche pop as well

def add_global_tp_target():
    trade = st.session_state.input_trade
    trade.global_tp_targets.append(Take_Profit_Target())

def remove_global_tp_target():
    if len(st.session_state.global_tp_targets) > 1:
        trade = st.session_state.input_trade
        trade.global_tp_targets.pop()


def update_input_keys(trade: Trade):
    # Update session state keys for trade parameters
    t = trade.trade_parameters
    for key, attr in [
        ("input_liq_delta_to_SL_delta_ratio", t.liq_delta_to_SL_delta_ratio),
        ("input_maintainance_margin_rate", t.maintainance_margin_rate),
        ("input_maintainance_deduction", t.maintainance_deduction),
        ("input_total_max_lvg", t.total_max_lvg),
        ("input_total_max_margin", t.total_max_margin),
        ("input_trailing_sl_percent", t.trailing_SL_percent),
        ("input_pull_SL", t.pull_SL),
    ]:
        st.session_state[key] = attr

def get_trade_parameters(): #forces Object of Type Trade_Parameters as Output
    with st.container(border=True):
        st.subheader("🎯 General Params")
        with st.expander("Main Inputs"):
            #rendering and assigning keys, giving inputs to trade_parameters
            #if else in input guarantees value >= min_value

            #input fields can be overwritten by calculate_all() results
            for key, attr in [
                ("input_liq_delta_to_SL_delta_ratio", t.liq_delta_to_SL_delta_ratio),
                ("input_maintainance_margin_rate", t.maintainance_margin_rate),
                ("input_maintainance_deduction", t.maintainance_deduction),
                ("input_total_max_lvg", t.total_max_lvg),
                ("input_total_max_margin", t.total_max_margin),
                ("input_trailing_sl_percent", t.trailing_sl_percent),
                ("input_pull_SL", t.pull_SL),
            ]:
            st.session_state[key] = attr
           
            st.number_input(
                "liq_delta_to_SL_delta_ratio: ", 
                min_value = 0.0, step = 0.25, 
                key = "input_liq_delta_to_SL_delta_ratio")

            st.number_input(
                "maintainance_margin_rate", 
                min_value = 0.0, 
                step = 0.001, 
                key = "input_maintainance_margin_rate")

            st.number_input(
                "maintainance_deduction: ", 
                min_value = 0.0, 
                step = 0.001, 
                key = "input_maintainance_deduction")

            st.number_input(
                "total_max_lvg", 
                key = "input_total_max_lvg")

            st.number_input(
                "total_max_margin: ", 
                min_value = 0.0, 
                step = 0.1, 
                key ="input_total_max_margin")

            st.number_input(
                "Trailing SL (%):",
                min_value=0.0,
                step=0.1,
                key="input_trailing_SL_percent",
            )

            st.number_input(
                "Pull SL Preis:",
                min_value = 0.0,
                step = 0.01,
                key = "input_pull_SL",
            )
            
            st.number_input(
                "Aktueller Asset-Preis:",
                min_value=0.0,
                step=0.01,
                key="input_current_asset_price",
            )

            order_type = st.selectbox(
                "Order Type:",
                options = session_state.order_type,
                key="input_order_type",
            )

            st.number_input(
                "Buffer SL Preis:",
                min_value = 0.0,
                step = 0.01,
                key = "input_buffer_SL",
            )

            st.number_input(
                "Aktueller SL Preis:",
                min_value = 0.0,
                step = 0.01,
                key = "input_current_sl_price",
            )

    with st.container(border=True):
            st.subheader("🎯 Fast Order")
            with st.expander("Fast Inputs"):
                st.number_input(
                    "total risk: ",
                    min_value = 0.0, 
                    step = 1.0, 
                    key = "input_total_risk")
                st.number_input(
                    "SL: ", 
                    min_value = 0.0, 
                    step = 0.01, 
                    key = "input_p_SL")


def current_direction_label(current_direction):
  
  if current_direction == "long":
    st.success("Long")
  elif current_direction == "short":
    st.error("Short")
  else:
    st.warning("Trade direction not consistent. Please check your input parameters.")


def update_tp_targets_triggered(trade: Trade):
    if not trade.tranches[0].tranche_parameters.current_direction:
        return trade
    
    for tranche in trade.tranches:
        if tranche.tranche_parameters.current_direction == "long":
            tranche.tp_target.triggered = trade.trade_parameters.current_asset_price >= trade.trade_parameters.current_asset_price    #boolish equation
        elif tranche.tranche_parameters.current_direction == "short":
            tranche.tp_target.triggered = trade.trade_parameters.current_asset_price <= trade.trade_parameters.current_asset_price
    return trade


def fast_order_table(trade: Trade):
    tranche1 = trade.tranches[0]
    with st.container(border=True):
        st.subheader("📊 Fast Order Table")
        # Wir nutzen Spalten für eine saubere Anordnung nebeneinander
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("lvg", f"{tranche1.tranche_parameters.lvg} x")
        col2.metric("isolated margin", f"{round(tranche1.tranche_parameters.isolated_margin, 2)} $")
        col3.metric("p_liquidation", f"{round(tranche1.tranche_parameters.p_liquidation, 2)} $")
        col4.metric("n_pos_value", f"{round(tranche1.tranche_parameters.n_pos_value, 2)} $")

    st.divider() # Visuelle Trennlinie zwischen den Abschnitten

def render_ladders(trade):
    
    with st.container(border=True):
        st.subheader("🎯 Entries")
        #entries
        updated_trade = render_ladder(trade, "Entries")

        st.subheader("🎯 TPs")
        
        updated_trade.trade_parameters.tp_mode = st.radio(
            "Choose TP mode:",
            options = ["global_TPs", "tranche_bound_TPs"],
            key = "TP_radio"
        )
        #TP-Ladder mode
        mode = updated_trade.trade_parameters.tp_mode
        if mode == "global_TPs":
            updated_trade = render_ladder(updated_trade, "global_TPs")
        elif mode == "tranche_bound_TPs":
            updated_trade = render_ladder(updated_trade, "tranche_bound_TPs")

    return updated_trade

def render_ladder(trade, mode): #modes: Entries, tranche_bound_TPs, global_TPs
    with st.expander(f"Ladder {mode}"):
        #Managing ladder size for each mode
        entry_col1, entry_col2 = st.columns(2)
        with entry_col1:
            if st.button(f"Weitere {mode} hinzufügen", key= f"add_{mode}_button"):   
                if mode == "Entries" or "tranche_bound_TPs":
                    add_tranche()
                elif mode == "global TPs":
                    add_global_tp_target()

        with entry_col2:
            if st.button(f"{mode} entfernen", key = f"remove_{mode}_button"):
                if mode == "global_TPs":
                    remove_global_tp_target()
                elif mode == "Entries" or "tranche_bound_TPs":
                    remove_tranche()
        
        #buildung input fields for each mode
        if mode == "Entries" or "tranche_bound_TPs":
            for index, tranche in enumerate(trade.tranches):
                if mode == "Entries":
                    price_key = f"input_entry_price_{index}"
                    share_key = f"input_position_share_{index}"
                    
                    # 1. Sicherstellen, dass der Wert existiert und min. den min_value (0.01) hat
                    if price_key not in st.session_state or st.session_state[price_key] < 0.01:
                        st.session_state[price_key] = max(0.01, float(tranche.entry_level.price))
                        
                    if share_key not in st.session_state or st.session_state[share_key] < 0.01:
                        st.session_state[share_key] = max(0.01, float(tranche.entry_level.position_share))

                    # 2. Widgets über den Key steuern
                    tranche.entry_level.price = st.number_input(
                        f"Tranche {index + 1} Entry Preis:",
                        min_value=0.01,
                        step=0.01,
                        key=price_key
                    )
                    
                    tranche.entry_level.position_share = st.number_input(
                        f"Tranche {index + 1} Share:",
                        min_value=0.01,
                        step=0.01,
                        key=share_key
                    )
                
                    # 3. Direkt in die Tranche-Objekte zurückschreiben (Punktschreibweise)
                    tranche.entry_level.price = st.session_state[price_key]
                    tranche.entry_level.position_share = st.session_state[share_key]

                elif mode == "tranche_bound_TPs":
                    tp_price_key = f"tp_price_{index}"
                    tp_percent_key = f"tp_close_percent_{index}"

                    tranche.tp_target.price = st.number_input(
                        f"TP {index + 1} Preis:",
                        min_value=0.01,
                        step = 0.01,
                        key = tp_price_key
                    )
        
                    tranche.tp_target.close_percent = st.number_input(
                        f"TP {index + 1} Schließung (%):",
                        min_value=0.0,
                        max_value=100.0,
                        step = 1.0,
                        key = tp_percent_key
                    )

                    #useless:
                    #tranche.tp_target.price = st.session_state[tp_price_key]
                    #tranche.tp_target.close_percent = st.session_state[tp_percent_key]
            
            #visualize:
            st.markdown(f"**{mode} Levels:**")
            for tranche in trade.tranches:
                if mode == "Entries":
                    st.write(f"- entering with {tranche.entry_level.position_share}% of the full position size at {tranche.entry_level.price}$.")
                elif mode == "TPs":
                    st.write(f"Closing {tranche.tp_target.close_percent}% of the position at {tranche.tp_target.price}$.")


        elif mode == "global_TPs":
            for index, tp in enumerate(trade.global_tp_targets):
                global_price_key = f"input_global_entry_price_{index}"
                global_share_key = f"input_global_position_share_{index}"
                
                # 1. Sicherstellen, dass der Wert existiert und min. den min_value (0.01) hat
                if price_key not in st.session_state or st.session_state[global_price_key] < 0.01:
                    st.session_state[global_price_key] = max(0.01, float(tranche.entry_level.price))
                    
                if share_key not in st.session_state or st.session_state[global_share_key] < 0.01:
                    st.session_state[global_share_key] = max(0.01, float(tranche.entry_level.position_share))

                # 2. Widgets über den Key steuern
                tp.price = st.number_input(
                    f" {index + 1}. TP target:",
                    min_value = 0.01,
                    step = 0.01,
                    key = global_price_key
                )
                
                tp.close_percent = st.number_input(
                    f"TP{index + 1} Share:",
                    min_value = 0.01,
                    step = 0.01,
                    key = global_share_key
                )
            
                # now useless: 3. Direkt in die Tranche-Objekte zurückschreiben (Punktschreibweise)
                #tp.price = st.session_state[global_price_key]
                #tp.close_percent = st.session_state[global_share_key]
                        
            #visualize:
            st.markdown(f"**{mode} Levels:**")
            for tp in trade.global_tp_targets:
                    st.write(f"Closing {tp.position_share}% of the full position size at {tp.price}$.")

            
    return trade

def get_trade_object_from_session_state():
    #st.session_state is global object
    return st.session_state.get("input_trade")

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

  if tranche1.tp_target:
      with st.container(border=True):
          st.subheader("🎯 TP-Status")
          for tranche in trade.tranches:
              status = "✅ Erreicht" if tranche.tp_target.triggered else "- offen"
              st.write(f"- TP bei {tranche.tp_target.price} | {tranche.tp_target.close_percent}% Schließung | {status}")

  st.divider()


def visualize_trade(trade: Trade):
    tranche1 = trade.tranches[0]
    st.title("Trade Visualizer")
    st.write(f"Direction: {tranche1.tranche_parameters.current_direction.capitalize()}" if tranche1.tranche_parameters.current_direction else "Direction unknown")

    # --- 2. DIE LOGIK & DER BALKEN (Nutzt einfach die Variablen von oben) ---
    try:
        balken_unten = 0.0

        #ba top
        if tranche1.tp_target.price > 0:  # hence, tp exists
            if tranche1.tranche_parameters.dirsign > 0:  # long case
                balken_oben = tranche1.tp_target.price if tranche1.tranche_parameters.tp_active else tranche1.entry_level.price
            elif tranche1.tranche_parameters.dirsign < 0:  # short case
                balken_oben = tranche1.tp_target.price if tranche1.tranche_parameters.tp_active else tranche1.entry_level.price
            else:
                balken_oben = tranche1.tranche_parameters.p_liquidation
        else:
            balken_oben = max(tranche1.entry_level.price, tranche1.tranche_parameters.p_liquidation)  # covers short and long case

        # Daten fürs Chart zusammenbauen
        zone_data = pd.DataFrame({
            'y_min': [balken_unten],
            'y_max': [balken_oben],
            'Zone': ['Preisbereich']
        })

        preise = [tranche1.entry_level.price, tranche1.tranche_parameters.p_SL, tranche1.tranche_parameters.p_liquidation]
        labels = ['Entry', 'Stop Loss', 'Liquidation']
        typen = ['entry', 'sl', 'liq']

        if tranche1.tranche_parameters.tp_active:
            preise.append(tranche1.tp_target.price)
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
