import axiosInstance from '@/shared/api/axiosInstance';
import type { ApiResponse } from '@/shared/types';
import type {
  GetPostListResponseDto,
  BoardCategory,
  CreatePostRequestDto,
  CreatePostResponseDto,
  GetPostResponseDto,
  PollCreateRequestDto,
  PollCreateResponseDto,
  PollDetailResponseDto,
  PollUpdateRequestDto,
  PollUpdateResponseDto,
  PollVoteSubmitRequestDto,
  PollVoteSubmitResponseDto,
  HotdealCreateRequestDto,
  HotdealCreateResponseDto,
  HotdealDetailResponseDto,
  HotdealUpdateRequestDto,
  HotdealUpdateResponseDto,
  GetCommentListResponseDto,
  GetCommentReplyListResponseDto,
  CreateCommentRequestDto,
  CreateCommentResponseDto,
  UpdatePostRequestDto,
  UpdatePostResponseDto,
  UpdateCommentRequestDto,
  UpdateCommentResponseDto,
  ToggleReactionRequestDto,
  ToggleReactionResponseDto,
  ReportCreateRequestDto,
  ReportCreateResponseDto,
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

export const createPoll = async (
  data: PollCreateRequestDto
): Promise<ApiResponse<PollCreateResponseDto>> => {
  return await axiosInstance.post('/community/polls', data);
};

export const getPollDetail = async (postId: number): Promise<ApiResponse<PollDetailResponseDto>> => {
  return await axiosInstance.get(`/community/polls/${postId}`);
};

export const updatePoll = async (
  postId: number,
  data: PollUpdateRequestDto
): Promise<ApiResponse<PollUpdateResponseDto>> => {
  return await axiosInstance.patch(`/community/polls/${postId}`, data);
};

export const submitPollVote = async (
  postId: number,
  data: PollVoteSubmitRequestDto
): Promise<ApiResponse<PollVoteSubmitResponseDto>> => {
  return await axiosInstance.post(`/community/polls/${postId}/votes`, data);
};

export const createHotdeal = async (
  data: HotdealCreateRequestDto
): Promise<ApiResponse<HotdealCreateResponseDto>> => {
  return await axiosInstance.post('/community/hotdeals', data);
};

export const getHotdealDetail = async (
  postId: number
): Promise<ApiResponse<HotdealDetailResponseDto>> => {
  return await axiosInstance.get(`/community/hotdeals/${postId}`);
};

export const updateHotdeal = async (
  postId: number,
  data: HotdealUpdateRequestDto
): Promise<ApiResponse<HotdealUpdateResponseDto>> => {
  return await axiosInstance.patch(`/community/hotdeals/${postId}`, data);
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

export const getCommentReplies = async (
  postId: number,
  commentId: number,
  page: number = 0,
  size: number = 10
): Promise<ApiResponse<GetCommentReplyListResponseDto>> => {
  return await axiosInstance.get(`/community/posts/${postId}/comments/${commentId}/replies`, {
    params: {
      page,
      size,
    },
  });
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

export const createReport = async (
  data: ReportCreateRequestDto
): Promise<ApiResponse<ReportCreateResponseDto>> => {
  return await axiosInstance.post('/community/reports', data);
};
