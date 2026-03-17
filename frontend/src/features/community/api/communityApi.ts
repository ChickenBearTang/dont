import axiosInstance from '@/shared/api/axiosInstance';
import type { ApiResponse } from '@/shared/types';
import type {
  GetPostListResponseDto,
  BoardCategory,
  CreatePostRequestDto,
  CreatePostResponseDto,
} from '../types';

export const getPosts = async (
  category?: BoardCategory | null,
  generationNo?: number,
  page: number = 0,
  size: number = 15
): Promise<ApiResponse<GetPostListResponseDto>> => {
  return await axiosInstance.get('/community/posts', {
    params: {
      category: category || undefined,
      generationNo,
      page,
      size,
    },
  });
};

export const createPost = async (
  data: CreatePostRequestDto
): Promise<ApiResponse<CreatePostResponseDto>> => {
  return await axiosInstance.post('/community/posts', data);
};
