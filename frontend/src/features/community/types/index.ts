export type BoardCategory = 'FREE' | 'COHORT' | 'PR' | 'POLL' | 'HOTDEAL';
export type ReactionType = 'LIKE' | 'DISLIKE';

export interface PrSummaryDto {
  status: string;
  resultStatus: string;
  totalVoteCount: number;
  deadlineAt: string;
}

export interface HotdealSummaryDto {
  dealPriceAmount: number;
  originalPriceAmount: number;
  storeName: string;
  expiredAt: string;
  isExpired: boolean;
}

export interface HotdealDetailResponseDto {
  postId: number;
  title: string;
  content: string;
  authorNickname: string;
  productName: string;
  storeName: string;
  dealPriceAmount: number;
  originalPriceAmount: number;
  dealUrl: string;
  shippingInfo: string;
  expiredAt: string;
  createdAt: string;
  updatedAt: string;
}

export interface PollSummaryDto {
  question: string;
  optionA: string;
  optionB: string;
  deadlineAt: string;
  isClosed: boolean;
  optionACount: number;
  optionBCount: number;
  totalVoteCount: number;
}

export interface PollDetailResponseDto {
  postId: number;
  title: string;
  content: string;
  authorNickname: string;
  question: string;
  optionA: string;
  optionB: string;
  deadlineAt: string;
  isClosed: boolean;
  optionACount: number;
  optionBCount: number;
  totalVoteCount: number;
  myVoteOption?: 'OPTION_A' | 'OPTION_B' | null;
  createdAt: string;
  updatedAt: string;
}

export interface PollVoteSubmitRequestDto {
  voteOption: 'OPTION_A' | 'OPTION_B';
}

export interface PollVoteSubmitResponseDto {
  postId: number;
  userId: number;
  voteOption: 'OPTION_A' | 'OPTION_B';
  optionACount: number;
  optionBCount: number;
  totalVoteCount: number;
  updatedAt: string;
}

export interface PostExtraSummaryDto {
  pr?: PrSummaryDto | null;
  hotdeal?: HotdealSummaryDto | null;
  poll?: PollSummaryDto | null;
}

export interface PostSummaryDto {
  postId: number;
  category: BoardCategory;
  generationNo: number | null;
  title: string;
  authorId: number;
  authorNickname: string;
  isMine: boolean;
  likeCount: number;
  commentCount: number;
  createdAt: string;
  extraSummary?: PostExtraSummaryDto | null;
}

export interface GetPostListResponseDto {
  content: PostSummaryDto[];
  page: number;
  size: number;
  totalElements: number;
  totalPages: number;
  hasNext: boolean;
}

export interface CreatePostRequestDto {
  category: BoardCategory;
  title: string;
  content: string;
  generationNo?: number;
}

export interface CreatePollPostRequestDto {
  title: string;
  content: string;
  question: string;
  optionA: string;
  optionB: string;
  deadlineAt: string;
}

export interface CreateHotdealPostRequestDto {
  title: string;
  content: string;
  productName: string;
  storeName?: string;
  dealPriceAmount: number;
  originalPriceAmount?: number;
  dealUrl?: string;
  shippingInfo?: string;
  expiredAt?: string;
}

export interface CreatePostResponseDto {
  postId: number;
  category: BoardCategory;
  generationNo: number | null;
  createdAt: string;
}

export interface GetPostResponseDto {
  postId: number;
  category: BoardCategory;
  generationNo: number | null;
  title: string;
  content: string;
  authorId: number;
  authorNickname: string;
  isMine: boolean;
  likeCount: number;
  dislikeCount: number;
  commentCount: number;
  createdAt: string;
  updatedAt: string;
  extraSummary?: PostExtraSummaryDto | null;
}

export interface CommentSummaryDto {
  commentId: number;
  parentCommentId: number | null;
  content: string;
  authorId: number;
  authorNickname: string;
  isMine: boolean;
  likeCount: number;
  createdAt: string;
}

export interface GetCommentListResponseDto {
  content: CommentSummaryDto[];
  page: number;
  size: number;
  totalElements: number;
  totalPages: number;
  hasNext: boolean;
}

export interface CreateCommentRequestDto {
  parentCommentId?: number | null;
  content: string;
}

export interface CreateCommentResponseDto {
  commentId: number;
  createdAt: string;
}

export interface UpdatePostRequestDto {
  title: string;
  content: string;
}

export interface UpdatePostResponseDto {
  postId: number;
  updatedAt: string;
}

export interface UpdateCommentRequestDto {
  content: string;
}

export interface UpdateCommentResponseDto {
  commentId: number;
  updatedAt: string;
}

export interface ToggleReactionRequestDto {
  targetType: 'POST' | 'COMMENT';
  targetId: number;
  reactionType: ReactionType;
  active: boolean;
}

export interface ToggleReactionResponseDto {
  targetType: 'POST' | 'COMMENT';
  targetId: number;
  reactionType: ReactionType;
  active: boolean;
  likeCount: number;
  dislikeCount: number;
}
