import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from nifty500 import load_nifty500_universe
from data_fetcher import fetch_ohlcv
from strategy import scan_symbol
from analytics import load_breakout_log, save_breakout_log, closed_trade_analytics, plot_equity_curve

st.set_page_config(page_title="Nifty 500 Momentum Breakout Scanner", page_icon="📈", layout="wide")
st.title("📈 Nifty 500 Momentum Breakout Scanner")
st.caption("Research scanner only — no broker connection or automatic order execution.")

with st.sidebar:
    st.header("Scanner settings")
    timeframe = st.radio("Timeframe", ["1 Day", "1 Week"], horizontal=True)
    period = st.selectbox("Historical lookback", ["2y", "5y", "10y"], index=1)
    max_symbols = st.number_input("Maximum symbols to scan (testing)", min_value=10, max_value=500, value=500, step=10)
    refresh = st.button("🔄 Run / refresh scan", type="primary")
    st.caption("Daily scans use completed daily candles. Weekly scans use completed weekly candles.")

@st.cache_data(ttl=3600, show_spinner=False)
def get_universe():
    return load_nifty500_universe()

universe, universe_note = get_universe()
st.info(universe_note)
if universe.empty:
    st.error("Could not load the Nifty 500 universe. Check internet access and try again.")
    st.stop()

symbols = universe["Symbol"].dropna().astype(str).tolist()[:int(max_symbols)]
interval = "1d" if timeframe == "1 Day" else "1wk"
benchmark = "^NSEI"

if "scan_results" not in st.session_state:
    st.session_state.scan_results = pd.DataFrame()
if refresh or st.session_state.scan_results.empty:
    rows, errors = [], []
    progress = st.progress(0, text="Preparing scan…")
    status = st.empty()
    with st.spinner(f"Scanning {len(symbols)} symbols. This may take several minutes…"):
        for i, symbol in enumerate(symbols, start=1):
            status.write(f"Scanning {symbol} ({i}/{len(symbols)})")
            try:
                stock = fetch_ohlcv(symbol, interval, period)
                nifty = fetch_ohlcv(benchmark, interval, period)
                if stock.empty or nifty.empty:
                    continue
                result = scan_symbol(symbol, stock, nifty)
                if result:
                    rows.append(result)
            except Exception as exc:
                errors.append(f"{symbol}: {str(exc)[:140]}")
            progress.progress(i / len(symbols), text=f"Scanned {i}/{len(symbols)}")
    progress.empty()
    status.empty()
    st.session_state.scan_results = pd.DataFrame(rows)
    st.session_state.scan_errors = errors

results = st.session_state.scan_results
if not results.empty:
    results = results.sort_values(["Breakout", "Relative Strength %"], ascending=[False, False])
    c1, c2, c3 = st.columns(3)
    c1.metric("Stocks scanned", len(symbols))
    c2.metric("Breakout candidates", int(results["Breakout"].sum()))
    c3.metric("Positive relative strength", int((results["Relative Strength %"] > 0).sum()))
    st.subheader("Breakout candidates and watchlist")
    show_cols = ["Symbol", "Breakout", "Signal", "Date", "Close", "Breakout Level", "Volume", "Volume SMA20", "Volume Multiple", "Relative Strength %", "ADX14", "EMA20", "EMA50", "MACD"]
    st.dataframe(results[show_cols], use_container_width=True, hide_index=True)
    st.download_button("Download scan results CSV", results.to_csv(index=False), "nifty500_scan_results.csv", "text/csv")
    new_breakouts = results[results["Breakout"] == True].copy()
    if not new_breakouts.empty:
        log = load_breakout_log()
        log = save_breakout_log(new_breakouts, log, timeframe)
        st.success(f"{len(new_breakouts)} breakout event(s) recorded in data/breakout_log.csv.")
else:
    st.warning("No qualifying setups found in the current scan. This is normal; the scanner does not force signals.")

errors = st.session_state.get("scan_errors", [])
if errors:
    with st.expander(f"Data issues ({len(errors)})"):
        st.write("\n".join(errors[:100]))

st.divider()
st.subheader("Closed-trade analytics")
st.caption("Import or maintain closed trades in data/trade_history.csv. This scanner records breakout candidates; it does not assume an exit or fabricate closed trades.")
trades = closed_trade_analytics()
if trades.empty:
    st.info("No closed trades recorded yet. Add rows to data/trade_history.csv using the template described in README.md.")
else:
    a, b, c = st.columns(3)
    a.metric("Closed trades", len(trades))
    b.metric("Win rate", f"{(trades['PnL %'] > 0).mean() * 100:.1f}%")
    b.metric("Net return (sum of trade %)", f"{trades['PnL %'].sum():.2f}%")
    st.dataframe(trades, use_container_width=True, hide_index=True)
    fig = plot_equity_curve(trades)
    st.plotly_chart(fig, use_container_width=True)

st.caption(f"Last page render: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} local app time. Market data is supplied by Yahoo Finance via yfinance and may be delayed, incomplete, or unavailable.")
