import axiosInstance from '@/shared/api/axiosInstance';
import type { ApiResponse } from '@/shared/types';
import type {
  GetPostListResponseDto,
  BoardCategory,
  CreatePostRequestDto,
  CreatePostResponseDto,
  CreatePollPostRequestDto,
  CreateHotdealPostRequestDto,
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
  PollDetailResponseDto,
  PollVoteSubmitRequestDto,
  PollVoteSubmitResponseDto,
  HotdealDetailResponseDto,
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

export const createPollPost = async (
  data: CreatePollPostRequestDto
): Promise<ApiResponse<CreatePostResponseDto>> => {
  return await axiosInstance.post('/community/polls', data);
};

export const createHotdealPost = async (
  data: CreateHotdealPostRequestDto
): Promise<ApiResponse<CreatePostResponseDto>> => {
  return await axiosInstance.post('/community/hotdeals', data);
};

export const getPost = async (postId: number): Promise<ApiResponse<GetPostResponseDto>> => {
  return await axiosInstance.get(`/community/posts/${postId}`);
};

export const getPollDetail = async (
  postId: number
): Promise<ApiResponse<PollDetailResponseDto>> => {
  return await axiosInstance.get(`/community/polls/${postId}`);
};

export const submitPollVote = async (
  postId: number,
  data: PollVoteSubmitRequestDto
): Promise<ApiResponse<PollVoteSubmitResponseDto>> => {
  return await axiosInstance.post(`/community/polls/${postId}/votes`, data);
};

export const getHotdealDetail = async (
  postId: number
): Promise<ApiResponse<HotdealDetailResponseDto>> => {
  return await axiosInstance.get(`/community/hotdeals/${postId}`);
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
