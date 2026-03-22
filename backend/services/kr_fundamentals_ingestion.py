from __future__ import annotations

from typing import Any

from dartlab import Company


def _build_company_summary(company_name: str | None, fs_summary: Any, ratios: Any, bsns_year: str) -> str:
    safe_name = company_name or '이 종목'
    fs_count = len(fs_summary) if isinstance(fs_summary, list) else 0
    ratio_count = len(ratios) if isinstance(ratios, list) else 0

    bits = [f'{safe_name}의 {bsns_year} 사업연도 재무 보강 데이터야.']
    if fs_count:
        bits.append(f'재무 요약 {fs_count}건을 적재했어.')
    if ratio_count:
        bits.append(f'주요 비율 {ratio_count}건도 함께 확인했어.')
    if fs_count == 0 and ratio_count == 0:
        bits.append('공시 기반 상세 요약은 비어 있지만 회사 메타데이터는 확보했어.')
    return ' '.join(bits)


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
    company_name = getattr(company, "corpName", None)

    return {
        "corp_code": corp_code,
        "business_year": bsns_year,
        "reprt_code": reprt_code,
        "company_name": company_name,
        "filings": filings,
        "fs_summary": fs_summary,
        "raw_finance": raw_finance,
        "ratios": ratios,
        "summary": _build_company_summary(company_name, fs_summary, ratios, bsns_year),
    }
