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
}

export interface AiReportJustification {
  id: number;
  message: string;
  createdAt: number[];
  aiResponse: string;
}

export interface AiReportPayload {
  base: {
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
