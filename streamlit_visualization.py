# -*- coding: utf-8 -*-
import streamlit as st
import altair as alt

import pandas as pd
from typing import get_args

#logic functions
from classes import Trade, Trade_Parameters, Tranche, Tranche_Parameters, Take_Profit_Target, Entry_Level
from dataclasses import fields
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

    #for first run, we need to update the session state keys with the default values from the Trade object
    update_input_items()

def get_trade_inputs_from_ui():
    #Collect Trade Inputs in streamlit session state
    update_input_items()

    get_trade_parameters()
    render_ladder(st.session_state.input_trade, "Entries")
    #evtl. hier schon fast order table anzeigen

    render_ladder(st.session_state.input_trade, st.session_state.input_trade.trade_parameters.tp_mode) #tranche_bound_TPs or global_TPs

    #loads ui inputs into trade object, so that it can be used for calculations; is used when widgets are not set yet, otherwse callback
    load_ui_into_trade()
    #send session state to object

    return st.session_state.input_trade

#Start Info
def intro():
    st.title("Too_Risky - Crypto live lvg and liquidation manager")
    st.text("Opimized for execution speed.")

#last list element (hence tp/entry) will be popped, as is intuitiv
def add_tranche():
    st.session_state.input_trade.tranches.append(Tranche())
    #tranche bound entry und TP created by tranche appendix as well

def remove_tranche():
    if len(st.session_state.input_trade.tranches) > 1:
        st.session_state.input_trade.tranches.pop()
        #tranche bound entry and tp get popped with the tranche pop as well

def add_global_tp_target():
    st.session_state.input_trade.global_tp_targets.append(Take_Profit_Target())

def remove_global_tp_target():
    #removing even the last global tp is allowed, bc you don't have to set a tp immediately
    if len(st.session_state.input_trade.global_tp_targets) > 0:
        st.session_state.input_trade.global_tp_targets.pop()
    

def update_input_items():
    # Update session state keys for trade parameters
    t = st.session_state.input_trade.trade_parameters
    for key, attr in [
        ("input_liq_delta_to_SL_delta_ratio", t.liq_delta_to_SL_delta_ratio),
        ("input_maintainance_margin_rate", t.maintainance_margin_rate),
        ("input_maintainance_deduction", t.maintainance_deduction),
        ("input_total_max_lvg", t.total_max_lvg),
        ("input_total_max_margin", t.total_max_margin),
        ("input_trailing_sl_percent", t.trailing_SL_percent),
        ("input_pull_SL", t.pull_SL),

        ("input_order_type", t.order_type),
        ("input_buffer_SL", t.buffer_SL),
        ("input_current_sl_price", t.current_sl_price),
        ("input_current_asset_price", t.current_asset_price),
        ("input_total_risk", t.total_risk),
        ("input_p_SL", t.p_SL),

        #radio_inputs:
        ("input_tp_mode", t.tp_mode)
    ]:
        st.session_state[key] = attr

def get_trade_parameters(): #forces Object of Type Trade_Parameters as Output
    with st.container(border = True):
        st.subheader("🎯 General Params")
        with st.expander("Main Inputs"):
            #rendering and assigning keys, giving inputs to trade_parameters
           
            build_number_input("liq_delta_to_SL_delta_ratio: ", step = 0.25)
            #guard clause:
            if st.session_state.input_trade.trade_parameters.liq_delta_to_SL_delta_ratio < 1.5:
                st.warning("⚠️ Warning: liq_delta_to_SL_delta_ratio should be >= 1.5 for safe trading.")
                st.stop()

            build_number_input("maintainance_margin_rate", step = 0.001)
            build_number_input("maintainance_deduction: ", step = 0.001)
            build_number_input("total_max_lvg:")
            #guard clause:
            if st.session_state.input_trade.trade_parameters.total_max_lvg > 15:
                st.warning("⚠️ Warning: No degenerate gambling, lions!")
                st.stop()

            build_number_input("total_max_margin: ")
            build_number_input("Trailing SL percent:", min_value=0.0)
            build_number_input("Pull SL price:", )
            build_number_input("Current Asset Price:")

            build_selectbox("Order Type:", options = st.session_state.input_trade.trade_parameters.order_type)

            build_number_input("Buffer_SL:")
            build_number_input("Current SL price:", )

    with st.container(border=True):
        st.subheader("🎯 Fast Order")
        with st.expander("Fast Inputs", expanded = True):
            build_number_input("total risk:",  step = 1.0)
            
            build_number_input("p_SL:", )
          
            #description
            st.write(rf"- loosing {st.session_state.input_total_risk}\$ if price goes to {st.session_state.input_p_SL}\$.")


def current_direction_label():
    if "input_trade" in st.session_state and st.session_state.input_trade.tranches:
        d = st.session_state.input_trade.tranches[0].tranche_parameters.current_direction
        if d == "long":
            st.success("Long")
        elif d == "short":
            st.error("Short")
        else:
            st.warning("Trade direction not consistent. Please check your input parameters.")
    else:
        st.warning("⚠️ Keine Tranchen vorhanden.")


def update_tp_targets_triggered():
    p = p = st.session_state.input_trade.trade_parameters

    if not st.session_state.input_trade.tranches[0].tranche_parameters.current_direction:
        return st.session_state.input_trade
    
    for tranche in st.session_state.input_trade.tranches:
        if tranche.tranche_parameters.current_direction == "long":
            tranche.tp_target.triggered = p.current_asset_price >= tranche.profit_target    #boolish equation
        elif tranche.tranche_parameters.current_direction == "short":
            tranche.tp_target.triggered = p.current_asset_price <= tranche.profit_target
    return st.session_state.input_trade


def fast_order_table():
    tranche1 = st.session_state.input_trade.tranches[0]
    with st.container(border=True):
        st.subheader("📊 Fast Order Table")
        # Wir nutzen Spalten für eine saubere Anordnung nebeneinander
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("lvg", f"{tranche1.tranche_parameters.lvg} x")
        col2.metric("isolated margin", f"{round(tranche1.tranche_parameters.isolated_margin, 2)} $")
        col3.metric("p_liquidation", f"{round(tranche1.tranche_parameters.p_liquidation, 2)} $")
        col4.metric("n_pos_value", f"{round(tranche1.tranche_parameters.n_pos_value, 2)} $")

    st.divider() # Visuelle Trennlinie zwischen den Abschnitten


def render_ladder(trade, mode): #modes: Entries, tranche_bound_TPs, global_TPs
    m = mode
    #for quick trade entry Entry ladder is always expanded at beginning
    if m == "Entries":
        is_Entries = True
    else:
        is_Entries = False

    #ladder:
    with st.expander(f"Ladder {m}", expanded = is_Entries):
        #tp_mode menu
        if m == "global_TPs" or m == "tranche_bound_TPs":
            # Bestimme den aktuellen Index basierend auf dem Trade-Objekt
            current_mode = st.session_state.input_trade.trade_parameters.tp_mode    #könnte falsch sein, wenn tp_mode aus vorherigerem überschrieben wird
            modes_list = list(get_args(Trade_Parameters.__annotations__["tp_mode"]))    #classes.py as tp_mode single source of truth
            default_index = modes_list.index(current_mode) if current_mode in modes_list else 0

            build_radio("Choose TP mode:", options = modes_list, index = default_index, key="input_tp_mode",   # Sichert die Anbindung an die sync-Logik
            )

        #Managing ladder size for each mode
        entry_col1, entry_col2 = st.columns(2)
        with entry_col1:
            if st.button(f"Weitere {m} hinzufügen", key= f"add_{m}_button"):   
                if m == "Entries" or m == "tranche_bound_TPs":
                    add_tranche()
                    
                elif m == "global_TPs":
                    add_global_tp_target()

        with entry_col2:
            if st.button(f"{m} entfernen", key = f"remove_{m}_button"):
                if m == "Entries" or m == "tranche_bound_TPs":
                    remove_tranche()
                elif m == "global_TPs":
                    remove_global_tp_target()
        
        #buildung input fields for each mode
        if m == "Entries" or m == "tranche_bound_TPs":    
            for index, tranche in enumerate(st.session_state.input_trade.tranches):
                if m == "Entries":
                    price_key = f"input_entry_price_{index}"
                    share_key = f"input_position_share_{index}"
                    
                    # 1. Sicherstellen, dass der Wert existiert und min. den min_value (0.01) hat
                    if price_key not in st.session_state or st.session_state[price_key] < 0.01:
                        st.session_state[price_key] = max(0.01, float(tranche.entry_level.price))
                        
                    if share_key not in st.session_state or st.session_state[share_key] < 0.01:
                        st.session_state[share_key] = max(0.01, float(tranche.entry_level.position_share))

                    # 2. Widgets über den Key steuern
                    build_number_input(f"Tranche {index + 1} Entry Price [$]:", min_value=0.01, step=0.01, key= price_key)
                    
                    build_number_input(f"Tranche {index + 1} Share [%]:", min_value=0.01, step=0.01, key=share_key)

                elif m == "tranche_bound_TPs":
                    tp_price_key = f"tp_price_{index}"
                    tp_percent_key = f"tp_close_percent_{index}"

                    build_number_input(f"TP {index + 1} Preis:", min_value=0.01, key = tp_price_key)
        
                    build_number_input(f"TP {index + 1} Schließung (%):", min_value=0.0, max_value=100.0, step = 1.0, key = tp_percent_key )
                
                    #visualize:
                    st.markdown(f"**{m} Levels:**")
                    for tranche in st.session_state.input_trade.tranches:
                        if m == "Entries":
                            st.write(f"- entering with {tranche.entry_level.position_share}% of the full position size at {tranche.entry_level.price}$.")
                        elif m == "TPs":
                            st.write(f"Closing {tranche.tp_target.close_percent}% of the position at {tranche.tp_target.price}$.")

        elif m == "global_TPs":
            for index, tp in enumerate(st.session_state.input_trade.global_tp_targets):
                global_price_key = f"input_global_entry_price_{index}"
                global_share_key = f"input_global_position_share_{index}"
                
                # 1. Sicherstellen, dass der Wert existiert und min. den min_value (0.01) hat
                if global_price_key not in st.session_state or st.session_state[global_price_key] < 0.01:
                    st.session_state[global_price_key] = max(0.01, float(tp.price))
                    
                if global_share_key not in st.session_state or st.session_state[global_share_key] < 0.01:
                    st.session_state[global_share_key] = max(0.01, float(tp.close_percent))

                # 2. Widgets über den Key steuern
                build_number_input(f" {index + 1}. TP target:", key = global_price_key)
                
                build_number_input(f"TP{index + 1} Share [%]:", key = global_share_key)
                    
            #visualize:
            st.markdown(f"**{m} Levels:**")
            for tp in st.session_state.input_trade.global_tp_targets:
                st.write(f"Closing {tp.close_percent}% of the full position size at {tp.price}$.")

    return st.session_state.input_trade




#st inputs lay on keys, now we need to sync them back to the session state input_trade object, so that the object can be used for calculations
def load_ui_into_trade():
    trade = st.session_state.input_trade
    t = trade.trade_parameters

    # Automatisches Durchgehen aller Felder in Trade_Parameters
    for field in fields(t):
        key = f"input_{field.name}"
        if key in st.session_state:
            setattr(t, field.name, st.session_state[key])

    # Das Gleiche für die Tranchen
    for index, tranche in enumerate(trade.tranches):
        tp = tranche.tranche_parameters
        for field in fields(tp):
            key = f"input_tranche_{index}_{field.name}"
            if key in st.session_state:
                setattr(tp, field.name, st.session_state[key])
                
        # Entry-Werte separat holen
        if f"input_entry_price_{index}" in st.session_state:
            tranche.entry_level.price = st.session_state[f"input_entry_price_{index}"]
        if f"input_position_share_{index}" in st.session_state:
            tranche.entry_level.position_share = st.session_state[f"input_position_share_{index}"]

    # NEU: Synchronisation der globalen TPs
    if st.session_state.input_trade.trade_parameters.tp_mode == "global_TPs":
        for index, tp in enumerate(st.session_state.input_trade.global_tp_targets):
            price_key = f"input_global_entry_price_{index}"
            share_key = f"input_global_position_share_{index}"
            
            if price_key in st.session_state:
                tp.price = float(st.session_state[price_key])
            if share_key in st.session_state:
                tp.close_percent = float(st.session_state[share_key])


#Callback wrappers for user st numbr_inputs:
#"**kwargs" allows for additional demands on the input, p.ex. specific max_value for a parameter

#label_cleaner for key generation:
def clean_label(label):
    # Remove special characters and spaces for key generation; replaces are executed after one another, so order can matter
    return label.lower().replace(" ", "_").replace(":", "").replace("-", "").lower()

def build_number_input(label, key = None, min_value = 0.0, step = 0.01, on_change = load_ui_into_trade, **kwargs):
    # Wenn KEIN Key übergeben wurde (key ist None), bauen wir einen Standard-Key
    if key is None:
        key = f"input_{clean_label(label)}"
    
    return st.number_input(label, key = key, min_value = min_value, step = step, on_change = on_change, **kwargs)

def build_selectbox(label, options, key=None, on_change = load_ui_into_trade, **kwargs):
    if key is None:
        key = f"input_{clean_label(label)}"
        
    return st.selectbox(label, options=options, key=key, on_change = load_ui_into_trade, **kwargs)

def build_radio(label, options, key=None, on_change = load_ui_into_trade,**kwargs):
    if key is None:
        key = f"input_{clean_label(label)}"
        
    return st.radio(label, options=options, key=key, on_change = load_ui_into_trade, **kwargs)


def update_session_state(trade):
    st.session_state["trade"] = trade


def overview_table():
  tranche1 = st.session_state.input_trade.tranches[0]
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
          for tranche in st.session_state.input_trade.tranches:
              status = "✅ Erreicht" if tranche.tp_target.triggered else "- offen"
              st.write(f"- TP bei {tranche.tp_target.price} | {tranche.tp_target.close_percent}% Schließung | {status}")

  st.divider()


def visualize_trade():
    tranche1 = st.session_state.input_trade.tranches[0]
    st.title("Trade Visualizer")

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
        st.altair_chart(chart, width='stretch')
    except Exception as exc:
        st.warning(f"Error in visualizing trade: {exc}")
