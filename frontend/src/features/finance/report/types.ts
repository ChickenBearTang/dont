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
