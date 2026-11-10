from pathlib import Path
import pandas as pd
import plotly.express as px

DATA_DIR = Path(__file__).parent / "data"
BREAKOUT_FILE = DATA_DIR / "breakout_log.csv"
TRADE_FILE = DATA_DIR / "trade_history.csv"

def load_breakout_log():
    DATA_DIR.mkdir(exist_ok=True)
    return pd.read_csv(BREAKOUT_FILE) if BREAKOUT_FILE.exists() else pd.DataFrame(columns=["Symbol", "Breakout", "Signal", "Date", "Close", "Breakout Level", "Volume", "Volume SMA20", "Volume Multiple", "Relative Strength %", "ADX14", "EMA20", "EMA50", "MACD", "Timeframe", "Recorded At"])

def save_breakout_log(new_rows, old_log, timeframe):
    rows = new_rows.copy()
    rows["Timeframe"] = timeframe
    rows["Recorded At"] = pd.Timestamp.now(tz="Asia/Kolkata").strftime("%Y-%m-%d %H:%M:%S %Z")
    combined = pd.concat([old_log, rows], ignore_index=True)
    if not combined.empty:
        combined = combined.drop_duplicates(subset=["Symbol", "Date", "Timeframe"], keep="last")
    DATA_DIR.mkdir(exist_ok=True)
    combined.to_csv(BREAKOUT_FILE, index=False)
    return combined

def closed_trade_analytics():
    if not TRADE_FILE.exists():
        return pd.DataFrame()
    df = pd.read_csv(TRADE_FILE)
    required = {"Symbol", "Entry Date", "Entry Price", "Exit Date", "Exit Price"}
    if not required.issubset(df.columns):
        return pd.DataFrame()
    df["Entry Price"] = pd.to_numeric(df["Entry Price"], errors="coerce")
    df["Exit Price"] = pd.to_numeric(df["Exit Price"], errors="coerce")
    df = df.dropna(subset=["Entry Price", "Exit Price"])
    df["PnL %"] = (df["Exit Price"] / df["Entry Price"] - 1) * 100
    df["Equity"] = (1 + df["PnL %"] / 100).cumprod() * 100
    return df

def plot_equity_curve(trades):
    return px.line(trades, x="Exit Date", y="Equity", markers=True, title="Closed-trade compounded equity curve (base = 100)")
