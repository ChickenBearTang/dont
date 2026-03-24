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
  cardRecommendation?: CardRecommendationResponse;
  justifications: AiReportJustification[];
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
  name: string;
  description: string;
  total_amount: number;
  count: number;
  score: number;
}

export interface CardResult {
  card_id: number;
  name: string;
  main_text: string;
  sub_text: string[];
  estimated_savings: number;
  picking_rate: number;
  comment: string;
}

export interface CardRecommendationResponse {
  user_persona: Persona;
  best_card: CardResult;
  all_cards: CardResult[];
  total_spend: number;
}
