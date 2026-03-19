import axiosInstance from '@/shared/api/axiosInstance';
import type { ApiResponse } from '@/shared/types';
import type {
  GetPostListResponseDto,
  BoardCategory,
  CreatePostRequestDto,
  CreatePostResponseDto,
  GetPostResponseDto,
  GetCommentListResponseDto,
  CreateCommentRequestDto,
  CreateCommentResponseDto,
  UpdatePostRequestDto,
  UpdatePostResponseDto,
  UpdateCommentRequestDto,
  UpdateCommentResponseDto,
  ToggleReactionRequestDto,
  ToggleReactionResponseDto,
} from '../types';

export const getPosts = async (
  category?: BoardCategory | null,
  keyword?: string,
  page: number = 0,
  size: number = 15
): Promise<ApiResponse<GetPostListResponseDto>> => {
  return await axiosInstance.get('/community/posts', {
    params: {
      category: category || undefined,
      keyword,
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

export const getPost = async (postId: number): Promise<ApiResponse<GetPostResponseDto>> => {
  return await axiosInstance.get(`/community/posts/${postId}`);
};

export const updatePost = async (
  postId: number,
  data: UpdatePostRequestDto
): Promise<ApiResponse<UpdatePostResponseDto>> => {
  return await axiosInstance.patch(`/community/posts/${postId}`, data);
};

export const deletePost = async (postId: number): Promise<ApiResponse<void>> => {
  return await axiosInstance.delete(`/community/posts/${postId}`);
};

export const getComments = async (
  postId: number,
  page: number = 0,
  size: number = 20
): Promise<ApiResponse<GetCommentListResponseDto>> => {
  return await axiosInstance.get(`/community/posts/${postId}/comments`, {
    params: {
      page,
      size,
    },
  });
};

export const createComment = async (
  postId: number,
  data: CreateCommentRequestDto
): Promise<ApiResponse<CreateCommentResponseDto>> => {
  return await axiosInstance.post(`/community/posts/${postId}/comments`, data);
};

export const updateComment = async (
  commentId: number,
  data: UpdateCommentRequestDto
): Promise<ApiResponse<UpdateCommentResponseDto>> => {
  return await axiosInstance.patch(`/community/comments/${commentId}`, data);
};

export const deleteComment = async (commentId: number): Promise<ApiResponse<void>> => {
  return await axiosInstance.delete(`/community/comments/${commentId}`);
};

export const toggleReaction = async (
  data: ToggleReactionRequestDto
): Promise<ApiResponse<ToggleReactionResponseDto>> => {
  return await axiosInstance.post(`/community/reactions`, data);
};
