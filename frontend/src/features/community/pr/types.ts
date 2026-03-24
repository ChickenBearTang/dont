import type { PostAttachmentDto, PostAttachmentRequestDto } from '@/features/community/types';

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
  deadlineAt?: string;
  attachments?: PostAttachmentRequestDto[];
}

export interface PrCreateResponseData {
  postId: number;
  resultStatus: PrStatus;
  deadlineAt: string | null;
}

export interface PrDetailResponseData {
  postId: number;
  title: string;
  authorId: number;
  authorNickname: string;
  authorProfileImageUrl?: string | null;
  itemName: string;
  priceAmount: number;
  category: string | null;
  content: string;
  purchaseUrl: string | null;
  deadlineAt: string | null;
  status: PrStatus;
  resultStatus: string | null;
  attachments: PostAttachmentDto[];
  createdAt: string;
  updatedAt: string;
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
