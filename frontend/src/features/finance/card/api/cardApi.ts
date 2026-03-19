import axiosInstance from '@/shared/api/axiosInstance';

import type { GetCardsResponse, CardDetailDto, GetCardTransactionsResponse } from '../types';

export const getMyCards = async (): Promise<GetCardsResponse> => {
  return await axiosInstance.get('/fin/cards');
};

export const getCard = async (
  cardId: string,
  startDate: string,
  endDate: string
): Promise<CardDetailDto> => {
  return await axiosInstance.get(`/fin/cards/${cardId}`, {
    params: { startDate, endDate },
  });
};

export const getCardTransactions = async (
  cardId: string,
  startDate: string,
  endDate: string
): Promise<GetCardTransactionsResponse> => {
  return await axiosInstance.get(`/fin/cards/${cardId}/transactions`, {
    params: { startDate, endDate },
  });
};
