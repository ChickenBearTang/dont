import React, { useEffect } from 'react';
import mascot3 from '../../../assets/character/luluddun3.png';
import { Mascot } from '../../../components/common/Feedback';

const SuccessScreen = ({ onComplete }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onComplete();
    }, 3000); // 3 seconds celebration

    return () => clearTimeout(timer);
  }, [onComplete]);

  return (
    <div
      className="container fade-in"
      style={{
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        textAlign: 'center',
      }}
    >
      {/* Confetti Animation Placeholder (Simple CSS Fireworks) */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          height: '300px',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          marginBottom: '40px',
        }}
      >
        <div
          className="celebration-ring"
          style={{
            position: 'absolute',
            width: '200px',
            height: '200px',
            borderRadius: '50%',
            border: '4px solid var(--primary-blue-light)',
            opacity: 0,
            animation: 'ringExpand 1.5s ease-out infinite',
          }}
        ></div>
        <Mascot
          src={mascot3}
          style={{ width: '220px', zIndex: 2, animation: 'bounce 0.5s ease infinite alternate' }}
        />
      </div>

      <h1 style={{ fontSize: '36px', color: 'var(--green)', marginBottom: '16px' }}>
        축하드려요! 🎉
      </h1>
      <h2
        style={{
          fontSize: '22px',
          color: 'var(--eel)',
          fontWeight: '800',
          wordBreak: 'keep-all',
          padding: '0 20px',
        }}
      >
        세이프박스 개설이 완료되었습니다.
        <br />
        목돈 마련의 첫 걸음을 떼셨네요!
      </h2>

      <p className="mt-6" style={{ color: 'var(--gray)', fontWeight: '700' }}>
        잠시 후 대시보드로 이동합니다...
      </p>

      <style>{`
                @keyframes ringExpand {
                    0% { transform: scale(0.5); opacity: 1; }
                    100% { transform: scale(1.5); opacity: 0; }
                }
                @keyframes bounce {
                    from { transform: translateY(0); }
                    to { transform: translateY(-20px); }
                }
            `}</style>
    </div>
  );
};

export default SuccessScreen;
