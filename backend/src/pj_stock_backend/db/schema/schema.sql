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
