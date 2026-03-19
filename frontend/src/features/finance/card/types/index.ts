export interface CardDto {
  cardIssuerName: string;
  cardName: string;
  monthlyCardExpense: number;
}

export interface GetCardsResponse {
  success: boolean;
  code: string;
  message: string;
  cards: CardDto[];
}

export interface TransactionDto {
  id: string;
  date: string;
  merchant: string;
  amount: number;
  category: string;
  type: 'PAYMENT' | 'REFUND';
}
