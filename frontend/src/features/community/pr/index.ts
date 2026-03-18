import axiosInstance from '@/shared/api/axiosInstance';
import type { ApiResponse } from '@/shared/types';
import type {
  PrCloseRequestPayload,
  PrCloseResponseData,
  PrCreateRequestPayload,
  PrCreateResponseData,
  PrDetailResponseData,
  PrVoteSubmitRequestPayload,
  PrVoteSubmitResponseData,
} from '@/features/community/pr/types';

const PR_BASE_PATH = '/community/purchase-requests';

export const createPr = async (
  payload: PrCreateRequestPayload
): Promise<ApiResponse<PrCreateResponseData>> => {
  return await axiosInstance.post(PR_BASE_PATH, payload);
};

export const getPrDetail = async (postId: number): Promise<ApiResponse<PrDetailResponseData>> => {
  return await axiosInstance.get(`${PR_BASE_PATH}/${postId}`);
};

export const submitPrVote = async (
  postId: number,
  payload: PrVoteSubmitRequestPayload
): Promise<ApiResponse<PrVoteSubmitResponseData>> => {
  return await axiosInstance.post(`${PR_BASE_PATH}/${postId}/votes`, payload);
};

export const closePr = async (
  postId: number,
  payload: PrCloseRequestPayload
): Promise<ApiResponse<PrCloseResponseData>> => {
  return await axiosInstance.post(`${PR_BASE_PATH}/${postId}/close`, payload);
};

export type {
  PrCloseRequestPayload,
  PrCloseResponseData,
  PrCloseTargetStatus,
  PrCreateRequestPayload,
  PrCreateResponseData,
  PrDetailResponseData,
  PrStatus,
  PrVoteSubmitRequestPayload,
  PrVoteSubmitResponseData,
  PrVoteValue,
} from '@/features/community/pr/types';

export * from '@/features/community/pr/pages/PrDetailPage';
export * from '@/features/community/pr/pages/PrCreatePage';
