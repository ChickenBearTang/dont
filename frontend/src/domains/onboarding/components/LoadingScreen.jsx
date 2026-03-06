import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import mascot4 from '../../../assets/character/luluddun4.png';
import { Mascot, ProgressBar } from '../../../components/common/Feedback';

const LoadingScreen = () => {
  const navigate = useNavigate();
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('은행 보안 서버에 안전하게 연결하고 있어요');

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(timer);
          setTimeout(() => navigate('/savebox-setup'), 500);
          return 100;
        }
        return prev + 1;
      });
    }, 45); // Approx 4.5 seconds total

    const messageTimer = setTimeout(
      () => setMessage('뚱땅이가 꼼꼼하게 계좌 정보를 불러오는 중이에요 ✨'),
      1500
    );
    const messageTimer2 = setTimeout(
      () => setMessage('거의 다 됐어요! 잠시만 기다려 주세요 🐷'),
      3200
    );

    return () => {
      clearInterval(timer);
      clearTimeout(messageTimer);
      clearTimeout(messageTimer2);
    };
  }, [navigate]);

  return (
    <div
      className="container"
      style={{
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '80vh',
        textAlign: 'center',
      }}
    >
      <Mascot src={mascot4} style={{ width: '200px' }} className="mb-10" />

      <div
        style={{
          height: '32px',
          marginBottom: '24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '100%',
        }}
      >
        <h2
          style={{
            fontSize: '19px',
            fontWeight: '800',
            color: 'var(--eel)',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            margin: 0,
            width: '100%',
          }}
        >
          {message}
        </h2>
      </div>

      <div
        className="progress-bar-container"
        style={{
          width: '100%',
          maxWidth: '300px',
          height: '16px',
          backgroundColor: '#e5e5e5',
          borderRadius: '10px',
        }}
      >
        <div
          className="progress-bar-fill"
          style={{
            width: `${progress}%`,
            backgroundColor: 'var(--primary-blue)',
            transition: 'width 0.1s linear',
            borderRadius: '10px',
          }}
        />
      </div>
      <p className="mt-4" style={{ color: 'var(--gray)', fontWeight: '900', fontSize: '18px' }}>
        {progress}%
      </p>
    </div>
  );
};

export default LoadingScreen;
