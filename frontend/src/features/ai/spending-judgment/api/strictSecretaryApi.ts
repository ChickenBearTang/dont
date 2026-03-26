import axiosInstance from '@/shared/api/axiosInstance';
import type { AIResultData } from '@/components/StrictSecretaryResult';

type AnyRecord = Record<string, unknown>;

const isAIResultData = (value: unknown): value is AIResultData => {
  if (!value || typeof value !== 'object') return false;
  const v = value as Record<string, unknown>;
  const approved = v.is_approved ?? v._approved;
  return (
    typeof approved === 'boolean' &&
    typeof v.fact_violence_comment === 'string' &&
    Array.isArray(v.reasoning)
  );
};

const normalizeAIResultData = (value: unknown): AIResultData | null => {
  if (!value || typeof value !== 'object') return null;

  const v = value as AnyRecord;
  const approvedCandidate = v.is_approved ?? v._approved ?? v.isApproved ?? v.approved;
  const commentCandidate =
    v.fact_violence_comment ?? v.factViolenceComment ?? v.comment ?? v.message;
  const reasoningCandidate = v.reasoning ?? v.reasons ?? v.reasonings;

  const isApproved =
    typeof approvedCandidate === 'boolean'
      ? approvedCandidate
      : approvedCandidate === 'true'
        ? true
        : approvedCandidate === 'false'
          ? false
          : null;

  const factComment =
    typeof commentCandidate === 'string' ? commentCandidate : String(commentCandidate ?? '');

  const reasoning = Array.isArray(reasoningCandidate)
    ? reasoningCandidate.map((item) => String(item))
    : typeof reasoningCandidate === 'string' && reasoningCandidate.trim().length > 0
      ? [reasoningCandidate]
      : [];

  if (isApproved === null || factComment.length === 0) {
    return null;
  }

  return {
    is_approved: isApproved,
    fact_violence_comment: factComment,
    reasoning,
  };
};

const toObject = (value: unknown): AnyRecord | null => {
  if (!value) return null;
  if (typeof value === 'object') return value as AnyRecord;
  if (typeof value === 'string') {
    try {
      const parsed = JSON.parse(value);
      if (parsed && typeof parsed === 'object') {
        return parsed as AnyRecord;
      }
    } catch {
      return null;
    }
  }
  return null;
};

const pickCandidate = (payload: unknown): unknown[] => {
  const obj = toObject(payload);
  if (!obj) return [payload];

  return [
    obj,
    obj.data,
    toObject(obj.data)?.data,
    obj.result,
    obj.payload,
    toObject(obj.data)?.result,
    toObject(obj.data)?.payload,
  ];
};

export const evaluatePurchase = async (data: {
  item_text: string;
  item_link: string;
  user_reason: string;
}): Promise<AIResultData> => {
  try {
    const response: unknown = await axiosInstance.post('/fin/strict-secretary/evaluate', data, {
      timeout: 45000,
    });

    const candidates = pickCandidate(response);
    for (const candidate of candidates) {
      if (isAIResultData(candidate)) {
        console.info('[strict-secretary] resolved response shape: exact');
        return candidate;
      }
      const normalized = normalizeAIResultData(candidate);
      if (normalized) {
        console.info('[strict-secretary] resolved response shape: normalized', normalized);
        return normalized;
      }
    }

    console.error('[strict-secretary] raw unexpected payload:', response);
    throw new Error('Unexpected strict-secretary response shape');
  } catch (error: any) {
    console.error('[strict-secretary] evaluate error detail:', {
      message: error?.message,
      status: error?.response?.status,
      data: error?.response?.data,
    });
    throw error;
  }
};

export const getTtsAudio = async (text: string): Promise<string> => {
  const blob: any = await axiosInstance.post(
    '/fin/strict-secretary/tts',
    { text },
    { responseType: 'blob' }
  );
  return URL.createObjectURL(blob);
};
