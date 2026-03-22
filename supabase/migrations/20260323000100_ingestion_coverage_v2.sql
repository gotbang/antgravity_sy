alter table public.ticker_universe
  add column if not exists coverage_tier text not null default 'cold',
  add column if not exists coverage_rank integer,
  add column if not exists refresh_bucket integer,
  add column if not exists is_exact_refresh_enabled boolean not null default true,
  add column if not exists primary_provider text;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'ticker_universe_coverage_tier_check'
  ) then
    alter table public.ticker_universe
      add constraint ticker_universe_coverage_tier_check
      check (coverage_tier in ('hot', 'warm', 'cold'));
  end if;
end
$$;

create table if not exists public.symbol_ingestion_state (
  symbol text not null,
  market text not null,
  coverage_tier text not null check (coverage_tier in ('hot', 'warm', 'cold')),
  refresh_bucket integer,
  freshness_status text not null default 'missing' check (freshness_status in ('fresh', 'stale', 'missing')),
  last_attempted_at timestamptz,
  last_succeeded_at timestamptz,
  last_snapshot_at timestamptz,
  last_price numeric,
  last_price_source text,
  last_error_code text,
  last_error_message text,
  consecutive_failures integer not null default 0,
  updated_at timestamptz not null default now(),
  primary key (symbol, market)
);

create table if not exists public.symbol_ingestion_failure_log (
  id bigint generated always as identity primary key,
  run_id text not null,
  symbol text not null,
  market text not null,
  phase text not null,
  provider text,
  result text not null check (result in ('success', 'failure', 'skipped')),
  error_code text,
  error_message text,
  attempted_at timestamptz not null default now()
);

create table if not exists public.symbol_refresh_requests (
  symbol text primary key,
  market text,
  requested_by text not null default 'ops',
  priority integer not null default 100,
  status text not null default 'queued' check (status in ('queued', 'running', 'done', 'failed')),
  requested_at timestamptz not null default now(),
  started_at timestamptz,
  completed_at timestamptz,
  last_error_code text
);

create index if not exists idx_ticker_universe_market_coverage_rank
  on public.ticker_universe (market, coverage_tier, coverage_rank);

create index if not exists idx_symbol_ingestion_state_tier_bucket
  on public.symbol_ingestion_state (market, coverage_tier, refresh_bucket);

create index if not exists idx_symbol_refresh_requests_status_priority
  on public.symbol_refresh_requests (status, priority, requested_at);

drop view if exists public.v_stock_detail_latest;
drop view if exists public.v_stock_search;

create or replace view public.v_stock_search as
with latest_snapshot as (
  select
    symbol,
    fetched_at,
    close,
    row_number() over (partition by symbol order by snapshot_date desc) as row_num
  from public.market_snapshot_daily
)
select
  universe.symbol,
  coalesce(universe.name, universe.symbol) as name,
  universe.market,
  universe.sector,
  universe.industry,
  lower(universe.symbol) as symbol_normalized,
  lower(coalesce(universe.name, '')) as name_normalized,
  lower(universe.symbol || ' ' || coalesce(universe.name, '')) as search_text,
  case
    when snapshot.close is not null then 'live'
    when nullif(fundamentals.payload->>'price', '') is not null then 'fallback'
    else 'missing'
  end as price_status,
  case
    when snapshot.close is not null then 'snapshot'
    when nullif(fundamentals.payload->>'price', '') is not null then 'cache_fallback'
    else 'unavailable'
  end as price_source,
  coalesce(universe.coverage_tier, state.coverage_tier, 'cold') as coverage_tier,
  coalesce(
    state.freshness_status,
    case
      when coalesce(snapshot.close, nullif(fundamentals.payload->>'price', '')::numeric) is null then 'missing'
      when snapshot.fetched_at is not null and snapshot.fetched_at >= now() - interval '20 hours' then 'fresh'
      else 'stale'
    end
  ) as freshness_status,
  state.last_succeeded_at as last_succeeded_at,
  state.last_snapshot_at as last_snapshot_at
from public.ticker_universe as universe
left join latest_snapshot as snapshot
  on snapshot.symbol = universe.symbol
 and snapshot.row_num = 1
left join public.fundamentals_cache as fundamentals
  on fundamentals.symbol = universe.symbol
left join public.symbol_ingestion_state as state
  on state.symbol = universe.symbol
 and state.market = universe.market;

create or replace view public.v_stock_detail_latest as
with latest_snapshot as (
  select
    symbol,
    market,
    snapshot_date,
    fetched_at,
    close,
    change_pct,
    market_cap,
    volume,
    per,
    pbr,
    row_number() over (partition by symbol order by snapshot_date desc) as row_num
  from public.market_snapshot_daily
),
home_summary as (
  select payload
  from public.market_summary_cache
  where cache_key = 'home'
  limit 1
)
select
  universe.symbol,
  coalesce(universe.name, universe.symbol) as name,
  universe.market,
  coalesce(
    snapshot.snapshot_date,
    nullif(fundamentals.payload->>'snapshot_date', '')::date
  ) as snapshot_date,
  coalesce(
    snapshot.close,
    nullif(fundamentals.payload->>'price', '')::numeric
  ) as price,
  coalesce(
    snapshot.change_pct,
    nullif(fundamentals.payload->>'change_pct', '')::numeric
  ) as change_pct,
  coalesce(
    snapshot.volume,
    nullif(fundamentals.payload->>'volume', '')::bigint
  ) as volume,
  coalesce(
    snapshot.market_cap,
    nullif(fundamentals.payload->>'market_cap', '')::numeric
  ) as market_cap,
  coalesce(
    snapshot.per,
    nullif(fundamentals.payload->>'per', '')::numeric
  ) as per,
  coalesce(
    snapshot.pbr,
    nullif(fundamentals.payload->>'pbr', '')::numeric
  ) as pbr,
  coalesce(
    fundamentals.payload->>'aiSummary',
    fundamentals.payload->>'summary'
  ) as summary,
  case
    when snapshot.close is not null then 'live'
    when nullif(fundamentals.payload->>'price', '') is not null then 'fallback'
    else 'missing'
  end as price_status,
  case
    when snapshot.close is not null then 'snapshot'
    when nullif(fundamentals.payload->>'price', '') is not null then 'cache_fallback'
    else 'unavailable'
  end as price_source,
  coalesce(
    nullif(fundamentals.payload->>'safe_activity_radius_pct', '')::numeric,
    greatest(
      1.5,
      least(
        6.0,
        5.0
        + case
            when coalesce((home_summary.payload->>'fearGreedIndex')::numeric, 50) <= 30
              or coalesce((home_summary.payload->>'fearGreedIndex')::numeric, 50) >= 70 then -1.5
            when coalesce((home_summary.payload->>'fearGreedIndex')::numeric, 50) <= 40
              or coalesce((home_summary.payload->>'fearGreedIndex')::numeric, 50) >= 60 then -0.8
            else 0.2
          end
        + case
            when abs(coalesce(snapshot.change_pct, nullif(fundamentals.payload->>'change_pct', '')::numeric, 0)) >= 7 then -2.0
            when abs(coalesce(snapshot.change_pct, nullif(fundamentals.payload->>'change_pct', '')::numeric, 0)) >= 4 then -1.2
            when abs(coalesce(snapshot.change_pct, nullif(fundamentals.payload->>'change_pct', '')::numeric, 0)) >= 2 then -0.5
            else 0.3
          end
        + case
            when universe.market = 'US'
             and coalesce(snapshot.volume, nullif(fundamentals.payload->>'volume', '')::bigint, 999999999) < 50000 then -0.5
            when universe.market = 'KR'
             and coalesce(snapshot.volume, nullif(fundamentals.payload->>'volume', '')::bigint, 999999999) < 100000 then -0.5
            else 0
          end
      )
    )
  ) as safe_activity_radius_pct,
  coalesce(
    fundamentals.payload->>'safe_activity_level',
    case
      when coalesce(nullif(fundamentals.payload->>'safe_activity_radius_pct', '')::numeric, 5.0) >= 4.5 then 'safe'
      when coalesce(nullif(fundamentals.payload->>'safe_activity_radius_pct', '')::numeric, 5.0) >= 3.0 then 'caution'
      else 'danger'
    end
  ) as safe_activity_level,
  coalesce(
    fundamentals.payload->>'safe_activity_label',
    '반경 계산 데이터가 아직 없어. 기본 경계로 탐색해줘.'
  ) as safe_activity_label,
  coalesce(universe.coverage_tier, state.coverage_tier, 'cold') as coverage_tier,
  coalesce(
    state.freshness_status,
    case
      when coalesce(snapshot.close, nullif(fundamentals.payload->>'price', '')::numeric) is null then 'missing'
      when snapshot.fetched_at is not null and snapshot.fetched_at >= now() - interval '20 hours' then 'fresh'
      else 'stale'
    end
  ) as freshness_status,
  state.last_succeeded_at as last_succeeded_at,
  state.last_attempted_at as last_attempted_at,
  case
    when snapshot.fetched_at is null then null
    else round(extract(epoch from (now() - snapshot.fetched_at)) / 3600.0, 2)
  end as stale_age_hours
from public.ticker_universe as universe
left join latest_snapshot as snapshot
  on snapshot.symbol = universe.symbol
 and snapshot.row_num = 1
left join public.fundamentals_cache as fundamentals
  on fundamentals.symbol = universe.symbol
left join public.symbol_ingestion_state as state
  on state.symbol = universe.symbol
 and state.market = universe.market
left join home_summary on true;
