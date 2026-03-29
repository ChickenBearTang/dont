from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class ProvenanceValue(BaseModel):
    value: str | int | float | None = None
    source: str
    snapshot_id: str | None = Field(default=None, alias="snapshotId")
    is_default: bool = Field(default=False, alias="isDefault")
    is_estimated: bool = Field(default=False, alias="isEstimated")
    estimation_method: str | None = Field(default=None, alias="estimationMethod")

    model_config = {"populate_by_name": True}


class PurchaseContext(BaseModel):
    post_id: int = Field(alias="postId")
    title: str
    item_name: str = Field(alias="itemName")
    content: str
    category: str | None = None
    purchase_url: str | None = Field(default=None, alias="purchaseUrl")
    price_amount: ProvenanceValue = Field(alias="priceAmount")

    model_config = {"populate_by_name": True}


class FinanceProfileContext(BaseModel):
    current_balance: ProvenanceValue = Field(alias="currentBalance")
    emergency_fund_balance: ProvenanceValue = Field(alias="emergencyFundBalance")
    expected_card_payment_amount: ProvenanceValue = Field(
        alias="expectedCardPaymentAmount"
    )
    days_until_card_due: ProvenanceValue = Field(alias="daysUntilCardDue")
    savebox_balance: ProvenanceValue | None = Field(
        default=None,
        alias="saveboxBalance",
    )
    available_fixed_expense: ProvenanceValue | None = Field(
        default=None,
        alias="availableFixedExpense",
    )
    available_fixed_income: ProvenanceValue | None = Field(
        default=None,
        alias="availableFixedIncome",
    )

    model_config = {"populate_by_name": True}


class RecentTransactionContext(BaseModel):
    transaction_date: str = Field(alias="transactionDate")
    transaction_time: str = Field(alias="transactionTime")
    merchant_name: str = Field(alias="merchantName")
    category_name: str = Field(alias="categoryName")
    transaction_amount: int = Field(alias="transactionAmount")

    model_config = {"populate_by_name": True}


class PurchaseXaiEvaluationRequest(BaseModel):
    request_id: str = Field(alias="requestId")
    schema_version: str = Field(alias="schemaVersion")
    context_version: str = Field(alias="contextVersion")
    purchase: PurchaseContext
    finance_profile: FinanceProfileContext = Field(alias="financeProfile")
    recent_transactions: list[RecentTransactionContext] = Field(
        default_factory=list, alias="recentTransactions"
    )

    model_config = {"populate_by_name": True}


class EvaluationMetric(BaseModel):
    code: str
    label: str
    value: str


class EvaluationSection(BaseModel):
    status: str
    key_metrics: list[EvaluationMetric] = Field(
        default_factory=list, alias="keyMetrics"
    )

    model_config = {"populate_by_name": True}


class TopFactor(BaseModel):
    code: str
    label: str
    direction: str
    impact: float


class SupportingEvidence(BaseModel):
    field: str
    value: str
    source: str
    snapshot_id: str | None = Field(default=None, alias="snapshotId")
    is_default: bool = Field(default=False, alias="isDefault")
    is_estimated: bool = Field(default=False, alias="isEstimated")
    estimation_method: str | None = Field(default=None, alias="estimationMethod")

    model_config = {"populate_by_name": True}


class Counterfactual(BaseModel):
    label: str
    target_decision: str = Field(alias="targetDecision")
    validated: bool

    model_config = {"populate_by_name": True}


class ConfidenceSection(BaseModel):
    decision_confidence: float = Field(alias="decisionConfidence")
    data_completeness: float = Field(alias="dataCompleteness")
    explanation_fidelity: float = Field(alias="explanationFidelity")

    model_config = {"populate_by_name": True}


class RuntimeEngines(BaseModel):
    decision: str
    explanation: str
    shap: str
    dice: str
    price_model: str = Field(default="disabled", alias="priceModel")
    finance_model: str = Field(default="disabled", alias="financeModel")

    model_config = {"populate_by_name": True}


class PurchaseXaiEvaluationResponse(BaseModel):
    request_id: str = Field(alias="requestId")
    purchase_request_id: int = Field(alias="purchaseRequestId")
    decision: str
    summary: str
    financial_evaluation: EvaluationSection = Field(alias="financialEvaluation")
    price_evaluation: EvaluationSection = Field(alias="priceEvaluation")
    top_factors: list[TopFactor] = Field(default_factory=list, alias="topFactors")
    supporting_evidence: list[SupportingEvidence] = Field(
        default_factory=list, alias="supportingEvidence"
    )
    counterfactuals: list[Counterfactual] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence: ConfidenceSection
    runtime_engines: RuntimeEngines = Field(alias="runtimeEngines")
    generated_at: datetime = Field(alias="generatedAt")
    schema_version: str = Field(alias="schemaVersion")
    model_version: str | None = Field(default=None, alias="modelVersion")
    rule_version: str | None = Field(default=None, alias="ruleVersion")

    model_config = {"populate_by_name": True}
