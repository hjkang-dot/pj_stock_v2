create table if not exists stocks (
    id integer primary key autoincrement,
    base_date text not null,
    stock_code text not null,
    stock_name text not null,
    market text not null,
    security_group text,
    sector text,
    listed_date text,
    listed_shares integer,
    created_at text not null default current_timestamp,
    updated_at text not null default current_timestamp,
    unique (base_date, stock_code, market)
);

