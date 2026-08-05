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

    trade = streamlit_visualization.get_trade_object_inputs()
   
    #Do the Math
    if trade is not None:
        trade = calculate_all(trade)
    else: 
        st.warning("Please provide valid inputs for the trade parameters.")
        return
    
    # updating session state after calc; st.session_state["trade"] prevents overwriting after calculate_all()
    streamlit_visualization.update_session_state(trade)

    #Visualization:
    streamlit_visualization.current_direction_label(trade)
    streamlit_visualization.fast_order_table(trade)
    streamlit_visualization.visualize_trade(trade)
    streamlit_visualization.overview_table(trade)


if __name__ == "__main__":
    main()
