import { useEffect, useRef, useState } from 'react';
import './StrictSecretaryLanding.css';
import LandingVideo from '@/assets/2026.mp4';

interface StrictSecretaryLandingProps {
  onVideoEnded: () => void;
  onClose: () => void;
}

export default function StrictSecretaryLanding({ onVideoEnded }: StrictSecretaryLandingProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isMuted, setIsMuted] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const video = videoRef.current;

    if (!video) return;

    video.muted = isMuted;
    video
      .play()
      .catch((error: unknown) => {
        if (cancelled) return;

        if (error instanceof DOMException && error.name === 'AbortError') {
          return;
        }

        console.warn('소리 포함 자동 재생 실패, 음소거 재생으로 전환합니다:', error);
        setIsMuted(true);

        if (!videoRef.current) return;
        videoRef.current.muted = true;
        videoRef.current.play().catch((mutedError: unknown) => {
          if (cancelled) return;
          if (mutedError instanceof DOMException && mutedError.name === 'AbortError') {
            return;
          }
          console.error('음소거 자동 재생도 실패했습니다.', mutedError);
        });
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  return (
    <div className="ss-landing-overlay">
      <div className="ss-landing-container" style={{ position: 'relative' }}>
        <button
          className="ss-mute-btn"
          onClick={toggleMute}
          aria-label={isMuted ? '소리 켜기' : '소리 끄기'}
          title={isMuted ? '소리 켜기' : '소리 끄기'}
        >
          {isMuted ? '🔇' : '🔊'}
        </button>
        <div className="ss-landing-header">
          <span>깐지가 판단 중입니다...</span>
        </div>
        <video
          ref={videoRef}
          className="ss-landing-video"
          src={LandingVideo}
          onEnded={onVideoEnded}
          playsInline
          autoPlay
          loop
        />
      </div>
    </div>
  );
}
