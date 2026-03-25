import axiosInstance from '@/shared/api/axiosInstance';
import type { AIResultData } from '@/components/StrictSecretaryResult';

export const evaluatePurchase = async (data: {
  item_text: string;
  item_link: string;
  user_reason: string;
}): Promise<AIResultData> => {
  const response: any = await axiosInstance.post('/fin/strict-secretary/evaluate', data);
  return response.data;
};

export const getTtsAudio = async (text: string): Promise<string> => {
  const blob: any = await axiosInstance.post(
    '/fin/strict-secretary/tts',
    { text },
    { responseType: 'blob' }
  );
  return URL.createObjectURL(blob);
};
