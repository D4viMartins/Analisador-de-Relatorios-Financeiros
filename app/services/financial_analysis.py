from __future__ import annotations

import re
from dataclasses import dataclass

from app.models.analysis import (
    AnalyzeResponse,
    CompareResponse,
    DocumentSnapshot,
    FinancialIndicators,
    FinancialMetrics,
    IndicatorValue,
    MetricDelta,
    MetricValue,
)
from app.services.document_store import get_document_metadata

LABEL_PATTERNS: dict[str, list[str]] = {
    "revenue": [
        r"receita\s+líquida",
        r"receita\s+liquida",
        r"receita\s+bruta",
        r"faturamento",
        r"vendas\s+líquidas",
        r"vendas\s+liquidas",
        r"\breceita\b",
    ],
    "ebitda": [
        r"\bebitda\b",
        r"lucro\s+antes\s+de\s+juros,?\s*impostos,?\s*deprecia[cç][aã]o\s+e\s+amortiza[cç][aã]o",
    ],
    "profit": [
        r"lucro\s+líquido",
        r"lucro\s+liquido",
        r"resultado\s+líquido",
        r"net\s+income",
        r"\blucro\b",
    ],
    "debt": [
        r"d[ií]vida\s+líquida",
        r"d[ií]vida\s+bruta",
        r"endividamento",
        r"passivo\s+financeiro",
        r"passivo\s+oneroso",
    ],
}

VALUE_PATTERN = re.compile(r"(?:R\$\s*)?(-?\d{1,3}(?:\.\d{3})+(?:,\d+)?|-?\d+(?:,\d+)?)")
PERCENT_PATTERN = re.compile(r"(-?\d+(?:[.,]\d+)?)\s*%")


@dataclass
class ParsedMetric:
    value: float | None
    source: str | None


def _normalize_number(raw_value: str) -> float:
    cleaned = raw_value.replace(".", "").replace("R$", "").replace(" ", "").replace(",", ".")
    return float(cleaned)


def _extract_numbers(text: str) -> list[float]:
    values: list[float] = []
    for match in VALUE_PATTERN.finditer(text):
        try:
            number = _normalize_number(match.group(1))
            if 1900 <= number <= 2100 and float(number).is_integer():
                continue
            values.append(number)
        except ValueError:
            continue
    return values


def _extract_percent(text: str) -> float | None:
    match = PERCENT_PATTERN.search(text)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", "."))
    except ValueError:
        return None


def _match_metric(text: str, patterns: list[str]) -> ParsedMetric:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        lines = [text.strip()]

    compiled = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]

    for index, line in enumerate(lines):
        for pattern in compiled:
            match = pattern.search(line)
            if not match:
                continue

            window = " ".join(lines[index : min(index + 3, len(lines))])
            tail = " ".join([line[match.end() :]] + lines[index + 1 : min(index + 3, len(lines))])
            numbers = _extract_numbers(tail)
            if numbers:
                return ParsedMetric(value=numbers[0], source=window)

            numbers = _extract_numbers(window)
            if numbers:
                return ParsedMetric(value=numbers[0], source=window)

    for line in lines:
        if any(pattern.search(line) for pattern in compiled):
            numbers = _extract_numbers(line)
            if numbers:
                return ParsedMetric(value=numbers[0], source=line)

    return ParsedMetric(value=None, source=None)


def _extract_yoy_growth(text: str) -> ParsedMetric:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        lines = [text.strip()]

    growth_keywords = re.compile(r"(cresc|aument|alta|varia|subiu|expand|recu|queda|comparad|ano anterior|yoy)", re.IGNORECASE)

    for line in lines:
        if not growth_keywords.search(line):
            continue
        percent = _extract_percent(line)
        if percent is not None:
            return ParsedMetric(value=percent, source=line)

    for index, line in enumerate(lines):
        if not re.search(r"receita|faturamento|vendas", line, re.IGNORECASE):
            continue
        window = " ".join(lines[index : min(index + 3, len(lines))])
        numbers = _extract_numbers(window)
        if len(numbers) >= 2 and numbers[1] != 0:
            growth = ((numbers[0] - numbers[1]) / numbers[1]) * 100
            return ParsedMetric(value=round(growth, 2), source=window)

    return ParsedMetric(value=None, source=None)


def _build_metric_value(parsed: ParsedMetric) -> MetricValue:
    return MetricValue(value=parsed.value, source=parsed.source)


def _safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return round(numerator / denominator, 4)


def _safe_margin(profit: float | None, revenue: float | None) -> float | None:
    ratio = _safe_ratio(profit, revenue)
    return None if ratio is None else round(ratio * 100, 2)


def _build_snapshot(document_id: str, filename: str, text: str) -> tuple[DocumentSnapshot, list[str]]:
    revenue = _match_metric(text, LABEL_PATTERNS["revenue"])
    ebitda = _match_metric(text, LABEL_PATTERNS["ebitda"])
    profit = _match_metric(text, LABEL_PATTERNS["profit"])
    debt = _match_metric(text, LABEL_PATTERNS["debt"])
    yoy_growth = _extract_yoy_growth(text)

    metrics = FinancialMetrics(
        revenue=_build_metric_value(revenue),
        ebitda=_build_metric_value(ebitda),
        profit=_build_metric_value(profit),
        debt=_build_metric_value(debt),
    )

    indicators = FinancialIndicators(
        leverage=IndicatorValue(
            value=_safe_ratio(debt.value, ebitda.value),
            unit="x",
            source="Dívida / EBITDA" if debt.value is not None and ebitda.value is not None else None,
        ),
        net_margin=IndicatorValue(
            value=_safe_margin(profit.value, revenue.value),
            unit="percent",
            source="Lucro líquido / Receita líquida" if profit.value is not None and revenue.value is not None else None,
        ),
        yoy_growth=IndicatorValue(
            value=yoy_growth.value,
            unit="percent",
            source=yoy_growth.source,
        ),
    )

    notes: list[str] = []
    for metric_name, metric in (
        ("receita", revenue),
        ("EBITDA", ebitda),
        ("lucro", profit),
        ("dívida", debt),
    ):
        if metric.value is None:
            notes.append(f"Não foi possível extrair {metric_name} de forma confiável.")

    snapshot = DocumentSnapshot(
        document_id=document_id,
        filename=filename,
        metrics=metrics,
        indicators=indicators,
    )
    return snapshot, notes


def analyze_document(document_id: str) -> AnalyzeResponse:
    metadata = get_document_metadata(document_id)
    if metadata is None:
        raise ValueError("Documento não encontrado.")

    snapshot, notes = _build_snapshot(metadata["document_id"], metadata["filename"], metadata["text"])
    return AnalyzeResponse(**snapshot.model_dump(), notes=notes)


def compare_documents(document_id_a: str, document_id_b: str) -> CompareResponse:
    metadata_a = get_document_metadata(document_id_a)
    metadata_b = get_document_metadata(document_id_b)
    if metadata_a is None or metadata_b is None:
        raise ValueError("Um ou mais documentos não foram encontrados.")

    snapshot_a, notes_a = _build_snapshot(metadata_a["document_id"], metadata_a["filename"], metadata_a["text"])
    snapshot_b, notes_b = _build_snapshot(metadata_b["document_id"], metadata_b["filename"], metadata_b["text"])

    deltas: list[MetricDelta] = []
    for metric_name in ("revenue", "ebitda", "profit", "debt"):
        value_a = getattr(snapshot_a.metrics, metric_name).value
        value_b = getattr(snapshot_b.metrics, metric_name).value
        absolute_change = None if value_a is None or value_b is None else round(value_b - value_a, 2)
        percentage_change = None
        if value_a not in (None, 0) and value_b is not None:
            percentage_change = round(((value_b - value_a) / value_a) * 100, 2)

        deltas.append(
            MetricDelta(
                metric=metric_name,
                document_a_value=value_a,
                document_b_value=value_b,
                absolute_change=absolute_change,
                percentage_change=percentage_change,
            )
        )

    summary_parts = [
        f"{snapshot_a.filename} vs {snapshot_b.filename}",
        f"receita: {snapshot_a.metrics.revenue.value} -> {snapshot_b.metrics.revenue.value}",
        f"lucro: {snapshot_a.metrics.profit.value} -> {snapshot_b.metrics.profit.value}",
    ]
    if notes_a or notes_b:
        summary_parts.append("algumas métricas não foram extraídas com total confiança.")

    return CompareResponse(
        document_a=snapshot_a,
        document_b=snapshot_b,
        deltas=deltas,
        summary=" ".join(summary_parts),
    )
