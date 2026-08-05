#stream_lit file search fix:
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from classes import Trade
from trading_logic import calculate_all
import streamlit_visualization


def main():
    #Init:
    streamlit_visualization.init_session_state()
    streamlit_visualization.intro()

    raw = streamlit_visualization.get_trade_inputs_from_ui()

    #prevent crash if raw is Any / None
    if raw is None:
        raise ValueError("Trade object is None. Cannot perform calculations.")
    trade: Trade = raw

    #Do the Math
    trade = calculate_all(trade)
    
    
    # updating session state after calc; st.session_state["trade"] prevents overwriting after calculate_all()
    streamlit_visualization.update_session_state(trade)

    #Visualization of Session State Trade Object:
    streamlit_visualization.current_direction_label()
    streamlit_visualization.fast_order_table()
    streamlit_visualization.visualize_trade()
    streamlit_visualization.overview_table()


if __name__ == "__main__":
    main()
