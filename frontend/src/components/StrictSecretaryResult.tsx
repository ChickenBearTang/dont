import { useState, useRef, useEffect } from 'react';
import './StrictSecretaryResult.css';
import ApprovedImg from '@/assets/approved.mp4';
import RejectedImg from '@/assets/rejected.mp4';

export interface AIResultData {
  is_approved: boolean;
  fact_violence_comment: string;
  reasoning: string[];
}

interface StrictSecretaryResultProps {
  status: 'RESULT' | 'RETRY';
  data?: AIResultData;
  audioUrl?: string;
  onRetry: () => void;
  onReset: () => void;
}

export default function StrictSecretaryResult({ status, data, audioUrl, onRetry, onReset }: StrictSecretaryResultProps) {
  const [ttsState, setTtsState] = useState<'idle' | 'loading' | 'playing'>('idle');
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const hasAutoPlayedRef = useRef(false);

  // 결과 페이지 도달 시 audioUrl이 있으면 자동 재생
  useEffect(() => {
    if (status === 'RESULT' && audioUrl && !hasAutoPlayedRef.current) {
      hasAutoPlayedRef.current = true;
      const audio = new Audio(audioUrl);

      audio.onended = () => {
        setTtsState('idle');
        audioRef.current = null;
      };

      audioRef.current = audio;
      audio.play()
        .then(() => setTtsState('playing'))
        .catch((err) => console.warn('자동 재생 실패:', err));
    }
  }, [status, audioUrl]);

  const handlePlayVoice = async () => {
    if (!data) return;

    // 이미 재생 중이면 정지
    if (ttsState === 'playing' && audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
      setTtsState('idle');
      return;
    }

    // 미리 생성된 audioUrl이 있으면 그걸 재사용
    if (audioUrl) {
      const audio = new Audio(audioUrl);
      audio.onended = () => {
        setTtsState('idle');
        audioRef.current = null;
      };
      audioRef.current = audio;
      await audio.play();
      setTtsState('playing');
      return;
    }

    // audioUrl이 없으면 직접 TTS API 호출 (fallback)
    setTtsState('loading');
    try {
      const res = await fetch('http://localhost:8000/api/v1/strict-secretary/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: data.fact_violence_comment }),
      });
      if (!res.ok) throw new Error('TTS 요청 실패');

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => {
        setTtsState('idle');
        URL.revokeObjectURL(url);
        audioRef.current = null;
      };
      audioRef.current = audio;
      await audio.play();
      setTtsState('playing');
    } catch (err) {
      console.error('TTS error:', err);
      alert('음성 생성에 실패했습니다. ELEVEN_API_KEY를 .env에 추가했는지 확인해주세요.');
      setTtsState('idle');
    }
  };

  if (status === 'RETRY' || !data) {
    return (
      <div className="ss-result-container retry">
        <h2>AI 응답 지연</h2>
        <p>엄격한 비서가 아직 답변을 준비하지 못했어요.</p>
        <div className="ss-result-actions">
          <button className="ss-retry-btn" onClick={onRetry}>다시 확인하기</button>
          <button className="ss-reset-btn" onClick={onReset}>처음으로</button>
        </div>
      </div>
    );
  }

  const { is_approved, fact_violence_comment, reasoning } = data;

  return (
    <div className={`ss-result-container ${is_approved ? 'approved' : 'rejected'}`}>
      <div className="ss-result-status">
        {is_approved ? '✅ 구매 승인' : '❌ 구매 기각'}
      </div>

      <div className="ss-character-speech">
        <video
          className="ss-character-img"
          src={is_approved ? ApprovedImg : RejectedImg}
          autoPlay
          loop
          muted
          playsInline
        />
        <div className="ss-speech-bubble">
          <div className="ss-speech-bubble-header">
            <h3>깐지의 한마디</h3>
            <button
              className="ss-tts-btn"
              onClick={handlePlayVoice}
              disabled={ttsState === 'loading'}
              aria-label="팩트폭력 음성으로 듣기"
            >
              {ttsState === 'idle' && '🔊 다시 듣기'}
              {ttsState === 'loading' && '⏳ 생성 중...'}
              {ttsState === 'playing' && '⏹ 정지'}
            </button>
          </div>
          <p>"{fact_violence_comment}"</p>
        </div>
      </div>

      <div className="ss-reasoning">
        <h3>판단 이유</h3>
        <ul className="ss-reasoning-list">
          {reasoning.map((reason, index) => (
            <li key={index}>{reason}</li>
          ))}
        </ul>
      </div>

      <button className="ss-reset-btn" onClick={onReset}>다른 물건 물어보기</button>
    </div>
  );
}
