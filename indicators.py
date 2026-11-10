import numpy as np
import pandas as pd

def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False, min_periods=span).mean()

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add MACD(8,17,9), Stochastic(14,3,3), ADX(14), EMA(20,50), and volume SMA(20)."""
    out = df.copy().sort_index()
    close = out["Close"].astype(float)
    high = out["High"].astype(float)
    low = out["Low"].astype(float)
    volume = out["Volume"].astype(float)

    out["EMA20"] = _ema(close, 20)
    out["EMA50"] = _ema(close, 50)

    fast = _ema(close, 8)
    slow = _ema(close, 17)
    out["MACD"] = fast - slow
    out["MACD_Signal"] = _ema(out["MACD"], 9)
    out["MACD_Hist"] = out["MACD"] - out["MACD_Signal"]
    out["MACD_Zero_Cross_Up"] = (out["MACD"] > 0) & (out["MACD"].shift(1) <= 0)

    lowest = low.rolling(14, min_periods=14).min()
    highest = high.rolling(14, min_periods=14).max()
    denom = (highest - lowest).replace(0, np.nan)
    out["Stoch_K_Raw"] = 100 * (close - lowest) / denom
    out["Stoch_K"] = out["Stoch_K_Raw"].rolling(3, min_periods=3).mean()
    out["Stoch_D"] = out["Stoch_K"].rolling(3, min_periods=3).mean()

    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=out.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=out.index)
    prev_close = close.shift(1)
    tr = pd.concat([(high-low), (high-prev_close).abs(), (low-prev_close).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1/14, adjust=False, min_periods=14).mean() / atr
    minus_di = 100 * minus_dm.ewm(alpha=1/14, adjust=False, min_periods=14).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    out["ADX14"] = dx.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    out["Volume_SMA20"] = volume.rolling(20, min_periods=20).mean()
    return out
