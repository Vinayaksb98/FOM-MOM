import pandas as pd
from indicators import add_indicators

OVERBOUGHT = 80.0

def _relative_strength(stock: pd.DataFrame, benchmark: pd.DataFrame, lookback: int = 20) -> float:
    joined = pd.concat([stock["Close"].rename("stock"), benchmark["Close"].rename("nifty")], axis=1).dropna()
    if len(joined) <= lookback:
        return float("nan")
    sret = joined["stock"].iloc[-1] / joined["stock"].iloc[-lookback-1] - 1
    bret = joined["nifty"].iloc[-1] / joined["nifty"].iloc[-lookback-1] - 1
    return float((sret - bret) * 100)

def _find_setup(df: pd.DataFrame):
    """
    State machine:
      1) Initial Stoch K cross above 80 while MACD > 0.
      2) Cooling: K closes back below 80; track high of initial overbought phase.
      3) Second K cross above 80 while MACD remains > 0.
      4) Breakout when close exceeds initial overbought phase high, with volume confirmation.
    MACD zero-cross reference is the close on the latest MACD cross above zero.
    Price protection: after that reference is set, no subsequent candle close may be below it.
    """
    state = "waiting_initial"
    phase_high = None
    zero_ref = None
    for i in range(1, len(df)):
        row, prev = df.iloc[i], df.iloc[i-1]
        if bool(row["MACD_Zero_Cross_Up"]):
            zero_ref = float(row["Close"])
        if zero_ref is not None and float(row["Close"]) < zero_ref:
            state, phase_high = "waiting_initial", None
            continue
        if pd.isna(row["Stoch_K"]) or pd.isna(prev["Stoch_K"]) or pd.isna(row["MACD"]):
            continue
        macd_ok = float(row["MACD"]) > 0
        crossed_up = float(prev["Stoch_K"]) <= OVERBOUGHT and float(row["Stoch_K"]) > OVERBOUGHT
        below = float(row["Stoch_K"]) <= OVERBOUGHT
        if not macd_ok:
            state, phase_high = "waiting_initial", None
            continue
        if state == "waiting_initial":
            if crossed_up:
                state = "first_overbought"
                phase_high = float(row["High"])
        elif state == "first_overbought":
            phase_high = max(phase_high, float(row["High"]))
            if below:
                state = "cooling"
        elif state == "cooling":
            if crossed_up:
                state = "second_overbought"
        elif state == "second_overbought":
            if float(row["Close"]) > float(phase_high):
                return i, float(phase_high)
    return None, None

def scan_symbol(symbol: str, stock: pd.DataFrame, benchmark: pd.DataFrame):
    if stock is None or stock.empty or len(stock) < 80:
        return None
    df = add_indicators(stock)
    benchmark = benchmark.copy()
    if benchmark.empty:
        return None
    rs = _relative_strength(df, benchmark, 20)
    idx, level = _find_setup(df)
    last = df.iloc[-1]
    # A breakout is valid only on the latest completed candle and with volume/confirmation filters.
    latest_idx = len(df) - 1
    volume_multiple = float(last["Volume"] / last["Volume_SMA20"]) if pd.notna(last["Volume_SMA20"]) and last["Volume_SMA20"] else float("nan")
    breakout = bool(idx == latest_idx and pd.notna(volume_multiple) and volume_multiple >= 1.5 and pd.notna(rs) and rs > 0)
    signal = "BREAKOUT" if breakout else ("SETUP / WATCH" if idx is not None else "—")
    date_value = df.index[-1]
    try:
        date_str = date_value.strftime("%Y-%m-%d")
    except Exception:
        date_str = str(date_value)
    return {
        "Symbol": symbol,
        "Breakout": breakout,
        "Signal": signal,
        "Date": date_str,
        "Close": round(float(last["Close"]), 2),
        "Breakout Level": round(float(level), 2) if level is not None else None,
        "Volume": int(last["Volume"]) if pd.notna(last["Volume"]) else None,
        "Volume SMA20": round(float(last["Volume_SMA20"]), 0) if pd.notna(last["Volume_SMA20"]) else None,
        "Volume Multiple": round(volume_multiple, 2) if pd.notna(volume_multiple) else None,
        "Relative Strength %": round(rs, 2) if pd.notna(rs) else None,
        "ADX14": round(float(last["ADX14"]), 2) if pd.notna(last["ADX14"]) else None,
        "EMA20": round(float(last["EMA20"]), 2) if pd.notna(last["EMA20"]) else None,
        "EMA50": round(float(last["EMA50"]), 2) if pd.notna(last["EMA50"]) else None,
        "MACD": round(float(last["MACD"]), 3) if pd.notna(last["MACD"]) else None,
    }
