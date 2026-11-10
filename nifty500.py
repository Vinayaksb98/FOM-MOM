import io
import pandas as pd
import requests

NSE_URL = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
FALLBACK_URL = "https://raw.githubusercontent.com/rahulbanerjee26/Nifty-Indices-Data/main/NIFTY500.csv"

def load_nifty500_universe():
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "text/csv,*/*", "Referer": "https://www.nseindia.com/"}
    for url in (NSE_URL, FALLBACK_URL):
        try:
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            df = pd.read_csv(io.BytesIO(response.content))
            cols = {c.lower().strip(): c for c in df.columns}
            symbol_col = cols.get("symbol") or cols.get("ticker")
            if symbol_col:
                out = pd.DataFrame({"Symbol": df[symbol_col].astype(str).str.strip() + ".NS"})
                out["Symbol"] = out["Symbol"].str.replace(".NS.NS", ".NS", regex=False)
                out = out.drop_duplicates().sort_values("Symbol").reset_index(drop=True)
                if len(out) > 100:
                    return out, f"Loaded {len(out)} Nifty 500 constituents from {url}."
        except Exception:
            pass
    return pd.DataFrame(columns=["Symbol"]), "Unable to retrieve the Nifty 500 constituent list from the configured sources."
