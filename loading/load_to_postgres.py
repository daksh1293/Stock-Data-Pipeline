import os
from datetime import date
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


def get_engine():
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


def create_raw_table(engine):
    """Create the raw prices table if it doesn't exist, with a unique constraint for upserts."""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS raw_stock_prices (
                ticker TEXT NOT NULL,
                date DATE NOT NULL,
                open NUMERIC,
                high NUMERIC,
                low NUMERIC,
                close NUMERIC,
                volume BIGINT,
                loaded_at TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY (ticker, date)
            );
        """))
        conn.commit()


def upsert_prices(df, engine, batch_size=500):
    """Insert price rows, updating on conflict (ticker, date) — safe to rerun."""
    records = df.to_dict(orient="records")

    insert_sql = text("""
        INSERT INTO raw_stock_prices (ticker, date, open, high, low, close, volume)
        VALUES (:ticker, :date, :open, :high, :low, :close, :volume)
        ON CONFLICT (ticker, date)
        DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume,
            loaded_at = NOW();
    """)

    with engine.connect() as conn:
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            conn.execute(insert_sql, batch)
            conn.commit()
            print(f"Upserted rows {i} to {i + len(batch)}")


if __name__ == "__main__":
    import pandas as pd

    today = date.today().isoformat()
    df = pd.read_csv(f"data/raw/{today}/prices.csv")

    engine = get_engine()
    create_raw_table(engine)
    upsert_prices(df, engine)
    print("Done.")