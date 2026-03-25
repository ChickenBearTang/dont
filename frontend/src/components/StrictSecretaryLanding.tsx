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
    if (videoRef.current) {
      videoRef.current.muted = isMuted;
      videoRef.current.play().catch((error) => {
        console.warn('Auto-play with sound failed, falling back to muted:', error);
        setIsMuted(true);
        if (videoRef.current) {
          videoRef.current.muted = true;
          videoRef.current.play().catch(e => console.error("Even muted autoplay failed", e));
        }
      });
    }
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
        />
      </div>
    </div>
  );
}
