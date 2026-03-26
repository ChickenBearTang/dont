import { useRef, useState } from 'react';
import StrictSecretaryForm from '@/components/StrictSecretaryForm';
import StrictSecretaryLanding from '@/components/StrictSecretaryLanding';
import StrictSecretaryResult, { type AIResultData } from '@/components/StrictSecretaryResult';
import { evaluatePurchase, getTtsAudio } from '@/features/ai/spending-judgment/api/strictSecretaryApi';
import PRImage from '@/assets/PR.png';
import './StrictSecretaryModal.css';

type PageState = 'IDLE' | 'FORM_OPEN' | 'LOADING_VIDEO' | 'RESULT' | 'RETRY';

type PurchaseFormData = {
  item_text: string;
  item_link: string;
  user_reason: string;
};

export default function StrictSecretaryModal() {
  const [pageState, setPageState] = useState<PageState>('IDLE');
  const [aiResult, setAiResult] = useState<AIResultData | null>(null);
  const [ttsAudioUrl, setTtsAudioUrl] = useState<string | null>(null);
  const [lastRequest, setLastRequest] = useState<PurchaseFormData | null>(null);
  const [isRequestInFlight, setIsRequestInFlight] = useState(false);

  const isVideoEndedRef = useRef(false);
  const isApiResolvedRef = useRef(false);
  const currentAiDataRef = useRef<AIResultData | null>(null);
  const ttsAudioUrlRef = useRef<string | null>(null);

  const toggleForm = () => {
    setPageState((prev) => (prev === 'IDLE' ? 'FORM_OPEN' : 'IDLE'));
  };

  const resetAll = () => {
    setPageState('IDLE');
    setAiResult(null);
    setTtsAudioUrl(null);
    setLastRequest(null);
    setIsRequestInFlight(false);
    isVideoEndedRef.current = false;
    isApiResolvedRef.current = false;
    currentAiDataRef.current = null;
    ttsAudioUrlRef.current = null;
  };

  const prefetchTts = (text: string) => {
    getTtsAudio(text)
      .then((url) => {
        ttsAudioUrlRef.current = url;
        setTtsAudioUrl(url);
      })
      .catch((err) => {
        console.warn('TTS prefetch failed (결과는 계속 표시):', err);
      });
  };

  const canUseTts = (result: AIResultData) => {
    const hasSystemErrorReason =
      Array.isArray(result.reasoning) &&
      result.reasoning.some((reason) => reason.includes('오류') || reason.includes('연동'));
    return !hasSystemErrorReason;
  };

  const startEvaluation = (data: PurchaseFormData) => {
    setLastRequest(data);
    setPageState('LOADING_VIDEO');
    setIsRequestInFlight(true);
    isVideoEndedRef.current = false;
    isApiResolvedRef.current = false;
    currentAiDataRef.current = null;
    ttsAudioUrlRef.current = null;
    setTtsAudioUrl(null);

    evaluatePurchase(data)
      .then((result) => {
        if (!result || typeof result.fact_violence_comment !== 'string') {
          throw new Error('Invalid strict-secretary result');
        }
        isApiResolvedRef.current = true;
        currentAiDataRef.current = result;
        if (canUseTts(result)) {
          prefetchTts(result.fact_violence_comment);
        }
        setAiResult(result);
        setPageState('RESULT');
      })
      .catch((err) => {
        console.error('strict-secretary API error:', {
          message: err?.message,
          status: err?.response?.status,
          data: err?.response?.data,
        });
        isApiResolvedRef.current = false;
        setPageState('RETRY');
      })
      .finally(() => {
        setIsRequestInFlight(false);
      });
  };

  const handleFormSubmit = (data: PurchaseFormData) => {
    startEvaluation(data);
  };

  const handleVideoEnded = () => {
    if (isRequestInFlight) {
      return;
    }

    isVideoEndedRef.current = true;

    if (isApiResolvedRef.current && currentAiDataRef.current) {
      setAiResult(currentAiDataRef.current);
      setPageState('RESULT');
      return;
    }
    setPageState('RETRY');
  };

  const handleRetry = () => {
    if (isApiResolvedRef.current && currentAiDataRef.current) {
      setAiResult(currentAiDataRef.current);
      setPageState('RESULT');
      return;
    }

    if (isRequestInFlight) {
      alert('아직 분석 중입니다. 조금만 더 기다려주세요.');
      return;
    }

    if (lastRequest) {
      startEvaluation(lastRequest);
      return;
    }

    setAiResult({
      is_approved: false,
      fact_violence_comment: '요청 정보를 찾지 못했습니다. 다시 입력해주세요.',
      reasoning: ['요청 데이터가 없어 재시도할 수 없습니다.'],
    });
    setPageState('RESULT');
  };

  return (
    <div className="ss-modal-wrapper">
      {(pageState === 'IDLE' || pageState === 'FORM_OPEN') && (
        <button className="ss-fab-btn" onClick={toggleForm} aria-label="구매 요청서 작성 열기">
          <img src={PRImage} alt="비서 이미지" className="ss-btn-image" />
        </button>
      )}

      {pageState === 'FORM_OPEN' && (
        <StrictSecretaryForm onSubmit={handleFormSubmit} onClose={toggleForm} />
      )}

      {pageState === 'LOADING_VIDEO' && (
        <StrictSecretaryLanding onVideoEnded={handleVideoEnded} onClose={resetAll} />
      )}

      {(pageState === 'RESULT' || pageState === 'RETRY') && (
        <div className="ss-result-overlay">
          <StrictSecretaryResult
            status={pageState === 'RESULT' ? 'RESULT' : 'RETRY'}
            data={aiResult || undefined}
            audioUrl={ttsAudioUrl || undefined}
            ttsEnabled={aiResult ? canUseTts(aiResult) : true}
            onRetry={handleRetry}
            onReset={resetAll}
          />
        </div>
      )}
    </div>
  );
}
