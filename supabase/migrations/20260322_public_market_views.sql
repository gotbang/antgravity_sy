alter table if exists public.ticker_universe enable row level security;
alter table if exists public.market_snapshot_daily enable row level security;
alter table if exists public.fundamentals_cache enable row level security;
alter table if exists public.market_summary_cache enable row level security;

revoke all on table public.ticker_universe from anon, authenticated;
revoke all on table public.market_snapshot_daily from anon, authenticated;
revoke all on table public.fundamentals_cache from anon, authenticated;
revoke all on table public.market_summary_cache from anon, authenticated;

create or replace view public.v_home_summary as
select
  fetched_at as updated_at,
  coalesce(payload->>'marketMood', '중립') as market_mood,
  coalesce((payload->>'fearGreedIndex')::integer, 50) as fear_greed_index,
  coalesce((payload->>'advancers')::integer, 0) as advancers,
  coalesce((payload->>'decliners')::integer, 0) as decliners,
  coalesce((payload->'sentimentMix'->>'positive')::numeric, 0) as positive_ratio,
  coalesce((payload->'sentimentMix'->>'negative')::numeric, 0) as negative_ratio,
  coalesce(payload->>'aiSummary', '시장 요약 데이터가 아직 없어.') as ai_summary
from public.market_summary_cache
where cache_key = 'home';

create or replace view public.v_stock_search as
with latest_snapshot as (
  select
    symbol,
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
  end as price_source
from public.ticker_universe as universe
left join latest_snapshot as snapshot
  on snapshot.symbol = universe.symbol
 and snapshot.row_num = 1
left join public.fundamentals_cache as fundamentals
  on fundamentals.symbol = universe.symbol;

create or replace view public.v_stock_detail_latest as
with latest_snapshot as (
  select
    symbol,
    market,
    snapshot_date,
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
  ) as safe_activity_label
from public.ticker_universe as universe
left join latest_snapshot as snapshot
  on snapshot.symbol = universe.symbol
 and snapshot.row_num = 1
left join public.fundamentals_cache as fundamentals
  on fundamentals.symbol = universe.symbol
left join home_summary on true;

grant select on public.v_home_summary to anon, authenticated;
grant select on public.v_stock_search to anon, authenticated;
grant select on public.v_stock_detail_latest to anon, authenticated;
