import { useEffect, useRef } from 'react';
import './StrictSecretaryLanding.css';
import LandingVideo from '@/assets/2026.mp4';

interface StrictSecretaryLandingProps {
  onVideoEnded: () => void;
}

export default function StrictSecretaryLanding({ onVideoEnded }: StrictSecretaryLandingProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    // Ensuring the video plays when mounted
    if (videoRef.current) {
      videoRef.current.play().catch((error) => {
        console.error('Auto-play failed:', error);
      });
    }
  }, []);

  return (
    <div className="ss-landing-overlay">
      <div className="ss-landing-container">
        <div className="ss-landing-header">
          <span>깐지가 판단 중입니다...</span>
        </div>
        <video
          ref={videoRef}
          className="ss-landing-video"
          src={LandingVideo}
          onEnded={onVideoEnded}
          playsInline
          muted // Needed for autoplay in most browsers
          autoPlay
        />
      </div>
    </div>
  );
}
