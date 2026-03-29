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
  impact: number;
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
}

export interface PrXaiAvailabilityResponseData {
  enabled: boolean;
  reason: string;
  matchType?: 'URL_EXACT' | 'TITLE_PRICE_SIMILAR' | 'ITEM_WHITELIST_ONLY' | string | null;
  matchedItemTitle?: string | null;
  matchedItemUrl?: string | null;
}
