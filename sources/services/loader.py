import pandas as pd
import requests
from requests.adapters import HTTPAdapter

session = requests.Session()
session.mount("https://", HTTPAdapter(max_retries=3))

def load_initial_candles(interval, limit = 30):
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "BTCUSDT",
        "interval": interval,
        "limit": limit + (1 if interval == "1m" else 0)  # 1m holt eine Kerze mehr, weil unvollst. 1m kerze degroppt wird, da binance 1m tf anders behandelt
    }
    
     # stable HTTPS‑Request
    response = session.get(url, params=params, timeout=5)
    response.raise_for_status()   # wirft klaren Fehler statt SSL‑Chaos
    data = response.json()
    print("DEBUG 1m:", interval, "len(data) =", len(data))


    # Bei 1m die letzte (laufende) Kerze entfernen, 
    # #weil das einziger tf, bei dem aktuell laufende Kerze auch ausgegeben wird für Scalper 
    # -> letzte Kerze erzeugt Fehler
    if interval == "1m" and len(data) > 0:
        data = data[:-1]

    rows = []
    for value in data:
        # Schutz gegen kaputte Candles (0-Werte oder None)
        try:
            t = value[0]
            o = float(value[1])
            h = float(value[2])
            l = float(value[3])
            c = float(value[4])

            # Nur gültige Kerzen übernehmen
            if t is None or o == 0 or h == 0 or l == 0 or c == 0:
                continue

            rows.append({
                "t": pd.to_datetime(t, unit="ms"),
                "open": o,
                "high": h,
                "low": l,
                "close": c
            })
        except:
            # Falls Binance eine kaputte Zeile liefert → skip
            continue

    return pd.DataFrame(rows)
