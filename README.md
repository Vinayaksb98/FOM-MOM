# Nifty 500 Momentum Breakout Scanner

A standalone Streamlit research dashboard for scanning Nifty 500 stocks using MACD + Stochastic momentum rules. It does **not** place trades.

## Features
- Nifty 500 universe loaded from NSE constituent CSV, with a secondary CSV source.
- Manual 1 Day / 1 Week timeframe selection.
- MACD (8,17,9), Stochastic (14,3,3), ADX (14), EMA (20,50), and Volume SMA (20).
- Two-stage Stochastic sequence: initial overbought phase, cooling below 80, then second overbought phase.
- MACD must remain above zero during the setup.
- Price protection against the close recorded at the latest MACD zero-cross-up.
- Breakout above the high of the initial overbought phase.
- Volume at least 1.5x its 20-period average.
- Relative strength versus Nifty 50 over 20 bars.
- Breakout event log, closed-trade analytics, and equity curve.

## Strategy interpretation used in this implementation
1. An initial phase begins when smoothed Stochastic %K crosses above 80.
2. The first phase high is tracked until %K closes back at or below 80.
3. Cooling is confirmed when %K is at or below 80.
4. A second phase begins when %K crosses above 80 again.
5. A breakout is confirmed when a candle closes above the first phase high.
6. MACD must be above zero during the sequence. The close at the latest MACD upward zero-cross is used as the price-protection reference; any later close below that reference resets the setup.
7. Final breakout confirmation also requires volume >= 1.5 x Volume SMA(20) and positive 20-bar relative strength versus Nifty 50.

**Important design note:** The user-specified rules do not define whether the MACD zero-cross reference should use the MACD line crossing zero or the MACD/signal bullish crossover. This version uses the MACD line crossing above zero and the close of that candle as the reference. ADX and EMA values are displayed as confirmation context but are not hard filters because no minimum ADX or EMA condition was specified.

## Deploy on Streamlit Community Cloud
1. Create a GitHub repository, e.g. `nifty500-momentum-scanner`.
2. Upload all project files and folders from this ZIP to the repository root.
3. Open https://share.streamlit.io/ and connect the GitHub repository.
4. Select branch `main` and main file `app.py`, then deploy.

## Run locally (optional)
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Data and persistence
- Market data is fetched from Yahoo Finance through `yfinance`; it may be delayed, rate-limited, or unavailable.
- `data/breakout_log.csv` stores breakout detections on the app filesystem.
- `data/trade_history.csv` stores closed trades for analytics.
- Streamlit Community Cloud local filesystem storage is **not guaranteed to persist** across restarts, rebuilds, or redeployments. For durable records, use a persistent external database or storage service.
- Scanning 500 symbols can take several minutes and Yahoo Finance may throttle requests. For first testing, set Maximum symbols to scan to 20–50.

## Closed-trade CSV template
Create `data/trade_history.csv` with these headers:
```csv
Symbol,Entry Date,Entry Price,Exit Date,Exit Price
```
Each row is one closed trade. The app calculates percentage P&L and a compounded equity curve.

## Limitations / validation checklist
- This is a screening prototype, not a backtested or validated investment system.
- Check a sample of signals manually against charts before relying on them.
- Yahoo Finance can return missing, adjusted, stale, or inconsistent data.
- A daily scan records the candle date; the app's log also records the scan timestamp. Weekly signals are based on completed weekly bars.
- The app scans sequentially to reduce request bursts, but large scans can still hit provider limits.
