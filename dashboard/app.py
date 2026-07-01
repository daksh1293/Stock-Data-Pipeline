import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

st.set_page_config(page_title="NSE Stock Pipeline Dashboard", layout="wide")

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "stock_pipeline")


@st.cache_resource
def get_engine():
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


@st.cache_data(ttl=300)
def load_data():
    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM fct_daily_returns"), conn)
    return df


st.title("NSE Stock Pipeline Dashboard")
st.caption("Data is refreshed daily by an automated Airflow pipeline. If you just started this stack, trigger the DAG once to populate data.")

df = load_data()

if df.empty:
    st.warning("No data yet. Run the stock_pipeline_dag in Airflow to populate the database.")
    st.stop()

latest_date = df["date"].max()
latest = df[df["date"] == latest_date].dropna(subset=["daily_return_pct"])

col1, col2 = st.columns(2)

with col1:
    st.subheader(f"Top Gainers — {latest_date}")
    top_gainers = latest.sort_values("daily_return_pct", ascending=False).head(10)
    st.dataframe(
        top_gainers[["ticker", "close", "daily_return_pct"]],
        hide_index=True,
        use_container_width=True,
    )

with col2:
    st.subheader(f"Top Losers — {latest_date}")
    top_losers = latest.sort_values("daily_return_pct", ascending=True).head(10)
    st.dataframe(
        top_losers[["ticker", "close", "daily_return_pct"]],
        hide_index=True,
        use_container_width=True,
    )

st.divider()

st.subheader("Ticker Detail")
tickers = sorted(df["ticker"].unique())
default_index = tickers.index("RELIANCE.NS") if "RELIANCE.NS" in tickers else 0
selected = st.selectbox("Select a ticker", tickers, index=default_index)

ticker_df = df[df["ticker"] == selected].sort_values("date").copy()
ticker_df["date"] = pd.to_datetime(ticker_df["date"]).dt.date

col3, col4 = st.columns(2)
with col3:
    st.line_chart(ticker_df.set_index("date")["close"], y_label="Close Price")
with col4:
    st.line_chart(ticker_df.set_index("date")["rolling_7day_avg_close"], y_label="7-Day Rolling Avg")

st.dataframe(
    ticker_df[["date", "open", "high", "low", "close", "volume", "daily_return_pct"]],
    hide_index=True,
    use_container_width=True,
)
