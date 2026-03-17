import { useState, useRef } from 'react';
import './StrictSecretaryResult.css';

export interface AIResultData {
  is_approved: boolean;
  fact_violence_comment: string;
  reasoning: string[];
}

interface StrictSecretaryResultProps {
  status: 'RESULT' | 'RETRY';
  data?: AIResultData;
  onRetry: () => void;
  onReset: () => void;
}

export default function StrictSecretaryResult({ status, data, onRetry, onReset }: StrictSecretaryResultProps) {
  const [ttsState, setTtsState] = useState<'idle' | 'loading' | 'playing'>('idle');
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handlePlayVoice = async () => {
    if (!data) return;

    // 이미 재생 중이면 정지
    if (ttsState === 'playing' && audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
      setTtsState('idle');
      return;
    }

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
      
      <div className="ss-fact-violence">
        <div className="ss-fact-violence-header">
          <h3>비서의 팩트 폭력</h3>
          <button
            className="ss-tts-btn"
            onClick={handlePlayVoice}
            disabled={ttsState === 'loading'}
            aria-label="팩트폭력 음성으로 듣기"
          >
            {ttsState === 'idle' && '🔊 듣기'}
            {ttsState === 'loading' && '⏳ 생성 중...'}
            {ttsState === 'playing' && '⏹ 정지'}
          </button>
        </div>
        <p>"{fact_violence_comment}"</p>
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

