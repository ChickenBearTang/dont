export type BoardCategory = 'FREE' | 'COHORT' | 'PR' | 'POLL' | 'HOTDEAL';

export type ReactionType = 'LIKE' | 'DISLIKE';

export interface CreatePostRequestDto {
  category: BoardCategory;
  generationNo?: number;
  title: string;
  content: string;
}

export interface CreatePostResponseDto {
  postId: number;
  category: string;
  generationNo: number | null;
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
}

export interface PrSummaryDto {
  status: string;
  resultStatus: string;
  totalVoteCount: number | null;
  deadlineAt: string | null;
}

export interface HotdealSummaryDto {
  dealPriceAmount: number | null;
  originalPriceAmount: number | null;
  storeName: string | null;
  expiredAt: string | null;
  isExpired: boolean | null;
}

export interface PollSummaryDto {
  question: string;
  optionA: string;
  optionB: string;
  deadlineAt: string | null;
  isClosed: boolean;
  optionACount: number;
  optionBCount: number;
  totalVoteCount: number;
}

export interface PostExtraSummaryDto {
  pr: PrSummaryDto | null;
  hotdeal: HotdealSummaryDto | null;
  poll: PollSummaryDto | null;
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
  dislikeCount: number;
  commentCount: number;
  createdAt: string;
  extraSummary: PostExtraSummaryDto | null;
}

export interface GetPostListResponseDto {
  content: PostSummaryDto[];
  page: number;
  size: number;
  totalElements: number;
  totalPages: number;
  hasNext: boolean;
}

export interface CreateCommentRequestDto {
  content: string;
  parentCommentId?: number | null;
}

export interface CreateCommentResponseDto {
  commentId: number;
  postId: number;
  parentCommentId: number | null;
  content: string;
  createdAt: string;
}

export interface UpdateCommentRequestDto {
  content: string;
}

export interface UpdateCommentResponseDto {
  commentId: number;
  updatedAt: string;
}

export interface CommentSummaryDto {
  commentId: number;
  parentCommentId: number | null;
  authorId: number;
  authorNickname: string;
  content: string;
  likeCount: number;
  dislikeCount: number;
  isMine: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface GetCommentListResponseDto {
  content: CommentSummaryDto[];
  page: number;
  size: number;
  totalElements: number;
  totalPages: number;
  hasNext: boolean;
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
