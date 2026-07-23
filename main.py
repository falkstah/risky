import streamlit as st

from classes import TradeParameters
from trading_logic import calculate_all
import streamlit_visualization


def main():
    st.title("Too_Risky - Crypto live lvg and liquidation manager")
    st.text("Opimized for execution speed.")

    params = TradeParameters(*streamlit_visualization.get_trade_parameters(), p_TP=streamlit_visualization.get_TP())
    params = calculate_all(params)

    streamlit_visualization.current_direction_label(params.current_direction)
    streamlit_visualization.fast_order_table(params)
    streamlit_visualization.visualize_trade(params)
    streamlit_visualization.overview_table(params)


if __name__ == "__main__":
    main()
