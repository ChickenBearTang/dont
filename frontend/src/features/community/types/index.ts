export type BoardCategory = 'FREE' | 'COHORT' | 'PR' | 'POLL' | 'HOTDEAL';

export type ReactionType = 'LIKE' | 'DISLIKE';

export interface PostAttachmentRequestDto {
  key: string;
  fileName: string;
  contentType: string;
  fileSize: number;
}

export interface PostAttachmentDto {
  attachmentId?: number;
  fileName: string;
  contentType: string;
  fileSize: number;
  fileUrl: string;
  key?: string;
}

export interface AttachmentPresignFileRequestDto {
  fileName: string;
  contentType: string;
  contentLength: number;
}

export interface AttachmentPresignFileResponseDto {
  uploadUrl: string;
  method: 'PUT';
  headers: Record<string, string>;
  key: string;
  expiresAt: string;
  fileUrl: string;
}

export interface AttachmentPresignResponseDto {
  files: AttachmentPresignFileResponseDto[];
}

export interface CreatePostRequestDto {
  category: BoardCategory;
  generationNo?: number;
  title: string;
  content: string;
  attachments?: PostAttachmentRequestDto[];
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
  attachments?: PostAttachmentRequestDto[];
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
  authorProfileImageUrl?: string | null;
  isMine: boolean;
  likeCount: number;
  dislikeCount: number;
  commentCount: number;
  attachments: PostAttachmentDto[];
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
  attachments?: PostAttachmentRequestDto[];
}

export interface PollCreateResponseDto {
  postId: number;
  createdAt: string;
}

export interface PollDetailResponseDto {
  postId: number;
  title: string;
  content: string;
  authorId: number;
  authorNickname: string;
  authorProfileImageUrl?: string | null;
  question: string;
  optionA: string;
  optionB: string;
  deadlineAt: string | null;
  isClosed: boolean;
  optionACount: number;
  optionBCount: number;
  totalVoteCount: number;
  attachments: PostAttachmentDto[];
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
  attachments?: PostAttachmentRequestDto[];
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
  attachments?: PostAttachmentRequestDto[];
}

export interface HotdealCreateResponseDto {
  postId: number;
  createdAt: string;
}

export interface HotdealDetailResponseDto {
  postId: number;
  title: string;
  content: string;
  authorId: number;
  authorNickname: string;
  authorProfileImageUrl?: string | null;
  productName: string;
  storeName: string | null;
  dealPriceAmount: number;
  originalPriceAmount: number | null;
  dealUrl: string | null;
  shippingInfo: string | null;
  expiredAt: string | null;
  attachments: PostAttachmentDto[];
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
  attachments?: PostAttachmentRequestDto[];
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
  authorProfileImageUrl?: string | null;
  isMine: boolean;
  likeCount: number;
  dislikeCount: number;
  commentCount: number;
  attachmentCount: number;
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

export interface CommentReplyDto {
  commentId: number;
  parentCommentId: number | null;
  replyToCommentId: number | null;
  replyToNickname: string | null;
  depth: number;
  authorId: number;
  authorNickname: string;
  authorProfileImageUrl?: string | null;
  content: string;
  status: 'ACTIVE' | 'DELETED' | 'BLINDED';
  likeCount: number;
  isMine: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CommentThreadDto {
  commentId: number;
  parentCommentId: number | null;
  authorId: number;
  authorNickname: string;
  authorProfileImageUrl?: string | null;
  content: string;
  status: 'ACTIVE' | 'DELETED' | 'BLINDED';
  likeCount: number;
  isMine: boolean;
  createdAt: string;
  updatedAt: string;
  replyCount: number;
  replies: CommentReplyDto[];
}

export interface GetCommentListResponseDto {
  content: CommentThreadDto[];
  page: number;
  size: number;
  totalElements: number;
  totalPages: number;
  hasNext: boolean;
}

export interface GetCommentReplyListResponseDto {
  content: CommentReplyDto[];
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
