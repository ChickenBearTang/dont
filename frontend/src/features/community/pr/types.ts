export type PrVoteValue = 'AGREE' | 'DISAGREE';

export type PrStatus = 'OPEN' | 'MERGED' | 'CLOSED';

export type PrCloseTargetStatus = 'MERGED' | 'CLOSED';

export interface PrCreateRequestPayload {
  title: string;
  content: string;
  itemName: string;
  priceAmount: number;
  category?: string;
  purchaseUrl?: string;
  imageUrl?: string;
  deadlineAt?: string;
}

export interface PrCreateResponseData {
  postId: number;
  resultStatus: string;
  deadlineAt: string;
}

export interface PrDetailResponseData {
  postId: number;
  itemName: string;
  priceAmount: number;
  category: string | null;
  content: string;
  purchaseUrl: string | null;
  imageUrl: string | null;
  status: PrStatus;
  resultStatus: string | null;
  agreeCount: number;
  disagreeCount: number;
  totalVoteCount: number;
  closedAt: string | null;
  reviews?: PrDetailReviewItem[];
  events?: PrDetailEventItem[];
  permissions?: PrDetailPermissions;
}

export interface PrDetailReviewItem {
  reviewId: number;
  userId: number;
  userNickname?: string | null;
  userProfileImageUrl?: string | null;
  decision: 'APPROVE' | 'REQUEST_CHANGES' | 'COMMENT' | string;
  content: string | null;
  createdAt: string;
}

export interface PrDetailEventItem {
  eventId: number;
  eventType: 'CREATED' | 'REVIEW_SUBMITTED' | 'STATUS_CHANGED' | string;
  actorUserId: number | null;
  actorNickname?: string | null;
  actorProfileImageUrl?: string | null;
  payload: Record<string, unknown> | null;
  createdAt: string;
}

export interface PrDetailPermissions {
  canVote: boolean;
  canClose: boolean;
  voteDisabledReason?: string | null;
  closeDisabledReason?: string | null;
}

export interface PrVoteSubmitRequestPayload {
  voteValue: PrVoteValue;
  opinionText?: string;
}

export interface PrVoteSubmitResponseData {
  postId: number;
  userId: number;
  voteValue: PrVoteValue;
  opinionText: string | null;
  votedAt: string;
}

export interface PrCloseRequestPayload {
  resultStatus: PrCloseTargetStatus;
}

export interface PrCloseResponseData {
  postId: number;
  status: PrStatus;
  resultStatus: PrCloseTargetStatus;
  agreeCount: number;
  disagreeCount: number;
  totalVoteCount: number;
  closedAt: string;
}
