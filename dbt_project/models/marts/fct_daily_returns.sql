with prices as (
    select * from {{ ref('stg_stock_prices') }}
),

with_returns as (
    select
        ticker,
        date,
        open,
        high,
        low,
        close,
        volume,
        lag(close) over (partition by ticker order by date) as prev_close
    from prices
)

select
    ticker,
    date,
    open,
    high,
    low,
    close,
    volume,
    prev_close,
    round(((close - prev_close) / prev_close) * 100, 2) as daily_return_pct,
    round(avg(close) over (
        partition by ticker
        order by date
        rows between 6 preceding and current row
    ), 2) as rolling_7day_avg_close
from with_returns