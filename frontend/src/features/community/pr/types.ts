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
