select
    ticker,
    date,
    open,
    high,
    low,
    close,
    volume
from {{ source('raw', 'raw_stock_prices') }}