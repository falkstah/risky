import streamlit as st

from classes import TradeParameters
from trading_logic import calculate_all
import streamlit_visualization


def main():
    st.title("Too_Risky - Crypto live lvg and liquidation manager")
    st.text("Opimized for execution speed.")

    liq_delta_to_SL_delta_ratio, risk, maintainance_margin_rate, maintainance_deduction, max_leverage, max_margin, p_entry, p_SL = streamlit_visualization.get_trade_parameters()
    params = TradeParameters(
        liq_delta_to_SL_delta_ratio=liq_delta_to_SL_delta_ratio,
        risk=risk,
        maintainance_margin_rate=maintainance_margin_rate,
        maintainance_deduction=maintainance_deduction,
        p_entry=p_entry,
        p_SL=p_SL,
        p_TP=streamlit_visualization.get_TP(),
        max_leverage=max_leverage,
        max_margin=max_margin,
    )
    params = calculate_all(params)

    streamlit_visualization.current_direction_label(params.current_direction)
    streamlit_visualization.fast_order_table(params)
    streamlit_visualization.visualize_trade(params)
    streamlit_visualization.overview_table(params)


if __name__ == "__main__":
    main()
