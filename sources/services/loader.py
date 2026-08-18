# sources/loader.py
import pandas as pd

def load_data():
    # Beispiel: CSV laden
    #df = pd.read_csv("data/input.csv")
    
    # Platzhalter-Daten, damit Dash startet
    df = pd.DataFrame({
        "x": [1, 2, 3, 4, 5],
        "y": [10, 15, 13, 17, 20]
    })
    return df
