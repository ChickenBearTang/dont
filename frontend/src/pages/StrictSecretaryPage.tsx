import { useState, useRef } from 'react';
import StrictSecretaryForm from '@/components/StrictSecretaryForm';
import StrictSecretaryLanding from '@/components/StrictSecretaryLanding';
import StrictSecretaryResult, { type AIResultData } from '@/components/StrictSecretaryResult';
import { evaluatePurchase, getTtsAudio } from '@/features/ai/spending-judgment/api/strictSecretaryApi';
import PRImage from '@/assets/PR.png';
import './StrictSecretaryPage.css';

type PageState = 'IDLE' | 'FORM_OPEN' | 'LOADING_VIDEO' | 'RESULT' | 'RETRY';

export default function StrictSecretaryPage() {
  const [pageState, setPageState] = useState<PageState>('IDLE');
  const [aiResult, setAiResult] = useState<AIResultData | null>(null);
  const [ttsAudioUrl, setTtsAudioUrl] = useState<string | null>(null);

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
    isVideoEndedRef.current = false;
    isApiResolvedRef.current = false;
    currentAiDataRef.current = null;
    ttsAudioUrlRef.current = null;
  };

  // TTS 음성을 미리 생성하는 함수 (영상 재생 중에 백그라운드로 호출)
  const prefetchTts = (text: string) => {
    getTtsAudio(text)
      .then((url) => {
        ttsAudioUrlRef.current = url;
        setTtsAudioUrl(url);
      })
      .catch((err) => {
        console.warn('TTS prefetch 실패 (음성 없이 결과만 표시):', err);
      });
  };

  const handleFormSubmit = (data: {
    item_text: string;
    item_link: string;
    user_reason: string;
  }) => {
    console.log('Purchase Request Data:', data);

    setPageState('LOADING_VIDEO');
    isVideoEndedRef.current = false;
    isApiResolvedRef.current = false;
    currentAiDataRef.current = null;
    ttsAudioUrlRef.current = null;
    setTtsAudioUrl(null);

    // 1. 텍스트 API 호출 → 성공하면 바로 TTS도 호출
    evaluatePurchase({
      item_text: data.item_text,
      item_link: data.item_link,
      user_reason: data.user_reason,
    })
      .then((result) => {
        isApiResolvedRef.current = true;
        currentAiDataRef.current = result;

        // 2. 텍스트 결과를 받자마자 TTS 생성도 백그라운드로 시작
        prefetchTts(result.fact_violence_comment);

        // 영상이 이미 끝났다면 바로 결과 화면으로 전환
        if (isVideoEndedRef.current) {
          setAiResult(result);
          setPageState('RESULT');
        }
      })
      .catch((err) => {
        console.error('strict-secretary API error:', err);
        isApiResolvedRef.current = false;
      });
  };

  const handleVideoEnded = () => {
    isVideoEndedRef.current = true;

    if (isApiResolvedRef.current && currentAiDataRef.current) {
      setAiResult(currentAiDataRef.current);
      setPageState('RESULT');
    } else {
      setPageState('RETRY');
    }
  };

  const handleRetry = () => {
    if (isApiResolvedRef.current && currentAiDataRef.current) {
      setAiResult(currentAiDataRef.current);
      setPageState('RESULT');
    } else {
      alert('아직 AI가 고민 중입니다. 잠시 후 다시 시도해주세요.');
    }
  };

  return (
    <div className="ss-page-container">
      <main className="ss-main">
        {(pageState === 'IDLE' || pageState === 'FORM_OPEN') && (
          <button
            className="ss-circle-btn"
            onClick={toggleForm}
            aria-label="구매 요청서 작성 폼 열기"
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
