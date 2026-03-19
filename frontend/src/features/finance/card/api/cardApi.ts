import axiosInstance from '@/shared/api/axiosInstance';
import type { ApiResponse } from '@/shared/types';
import type { CardDto, GetCardsResponse, TransactionDto } from '../types';

export const getMyCards = async (): Promise<GetCardsResponse> => {
  return await axiosInstance.get('/fin/cards');
};

export const getCard = async (cardName: string): Promise<ApiResponse<CardDto>> => {
  return await axiosInstance.get(`/fin/cards/${cardName}`);
};

export const getCardTransactions = async (
  cardName: string
): Promise<ApiResponse<TransactionDto[]>> => {
  return await axiosInstance.get(`/fin/cards/${cardName}/transactions`);
};
