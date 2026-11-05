export interface PrXaiMetricData {
  code: string;
  label: string;
  value: string;
}

export interface PrXaiSectionData {
  status: string;
  keyMetrics: PrXaiMetricData[];
}

export interface PrXaiTopFactorData {
  code: string;
  label: string;
  direction: string;
  /** 작성자가 아닌 사용자에게는 재무 요인의 영향도를 주지 않는다 (null). */
  impact: number | null;
}

export interface PrXaiEvidenceData {
  field: string;
  value: string;
  source: string;
  snapshotId?: string | null;
  isDefault: boolean;
  isEstimated: boolean;
  estimationMethod?: string | null;
}

export interface PrXaiCounterfactualData {
  label: string;
  targetDecision: string;
  validated: boolean;
}

export interface PrXaiConfidenceData {
  decisionConfidence: number;
  dataCompleteness: number;
  explanationFidelity: number;
}

export interface PrXaiRuntimeEnginesData {
  decision: string;
  explanation: string;
  shap: string;
  dice: string;
}

export interface PrXaiEvaluationResponseData {
  requestId: string;
  purchaseRequestId: number;
  decision: 'BUY_NOW' | 'WAIT' | 'REVIEW' | 'NOT_RECOMMENDED' | string;
  summary: string;
  financialEvaluation: PrXaiSectionData;
  priceEvaluation: PrXaiSectionData;
  topFactors: PrXaiTopFactorData[];
  supportingEvidence: PrXaiEvidenceData[];
  counterfactuals: PrXaiCounterfactualData[];
  warnings: string[];
  confidence: PrXaiConfidenceData;
  runtimeEngines: PrXaiRuntimeEnginesData;
  generatedAt: string;
  schemaVersion: string;
  modelVersion?: string | null;
  ruleVersion?: string | null;
  /**
   * true 면 PR 작성자가 아닌 사용자에게 내려온 응답이라 작성자의 잔액·소득·지출 금액이 빠져 있다.
   * (재무 지표, 반사실, 재무 근거, 재무 요인의 영향도, 재무 경고)
   */
  financialDetailsHidden?: boolean;
}

export interface PrXaiAvailabilityResponseData {
  enabled: boolean;
  reason: string;
  matchType?: 'URL_EXACT' | 'TITLE_PRICE_SIMILAR' | 'ITEM_WHITELIST_ONLY' | string | null;
  matchedItemTitle?: string | null;
  matchedItemUrl?: string | null;
}
