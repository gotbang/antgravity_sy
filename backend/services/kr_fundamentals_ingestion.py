from __future__ import annotations

from typing import Any

from dartlab import SearchResults, fs_single_account

from core.config import settings


def collect_kr_fundamentals(corp_code: str, bsns_year: str, reprt_code: str = "11011") -> dict[str, Any]:
    # dartlab helper wrapper; 실패는 상위에서 처리
    disclosures = SearchResults(api_key=settings.DART_API_KEY).search(corp_code=corp_code)
    financials = fs_single_account(api_key=settings.DART_API_KEY, corp_code=corp_code, bsns_year=bsns_year, reprt_code=reprt_code)
    return {
        "corp_code": corp_code,
        "business_year": bsns_year,
        "reprt_code": reprt_code,
        "disclosures": disclosures.to_dict() if hasattr(disclosures, "to_dict") else [],
        "financials": financials.to_dict(orient="records") if hasattr(financials, "to_dict") else [],
    }
