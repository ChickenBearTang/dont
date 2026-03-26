import { useRef, useState } from 'react';
import StrictSecretaryForm from '@/components/StrictSecretaryForm';
import StrictSecretaryLanding from '@/components/StrictSecretaryLanding';
import StrictSecretaryResult, { type AIResultData } from '@/components/StrictSecretaryResult';
import { evaluatePurchase, getTtsAudio } from '@/features/ai/spending-judgment/api/strictSecretaryApi';
import PRImage from '@/assets/PR.png';
import './StrictSecretaryPage.css';

type PageState = 'IDLE' | 'FORM_OPEN' | 'LOADING_VIDEO' | 'RESULT' | 'RETRY';

type PurchaseFormData = {
  item_text: string;
  item_link: string;
  user_reason: string;
};

export default function StrictSecretaryPage() {
  const [pageState, setPageState] = useState<PageState>('IDLE');
  const [aiResult, setAiResult] = useState<AIResultData | null>(null);
  const [ttsAudioUrl, setTtsAudioUrl] = useState<string | null>(null);
  const [isRequestInFlight, setIsRequestInFlight] = useState(false);

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
    setIsRequestInFlight(false);
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

  const handleFormSubmit = (data: PurchaseFormData) => {
    setPageState('LOADING_VIDEO');
    setIsRequestInFlight(true);
    isApiResolvedRef.current = false;
    currentAiDataRef.current = null;
    ttsAudioUrlRef.current = null;
    setTtsAudioUrl(null);

    evaluatePurchase(data)
      .then((result) => {
        isApiResolvedRef.current = true;
        currentAiDataRef.current = result;
        prefetchTts(result.fact_violence_comment);
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

  const handleVideoEnded = () => {
    if (isRequestInFlight) {
      return;
    }

    if (isApiResolvedRef.current && currentAiDataRef.current) {
      setAiResult(currentAiDataRef.current);
      setPageState('RESULT');
    }
  };

  const handleRetry = () => {
    if (isRequestInFlight) {
      alert('아직 분석 중입니다. 조금만 더 기다려주세요.');
      return;
    }

    if (isApiResolvedRef.current && currentAiDataRef.current) {
      setAiResult(currentAiDataRef.current);
      setPageState('RESULT');
      return;
    }

    alert('요청이 실패했습니다. 다시 시도해 주세요.');
  };

  return (
    <div className="ss-page-container">
      <main className="ss-main">
        {(pageState === 'IDLE' || pageState === 'FORM_OPEN') && (
          <button
            className="ss-circle-btn"
            onClick={toggleForm}
            aria-label="구매 요청서 작성 열기"
          >
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
          <StrictSecretaryResult
            status={pageState === 'RESULT' ? 'RESULT' : 'RETRY'}
            data={aiResult || undefined}
            audioUrl={ttsAudioUrl || undefined}
            onRetry={handleRetry}
            onReset={resetAll}
          />
        )}
      </main>
    </div>
  );
}
