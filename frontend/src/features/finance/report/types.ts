export interface SpendingSummaryRank {
  categoryName: string;
  percentage: number;
  amount: number;
  amount_prv: number;
}

export interface SpendingSummaryResponse {
  success: boolean;
  code: string;
  message: string;
  totalAmount: number;
  rankColumList: SpendingSummaryRank[];
  aiReport?: {
    ai_analysis: {
      consumption_patterns: string[];
      anomaly_explanations: string[];
      actionable_solutions: string[];
      llm_advice?: string;
    };
    anomaly_transactions: {
      id: number;
      merchant_name: string;
      transaction_amount: number;
      justification?: string;
    }[];
  };
}

export interface AiReportJustification {
  id: number;
  message: string;
  createdAt: number[];
  aiResponse: string;
}

export interface AiReportPayload {
  cardRecommendation: CardRecommendationResponse | Record<string, never>;
  justifications: AiReportJustification[];
  meta: {
    analysisStatus: 'OK' | 'DEGRADED' | 'SKIPPED';
    recommendationStatus: 'OK' | 'FAILED';
    recommendationReused: boolean;
    transactionFingerprint: string;
  };
  base?: {
    userId: number;
    reportMonth: string;
    topCategory: {
      amount: number;
      percentage: number;
      categoryName: string;
    };
    totalAmount: number;
    categorySummary: {
      amount: number;
      percentage: number;
      categoryName: string;
    }[];
  };
  aiAnalysis: {
    actionable_solutions: string[];
    anomaly_explanations: string[];
    consumption_patterns: string[];
  };
}

export interface AiReportData {
  id: number;
  reportMonth: string;
  versionNo: number;
  latest: boolean;
  llmStatus: string;
  reportStatus: string;
  generationSource: string;
  generatedAt: string;
  reportPayload: AiReportPayload;
}

export interface AiReportResponse {
  success: boolean;
  code: string;
  message: string;
  data: AiReportData;
  timestamp: string;
}

export interface Persona {
  type_id: string;
  name?: string;
  nickname?: string;
  description: string;
  total_amount: number;
  count: number;
  score: number;
}

export interface CardResult {
  card_id: string | number;
  name: string;
  main_text: string;
  sub_text: string[];
  structured_benefits?: {
    target_type: string;
    type?: string;
    rate: number;
  }[];
  estimated_savings: number;
  picking_rate: number;
  comment: string;
}

export interface CardRecommendationResponse {
  user_persona: Persona;
  best_card: CardResult;
  all_cards: CardResult[];
  total_spend: number;
  type_spend_stats?: Record<string, number>;
}

export interface CohortComparisonData {
  cohort: number;
  avg_save_box: number;
  avg_food: number;
  avg_cafe: number;
  avg_culture: number;
  avg_market: number;
  avg_medical: number;
}

export interface CohortComparisonResponse {
  success: boolean;
  code: string;
  message: string;
  data: CohortComparisonData;
  timestamp: string;
}
