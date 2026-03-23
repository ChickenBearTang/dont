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
  status: 'ACTIVE' | 'DELETED' | 'BLINDED';
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
  itemName: string;
  priceAmount: number | null;
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

export interface PollCreateRequestDto {
  title: string;
  content: string;
  question: string;
  optionA: string;
  optionB: string;
  deadlineAt: string;
}

export interface PollCreateResponseDto {
  postId: number;
  createdAt: string;
}

export interface PollDetailResponseDto {
  postId: number;
  title: string;
  content: string;
  authorNickname: string;
  question: string;
  optionA: string;
  optionB: string;
  deadlineAt: string | null;
  isClosed: boolean;
  optionACount: number;
  optionBCount: number;
  totalVoteCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface PollUpdateRequestDto {
  title: string;
  content: string;
  question: string;
  optionA: string;
  optionB: string;
  deadlineAt: string;
}

export interface PollUpdateResponseDto {
  postId: number;
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

export interface HotdealCreateRequestDto {
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

export interface HotdealCreateResponseDto {
  postId: number;
  createdAt: string;
}

export interface HotdealDetailResponseDto {
  postId: number;
  title: string;
  content: string;
  authorNickname: string;
  productName: string;
  storeName: string | null;
  dealPriceAmount: number;
  originalPriceAmount: number | null;
  dealUrl: string | null;
  shippingInfo: string | null;
  expiredAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface HotdealUpdateRequestDto {
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

export interface HotdealUpdateResponseDto {
  postId: number;
  updatedAt: string;
}

export interface PostSummaryDto {
  postId: number;
  category: BoardCategory;
  generationNo: number | null;
  title: string;
  status: 'ACTIVE' | 'DELETED' | 'BLINDED';
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
  status: 'ACTIVE' | 'DELETED' | 'BLINDED';
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

export type ReportTargetType = 'POST' | 'COMMENT';

export type ReportReasonCode = 'SPAM' | 'ABUSE' | 'INAPPROPRIATE' | 'SCAM' | 'PRIVACY' | 'OTHER';

export interface ReportCreateRequestDto {
  targetType: ReportTargetType;
  targetId: number;
  reasonCode: ReportReasonCode;
  detailText?: string;
}

export interface ReportCreateResponseDto {
  reportId: number;
  reportStatus: string;
  createdAt: string;
}
export interface AdminReportSummaryDto {
  reportId: number;
  reporterUserId: number;
  targetType: 'POST' | 'COMMENT';
  targetId: number;
  reasonCode: string;
  reportStatus: 'RECEIVED' | 'BLINDED' | 'REJECTED';
  createdAt: string;
  processedAt: string | null;
}

export interface AdminReportListResponseDto {
  content: AdminReportSummaryDto[];
  page: number;
  size: number;
  totalElements: number;
  totalPages: number;
  hasNext: boolean;
}

export interface AdminReportDetailResponseDto {
  reportId: number;
  reporterUserId: number;
  targetType: 'POST' | 'COMMENT';
  targetId: number;
  reasonCode: string;
  detailText: string;
  reportStatus: 'RECEIVED' | 'BLINDED' | 'REJECTED';
  processedByUserId: number | null;
  processNote: string | null;
  processedAt: string | null;
  createdAt: string;
  updatedAt: string;
  targetAuthorNickname: string;
  targetTitle: string | null;
  targetContent: string;
  targetStatus: string;
  postId: number | null;
}

export interface ReportProcessRequestDto {
  processNote: string;
}

export interface ReportProcessResponseDto {
  reportId: number;
  status: 'RECEIVED' | 'BLINDED' | 'REJECTED';
  processedAt: string;
}
