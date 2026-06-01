create table if not exists stocks (
    id integer primary key autoincrement,
    stock_code text not null unique,
    stock_name text not null,
    market text not null,
    security_group text,
    sector text,
    dart_corp_code text,
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

create table if not exists company_financials (
    id integer primary key autoincrement,
    corp_code text not null,
    stock_code text,
    bsns_year integer not null,
    fs_div text,
    fs_nm text,
    currency text,
    fiscal_period text not null,
    current_assets real,
    non_current_assets real,
    total_assets real,
    current_liabilities real,
    non_current_liabilities real,
    total_liabilities real,
    total_equity real,
    revenue real,
    operating_income real,
    net_income real,
    debt_ratio real,
    current_ratio real,
    equity_ratio real,
    operating_margin real,
    net_margin real,
    par_value real,
    eps real,
    cash_dividend_yield real,
    cash_dividend_per_share real,
    cash_dividend_total real,
    cash_dividend_payout_ratio real,
    created_at text not null default current_timestamp,
    updated_at text not null default current_timestamp,
    unique (corp_code, fiscal_period)
);

create index if not exists idx_company_financials_corp_code_fiscal_period
on company_financials (corp_code, fiscal_period);

create index if not exists idx_company_financials_stock_code
on company_financials (stock_code);

create table if not exists market_closed_dates (
    trade_date text primary key,
    created_at text not null default current_timestamp
);

create table if not exists stock_evaluations (
    id integer primary key autoincrement,
    stock_code text not null,
    business_year integer not null,
    base_date text not null,
    close_price integer,
    market_cap integer,
    net_income real,
    total_equity real,
    debt_ratio real,
    roe real,
    per real,
    pbr real,
    dividend_yield real,
    cash_dividend_per_share real,
    payout_ratio real,
    dividend_years integer,
    dividend_decrease_count integer,
    current_ratio real,
    revenue_growth real,
    operating_income_growth real,
    eps_growth real,
    financial_stability_score real,
    growth_score real,
    undervaluation_score real,
    shareholder_return_score real,
    market_governance_score real,
    total_score real,
    is_candidate integer,
    created_at text not null default current_timestamp,
    updated_at text not null default current_timestamp,
    unique (stock_code, business_year, base_date)
);

create index if not exists idx_stock_evaluations_stock_code
on stock_evaluations (stock_code);

create table if not exists ud_portfolio_status (
    id integer primary key autoincrement,
    initial_balance real not null,
    current_cash real not null,
    current_valuation real not null,
    total_asset real not null,
    mdd real not null default 0.0,
    total_return real not null default 0.0,
    win_rate real not null default 0.0,
    updated_at text not null default current_timestamp
);

create table if not exists ud_portfolio_holdings (
    id integer primary key autoincrement,
    stock_code text not null,
    stock_name text not null,
    entry_date text not null,
    entry_price real not null,
    quantity integer not null,
    current_price real not null,
    valuation real not null,
    holding_return real not null,
    score_at_entry real,
    exit_date text,
    exit_price real,
    score_at_exit real,
    status text not null default 'ACTIVE',
    updated_at text not null default current_timestamp
);

create table if not exists ud_portfolio_history (
    trade_date text primary key,
    cash real not null,
    valuation real not null,
    total_asset real not null,
    daily_return real not null,
    drawdown real not null default 0.0,
    updated_at text not null default current_timestamp
);

create table if not exists ud_portfolio_transactions (
    id integer primary key autoincrement,
    trade_date text not null,
    stock_code text not null,
    stock_name text not null,
    transaction_type text not null, -- 'BUY' or 'SELL'
    price real not null,
    quantity integer not null,
    amount real not null,
    score real,
    created_at text not null default current_timestamp
);
