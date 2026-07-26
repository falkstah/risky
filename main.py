import streamlit as st

from classes import TradeParameters
from trading_logic import calculate_all
import streamlit_visualization


def main():
    st.title("Too_Risky - Crypto live lvg and liquidation manager")
    st.text("Opimized for execution speed.")

    params = streamlit_visualization.get_trade_parameters()
    params = calculate_all(params)

    #st.session_state["params"] prevents overwriting after calculate_all()
    streamlit_visualization.current_direction_label(st.session_state["params"].current_direction)
    streamlit_visualization.fast_order_table(st.session_state["params"])
    streamlit_visualization.visualize_trade(st.session_state["params"])
    streamlit_visualization.overview_table(st.session_state["params"])


if __name__ == "__main__":
    main()
