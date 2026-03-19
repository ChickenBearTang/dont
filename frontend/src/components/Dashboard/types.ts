export interface User {
  user_id: number;
  name: string;
}

export interface SummaryData {
  selected_month: string;
  previous_month: string;
  current_total_spend: number;
  previous_total_spend: number;
  difference_amount: number;
  difference_text: string;
}

export interface DailyCumulative {
  day: number;
  current_cumulative_amount: number;
  previous_cumulative_amount: number;
}

export interface TrendData {
  average_amount: number;
  months: { month: string; total_card_spend: number; is_selected_month: boolean }[];
}

export interface CategoryData {
  category_display: string;
  amount: number;
  delta_amount: number;
  share_percent: number;
}

export interface AiAnalysis {
  consumption_patterns: string[];
  anomaly_explanations: string[];
  actionable_solutions: string[];
}

export interface RecommendationPayload {
  error?: string;
  user_persona?: {
    type_id: string;
    nickname: string;
    description: string;
  };
  best_card?: {
    card_id: number;
    name: string;
    estimated_savings: number;
    picking_rate: number;
    comment: string;
  };
  all_cards?: {
    card_id: number;
    name: string;
    main_text: string;
    sub_text: string[];
    estimated_savings: number;
    picking_rate: number;
    comment: string;
  }[];
}

export interface DashboardPayload {
  meta: {
    user_name: string;
    selected_month: string;
    period: { start: string; end: string; };
    llm_status: string;
  };
  period_summary: SummaryData;
  daily_cumulative: DailyCumulative[];
  six_month_trend: TrendData;
  category_breakdown: CategoryData[];
  ai_analysis?: AiAnalysis;
}

export interface ChatMessage {
  role: "user" | "model" | "ai";
  text: string;
}
