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
select
  symbol,
  coalesce(name, symbol) as name,
  market,
  sector,
  industry,
  lower(symbol || ' ' || coalesce(name, '')) as search_text
from public.ticker_universe;

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
)
select
  universe.symbol,
  coalesce(universe.name, universe.symbol) as name,
  universe.market,
  snapshot.snapshot_date,
  snapshot.close as price,
  snapshot.change_pct,
  snapshot.volume,
  snapshot.market_cap,
  snapshot.per,
  snapshot.pbr,
  coalesce(
    fundamentals.payload->>'aiSummary',
    fundamentals.payload->>'summary'
  ) as summary,
  case
    when snapshot.symbol is not null then 'snapshot'
    else null
  end as price_source
from public.ticker_universe as universe
left join latest_snapshot as snapshot
  on snapshot.symbol = universe.symbol
 and snapshot.row_num = 1
left join public.fundamentals_cache as fundamentals
  on fundamentals.symbol = universe.symbol;

grant select on public.v_home_summary to anon, authenticated;
grant select on public.v_stock_search to anon, authenticated;
grant select on public.v_stock_detail_latest to anon, authenticated;
