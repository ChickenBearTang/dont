export interface CardDto {
  id: number;
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

export interface CardDetailDto {
  cardIssuerName: string;
  cardName: string;
  monthlyCardExpense: number;
}

export interface TransactionItemDto {
  categoryName: string;
  merchantName: string;
  transactionDate: string;
  transactionTime: string;
  transactionAmount: string;
}

export interface GetCardTransactionsResponse {
  success: boolean;
  code: string;
  message: string;
  cardName: string;
  cardNo: string;
  transaction: TransactionItemDto[];
}
