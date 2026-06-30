import pandas as pd

def fetch_nse_tickers():
    """Fetch the full list of NSE-listed equity symbols."""
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    nse_tickers = pd.read_csv(url)
    return nse_tickers

if __name__ == "__main__":
    df = fetch_nse_tickers()
    print(df.columns.tolist())
    print(df.shape)
    print(df.head(10))