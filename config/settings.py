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
# Risiko‑Parameter (Processor)
# ---------------------------------------------------------
RISK = {
    "risk_reward_default": 2.0,
    "max_risk_percent": 1.0,
    "min_position_size": 0.001,
}
