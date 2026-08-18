# sources/loader.py
import pandas as pd

def load_data():
    # Beispiel: CSV laden
    df = pd.read_csv("data/input.csv")
    return df
