import streamlit as st

from classes import Trade
from trading_logic import calculate_all
import streamlit_visualization


def main():
    #init keys:
    if "key" not in st.session_state:
        st.session_state["key"] = 0

    st.title("Too_Risky - Crypto live lvg and liquidation manager")
    st.text("Opimized for execution speed.")

    trade = streamlit_visualization.get_trade_parameters()
    trade = calculate_all(trade)

    #st.session_state["trade"] prevents overwriting after calculate_all()
    st.session_state["trade"] = trade
    streamlit_visualization.current_direction_label(st.session_state["trade"].parameters.current_direction)
    streamlit_visualization.fast_order_table(st.session_state["trade"])
    streamlit_visualization.visualize_trade(st.session_state["trade"])
    streamlit_visualization.overview_table(st.session_state["trade"])
    streamlit_visualization.render_trade_controls(st.session_state["trade"])


if __name__ == "__main__":
    main()
