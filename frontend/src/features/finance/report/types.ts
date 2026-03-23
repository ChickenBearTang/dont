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
