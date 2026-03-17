export type BoardCategory = 'FREE' | 'COHORT' | 'PR' | 'POLL' | 'HOTDEAL';

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
  authorNickname: string;
  likeCount: number;
  commentCount: number;
  createdAt: string;
  extra?: PostExtraSummaryDto | null;
}

export interface GetPostListResponseDto {
  content: PostSummaryDto[];
  pageNumber: number;
  pageSize: number;
  totalElements: number;
  totalPages: number;
  hasNext: boolean;
}

export interface CreatePostRequestDto {
  category: BoardCategory;
  title: string;
  content: string;
}

export interface CreatePostResponseDto {
  postId: number;
  category: BoardCategory;
  generationNo: number | null;
  createdAt: string;
}
