create table if not exists stocks (
    id integer primary key autoincrement,
    stock_code text not null unique,
    stock_name text not null,
    market text not null,
    security_group text,
    sector text,
    listed_date text,
    listed_shares integer,
    is_active integer not null default 1,
    last_synced_at text not null default current_timestamp,
    created_at text not null default current_timestamp,
    updated_at text not null default current_timestamp
);

create table if not exists daily_prices (
    id integer primary key autoincrement,
    trade_date text not null,
    stock_code text not null,
    stock_name text not null,
    market text not null,
    section text,
    open_price integer not null,
    high_price integer not null,
    low_price integer not null,
    close_price integer not null,
    price_change integer not null,
    change_rate real not null,
    volume integer not null,
    trading_value integer not null,
    market_cap integer not null,
    listed_shares integer not null,
    last_synced_at text not null default current_timestamp,
    created_at text not null default current_timestamp,
    updated_at text not null default current_timestamp,
    unique (trade_date, stock_code)
);

create index if not exists idx_daily_prices_stock_code_trade_date
on daily_prices (stock_code, trade_date);

create index if not exists idx_daily_prices_trade_date
on daily_prices (trade_date);
