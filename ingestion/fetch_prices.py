import os
import time
from datetime import date
import pandas as pd
import yfinance as yf
from ingestion.fetch_tickers import fetch_nse_tickers


def get_all_symbols():
    """Get all NSE symbols, formatted for yfinance."""
    nse_tickers = fetch_nse_tickers()
    all_symbols = nse_tickers["SYMBOL"].tolist()
    return [f"{s}.NS" for s in all_symbols]


def get_test_symbols(limit=20):
    """Get a small subset of NSE symbols, formatted for yfinance."""
    nse_tickers = fetch_nse_tickers()
    all_symbols = nse_tickers["SYMBOL"].tolist()
    return [f"{s}.NS" for s in all_symbols[:limit]]


def fetch_prices(symbols, period="5d"):
    """Fetch historical price data for given symbols."""
    data = yf.download(symbols, period=period, group_by="ticker")
    return data


def reshape_to_long(data):
    """Convert wide multi-ticker yfinance output to long format (one row per ticker per day)."""
    df = data.stack(level=0, future_stack=True).reset_index()
    df = df.rename(columns={"level_1": "ticker", "Date": "date"})
    df.columns = [c.lower() for c in df.columns]
    return df


def fetch_prices_batched(symbols, period="5d", batch_size=50, delay=2):
    """Fetch prices in batches to avoid overwhelming the API."""
    all_data = []
    total_batches = (len(symbols) + batch_size - 1) // batch_size

    for batch_num, i in enumerate(range(0, len(symbols), batch_size), start=1):
        batch = symbols[i:i + batch_size]
        print(f"Batch {batch_num}/{total_batches}: fetching {len(batch)} symbols ({i} to {i + len(batch)})")
        try:
            data = yf.download(batch, period=period, group_by="ticker", threads=True)
            long_df = reshape_to_long(data)
            all_data.append(long_df)
            print(f"Batch {batch_num} succeeded: {len(long_df)} rows")
        except Exception as e:
            print(f"Batch {batch_num} FAILED: {e}")
        time.sleep(delay)

    if not all_data:
        raise RuntimeError("All batches failed - no data fetched")

    return pd.concat(all_data, ignore_index=True)


def save_raw(df, folder="data/raw"):
    """Save fetched data to a dated folder, untouched."""
    today = date.today().isoformat()
    out_dir = os.path.join(folder, today)
    os.makedirs(out_dir, exist_ok=True)

    out_path = os.path.join(out_dir, "prices.csv")
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows to {out_path}")
    return out_path


if __name__ == "__main__":
    symbols = get_all_symbols()
    print(f"Total symbols to fetch: {len(symbols)}")
    long_df = fetch_prices_batched(symbols, batch_size=50, delay=2)
    print(long_df.head(10))
    print(long_df.shape)
    save_raw(long_df)