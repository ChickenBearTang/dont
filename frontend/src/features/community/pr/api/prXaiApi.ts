import axiosInstance from '@/shared/api/axiosInstance';
import type { ApiResponse } from '@/shared/types';
import type { PrXaiEvaluationResponseData } from '@/features/community/pr/xaiTypes';

export const getPrXaiEvaluation = async (
  postId: number
): Promise<ApiResponse<PrXaiEvaluationResponseData>> => {
  return await axiosInstance.get(`/community/purchase-requests/${postId}/xai-evaluation`);
};
