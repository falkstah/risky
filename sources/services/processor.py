import pandas as pd

def process_data(df: pd.DataFrame) -> pd.DataFrame:
    print("Processor läuft (Dummy-Berechnung).")
    df["dummy"] = range(len(df))
    return df
