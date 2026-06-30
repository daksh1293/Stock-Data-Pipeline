import os
from datetime import date
import yfinance as yf
from ingestion.fetch_tickers import fetch_nse_tickers


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
    symbols = get_test_symbols(limit=20)
    print(symbols)
    data = fetch_prices(symbols)
    long_df = reshape_to_long(data)
    print(long_df.head(10))
    print(long_df.shape)
    save_raw(long_df)