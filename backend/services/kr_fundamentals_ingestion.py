from __future__ import annotations

from typing import Any

from dartlab import Company


def _to_serializable(value: Any) -> Any:
    if value is None:
        return None
    if callable(value):
        try:
            value = value()
        except Exception:
            return None
    if hasattr(value, "to_dict"):
        try:
            return value.to_dict(as_series=False)
        except TypeError:
            try:
                return value.to_dict(orient="records")
            except TypeError:
                return value.to_dict()
    if hasattr(value, "__dict__"):
        return {
            key: _to_serializable(raw)
            for key, raw in vars(value).items()
            if not key.startswith("_")
        }
    return value


def collect_kr_fundamentals(corp_code: str, bsns_year: str, reprt_code: str = "11011") -> dict[str, Any]:
    company = Company(corp_code)

    filings = _to_serializable(getattr(company, "filings", None))
    fs_summary = _to_serializable(getattr(company, "fsSummary", None))
    raw_finance = _to_serializable(getattr(company, "rawFinance", None))
    ratios = _to_serializable(getattr(company, "ratios", None))

    return {
        "corp_code": corp_code,
        "business_year": bsns_year,
        "reprt_code": reprt_code,
        "company_name": getattr(company, "corpName", None),
        "filings": filings,
        "fs_summary": fs_summary,
        "raw_finance": raw_finance,
        "ratios": ratios,
    }
