import yfinance as yf
import pandas as pd

def fetch_ohlcv(symbol: str, interval: str = "1d", period: str = "5y") -> pd.DataFrame:
    ticker = symbol if symbol.startswith("^") else symbol
    df = yf.download(ticker, period=period, interval=interval, auto_adjust=False, progress=False, threads=False)
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    needed = ["Open", "High", "Low", "Close", "Volume"]
    if not set(needed).issubset(df.columns):
        return pd.DataFrame()
    df = df[needed].dropna(subset=["High", "Low", "Close"])
    df.index = pd.to_datetime(df.index)
    # Yahoo's latest daily/weekly bar can still be forming. Exclude it to avoid intrabar signals.
    now = pd.Timestamp.now(tz="Asia/Kolkata")
    last = df.index[-1]
    if last.tzinfo is not None:
        last_local = last.tz_convert("Asia/Kolkata")
    else:
        last_local = last.tz_localize("Asia/Kolkata")
    if interval == "1d":
        if last_local.date() == now.date() and now.hour < 16:
            df = df.iloc[:-1]
    elif interval == "1wk":
        # Keep only weeks that ended before the current local week.
        current_week = now.isocalendar().week
        current_year = now.isocalendar().year
        mask = [not (x.isocalendar().week == current_week and x.isocalendar().year == current_year) for x in df.index]
        df = df.loc[mask]
    return df
