import { useEffect, useRef, useState } from 'react';
import axiosInstance from '@/shared/api/axiosInstance';
import ApprovedImg from '@/assets/approved.mp4';
import RejectedImg from '@/assets/rejected.mp4';
import './StrictSecretaryResult.css';

export interface AIResultData {
  is_approved: boolean;
  fact_violence_comment: string;
  reasoning: string[];
}

interface StrictSecretaryResultProps {
  status: 'RESULT' | 'RETRY';
  data?: AIResultData;
  audioUrl?: string;
  ttsEnabled?: boolean;
  onRetry: () => void;
  onReset: () => void;
}

export default function StrictSecretaryResult({
  status,
  data,
  audioUrl,
  ttsEnabled = true,
  onRetry,
  onReset,
}: StrictSecretaryResultProps) {
  const [ttsState, setTtsState] = useState<'idle' | 'loading' | 'playing'>('idle');
  const [localAudioUrl, setLocalAudioUrl] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const hasAutoPlayedRef = useRef(false);

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    return () => {
      if (localAudioUrl) {
        URL.revokeObjectURL(localAudioUrl);
      }
    };
  }, [localAudioUrl]);

  useEffect(() => {
    if (status !== 'RESULT' || !audioUrl || !ttsEnabled || hasAutoPlayedRef.current) {
      return;
    }

    hasAutoPlayedRef.current = true;
    const audio = new Audio(audioUrl);
    audio.onended = () => {
      setTtsState('idle');
      audioRef.current = null;
    };
    audioRef.current = audio;
    audio
      .play()
      .then(() => setTtsState('playing'))
      .catch((err) => console.warn('자동 재생 실패:', err));
  }, [status, audioUrl, ttsEnabled]);

  const handlePlayVoice = async () => {
    if (!data || !ttsEnabled) return;

    if (ttsState === 'playing' && audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
      setTtsState('idle');
      return;
    }

    const cachedUrl = audioUrl || localAudioUrl;
    if (cachedUrl) {
      const audio = new Audio(cachedUrl);
      audio.onended = () => {
        setTtsState('idle');
        audioRef.current = null;
      };
      audioRef.current = audio;
      await audio.play();
      setTtsState('playing');
      return;
    }

    setTtsState('loading');
    try {
      const blob: any = await axiosInstance.post(
        '/fin/strict-secretary/tts',
        { text: data.fact_violence_comment },
        { responseType: 'blob' }
      );
      const url = URL.createObjectURL(blob);
      setLocalAudioUrl(url);

      const audio = new Audio(url);
      audio.onended = () => {
        setTtsState('idle');
        audioRef.current = null;
      };
      audioRef.current = audio;
      await audio.play();
      setTtsState('playing');
    } catch (err) {
      console.error('TTS error:', err);
      alert('음성 생성에 실패했습니다. 잠시 후 다시 시도해주세요.');
      setTtsState('idle');
    }
  };

  if (status === 'RETRY' || !data) {
    return (
      <div className="ss-result-container retry" style={{ position: 'relative' }}>
        <button className="ss-close-btn" onClick={onReset} aria-label="닫기">
          &times;
        </button>
        <h2>AI 응답 지연</h2>
        <p>엄격한 비서가 아직 답변을 준비하지 못했어요.</p>
        <div className="ss-result-actions">
          <button className="ss-retry-btn" onClick={onRetry}>
            다시 확인하기
          </button>
          <button className="ss-reset-btn" onClick={onReset}>
            처음으로
          </button>
        </div>
      </div>
    );
  }

  const { is_approved, fact_violence_comment, reasoning } = data;

  return (
    <div className={`ss-result-container ${is_approved ? 'approved' : 'rejected'}`} style={{ position: 'relative' }}>
      <button className="ss-close-btn" onClick={onReset} aria-label="닫기">
        &times;
      </button>
      <div className="ss-result-status">{is_approved ? '✅ 구매 승인' : '❌ 구매 기각'}</div>

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
              disabled={ttsState === 'loading' || !ttsEnabled}
              aria-label="텍스트를 음성으로 듣기"
            >
              {ttsState === 'idle' && (ttsEnabled ? '🔊 다시 듣기' : '음성 비활성')}
              {ttsState === 'loading' && '🔄 생성 중...'}
              {ttsState === 'playing' && '⏸ 정지'}
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

      <button className="ss-reset-btn" onClick={onReset}>
        다른 물건 물어보기
      </button>
    </div>
  );
}
