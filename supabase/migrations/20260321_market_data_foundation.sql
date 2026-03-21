create table if not exists ticker_universe (
  symbol text not null,
  market text not null,
  name text,
  sector text,
  industry text,
  updated_at timestamptz not null default now(),
  primary key (symbol, market)
);

create table if not exists market_snapshot_daily (
  symbol text not null,
  market text not null,
  snapshot_date date not null,
  close numeric,
  change_pct numeric,
  market_cap numeric,
  volume bigint,
  per numeric,
  pbr numeric,
  payload jsonb not null default '{}'::jsonb,
  fetched_at timestamptz not null default now(),
  primary key (symbol, snapshot_date)
);

create table if not exists fundamentals_cache (
  symbol text primary key,
  payload jsonb not null default '{}'::jsonb,
  fetched_at timestamptz not null default now()
);

create table if not exists market_summary_cache (
  cache_key text primary key,
  payload jsonb not null default '{}'::jsonb,
  fetched_at timestamptz not null default now()
);

create index if not exists idx_market_snapshot_daily_market_date
  on market_snapshot_daily (market, snapshot_date desc);

create index if not exists idx_market_snapshot_daily_market_cap
  on market_snapshot_daily (snapshot_date desc, market_cap desc);
