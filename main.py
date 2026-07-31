#stream_lit file search fix:
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from classes import Trade, Trade_Parameters, Tranche, Tranche_Parameters, Take_Profit_Target, Entry_Level
from trading_logic import calculate_all
import streamlit_visualization


def main():
    #Init:
    streamlit_visualization.init_session_state()
    streamlit_visualization.intro()

    #gets trade von session_state
    trade = streamlit_visualization.get_trade()

    #Assign Values to trade
    trade = streamlit_visualization.get_trade_parameters(trade)
    trade = streamlit_visualization.render_ladders(trade)

    #Do the Math
    trade = calculate_all(trade)

    # st.session_state["trade"] prevents overwriting after calculate_all()
    st.session_state["trade"] = trade
    up_down = trade.tranches[0].tranche_parameters.current_direction
    streamlit_visualization.current_direction_label(st.session_state["trade"].trade_parameters.up_down)
    streamlit_visualization.fast_order_table(st.session_state["trade"])
    streamlit_visualization.visualize_trade(st.session_state["trade"])
    streamlit_visualization.overview_table(st.session_state["trade"])


if __name__ == "__main__":
    main()
