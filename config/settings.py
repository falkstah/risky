# config/settings.py

# ---------------------------------------------------------
# App‑Meta
# ---------------------------------------------------------
APP_TITLE = "Risky – Trading Visualizer"
APP_VERSION = "0.1.0"

# ---------------------------------------------------------
# Datenpfade
# ---------------------------------------------------------
DATA_PATH = "data/input.csv"          # Loader nutzt das
EXPORT_PATH = "data/export/"          # später für Saves

# ---------------------------------------------------------
# Plot‑Theme (für Plotly, JS‑Interaktion, Risiko‑Zonen)
# ---------------------------------------------------------
COLOR_THEME = {
    "background": "#0d1117",          # dunkles Dashboard
    "surface": "#161b22",             # Karten / Container
    "primary": "#58a6ff",             # Linien, Buttons
    "accent": "#f0c674",              # Markierungen
    "danger": "#ff4d4d",              # SL / Risiko
    "success": "#4caf50",             # TP / Gewinn
    "grid": "#30363d",                # Chart‑Grid
}

# ---------------------------------------------------------
# Chart‑Defaults (Plotter)
# ---------------------------------------------------------
CHART_SETTINGS = {
    "line_width": 2,
    "marker_size": 6,
    "font_family": "Segoe UI",
    "font_size": 14,
}

# ---------------------------------------------------------
# Interaktions‑Parameter (für JS / Drag & Drop)
# ---------------------------------------------------------
INTERACTION = {
    "snap_distance": 10,              # Pixel‑Snap beim Ziehen
    "drag_color": COLOR_THEME["accent"],
    "hover_color": COLOR_THEME["primary"],
}

# ---------------------------------------------------------
# Fachliche Default-values (Processor)
# ---------------------------------------------------------

# ---------------------------------------------------------
# Fachliche Defaults für Entry-Level
# ---------------------------------------------------------
ENTRY_DEFAULTS = {
    "price": 0.01,            # fachlicher Startpreis
    "position_share": 1.0,    # 100% der Tranche
}

# ---------------------------------------------------------
# Fachliche Defaults für Take-Profit-Targets
# ---------------------------------------------------------
TP_DEFAULTS = {
    "price": 0.01,            # TP-Level
    "close_percent": 50.0,    # 50% schließen
}

# ---------------------------------------------------------
# Fachliche Defaults für Tranche-Parameter (Inputs)
# ---------------------------------------------------------
TRANCHE_INPUT_DEFAULTS = {
    "liq_delta_to_SL_delta_ratio": 4.0,
    "risk": 10.0,
    "maintainance_margin_rate": 0.02,
    "maintainance_deduction": 0.00,
    "max_lvg": 10.0,
    "max_margin": 100.0,      # deine Logik nutzt später 80% davon
}

# ---------------------------------------------------------
# Fachliche Defaults für Trade-Parameter
# ---------------------------------------------------------
TRADE_DEFAULTS = {
    "total_max_lvg": 10.0,
    "total_risk": 10.0,
    "liq_delta_to_SL_delta_ratio": 4.0,
    "maintainance_margin_rate": 0.02,
    "maintainance_deduction": 0.00,
    "order_type": "single limit",
    "tp_mode": "global_TPs",
}

# ---------------------------------------------------------
# Struktur-Defaults (Anzahl Objekte)
# ---------------------------------------------------------
TRADE_STRUCTURE_DEFAULTS = {
    "initial_tranches": 1,            # jeder Trade hat mind. 1 Tranche
    "initial_global_tp_targets": 0,   # optional
}
