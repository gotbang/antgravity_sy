from pathlib import Path


API_CLIENT_PATH = Path(__file__).resolve().parents[2] / 'src' / 'lib' / 'apiClient.ts'


def test_legacy_read_helpers_remain_available_for_rollback_contract():
    source = API_CLIENT_PATH.read_text(encoding='utf-8')

    assert 'export async function fetchMarketSummary' in source
    assert 'export async function fetchStockSearch' in source
    assert 'export async function fetchStockDetail' in source
    assert 'export async function fetchTrending' in source
