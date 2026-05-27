from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    document_id: str = Field(..., min_length=1, description="Identificador do documento a ser analisado")


class CompareRequest(BaseModel):
    document_id_a: str = Field(..., min_length=1, description="Identificador do primeiro documento")
    document_id_b: str = Field(..., min_length=1, description="Identificador do segundo documento")


class MetricValue(BaseModel):
    value: float | None = Field(default=None, description="Valor numérico extraído")
    currency: str = Field(default="BRL", description="Moeda de referência")
    source: str | None = Field(default=None, description="Trecho do texto de onde o valor foi extraído")


class IndicatorValue(BaseModel):
    value: float | None = Field(default=None, description="Valor do indicador")
    unit: str = Field(default="ratio", description="Unidade do indicador")
    source: str | None = Field(default=None, description="Trecho do texto ou regra usada para calcular")


class FinancialMetrics(BaseModel):
    revenue: MetricValue
    ebitda: MetricValue
    profit: MetricValue
    debt: MetricValue


class FinancialIndicators(BaseModel):
    leverage: IndicatorValue
    net_margin: IndicatorValue
    yoy_growth: IndicatorValue


class DocumentSnapshot(BaseModel):
    document_id: str = Field(..., description="Identificador do documento")
    filename: str = Field(..., description="Nome original do arquivo")
    metrics: FinancialMetrics
    indicators: FinancialIndicators


class AnalyzeResponse(DocumentSnapshot):
    notes: list[str] = Field(default_factory=list, description="Observações sobre a extração e cálculo")


class MetricDelta(BaseModel):
    metric: str = Field(..., description="Nome da métrica comparada")
    document_a_value: float | None = Field(default=None, description="Valor no primeiro documento")
    document_b_value: float | None = Field(default=None, description="Valor no segundo documento")
    absolute_change: float | None = Field(default=None, description="Diferença absoluta entre os valores")
    percentage_change: float | None = Field(default=None, description="Diferença percentual entre os valores")


class CompareResponse(BaseModel):
    document_a: DocumentSnapshot
    document_b: DocumentSnapshot
    deltas: list[MetricDelta] = Field(default_factory=list, description="Diferenças entre as métricas comparadas")
    summary: str = Field(..., description="Resumo textual da comparação")
