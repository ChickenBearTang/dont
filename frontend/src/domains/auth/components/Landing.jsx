import React from 'react';
import { useNavigate } from 'react-router-dom';
import mascotImg from '../../../assets/character/luluddun1.png';
import ssafyLogo from '../../../assets/logo/ssafylogo.png';
import { Button } from '../../../components/common/UI';
import { Mascot } from '../../../components/common/Feedback';

const Landing = ({ onSocialLogin }) => {
  const navigate = useNavigate();
  return (
    <div
      className="container"
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
      }}
    >
      {/* Title & Description at Top */}
      <h1
        style={{ fontSize: '80px', marginBottom: '8px', letterSpacing: '-4px', fontWeight: '900' }}
      >
        DON'T
      </h1>
      <p
        style={{
          color: 'var(--gray)',
          marginBottom: '30px',
          fontSize: '22px',
          fontWeight: '800',
          lineHeight: '1.4',
          wordBreak: 'keep-all',
        }}
      >
        싸피인을 위한 가장 스마트한
        <br />
        목돈 마련 도우미
      </p>

      {/* Mascot in Middle */}
      <Mascot src={mascotImg} className="mb-10" style={{ width: '280px' }} />

      {/* Buttons at Bottom */}
      <div
        style={{
          width: '100%',
          maxWidth: '360px',
          display: 'flex',
          flexDirection: 'column',
          gap: '15px',
        }}
      >
        <Button
          variant="primary"
          style={{ fontSize: '20px', padding: '18px' }}
          onClick={() => navigate('/onboarding')}
        >
          시작하기
        </Button>

        <Button variant="oauth" style={{ margin: '0' }} onClick={() => onSocialLogin('ssafy')}>
          <img src={ssafyLogo} alt="SSAFY" style={{ width: '28px' }} />
          SSAFY 계정으로 시작하기
        </Button>

        <Button
          variant="outline"
          style={{
            border: 'none',
            background: 'none',
            color: 'var(--primary-blue)',
            fontSize: '18px',
            boxShadow: 'none',
            padding: '10px',
          }}
          onClick={() => navigate('/login')}
        >
          이미 계정이 있어요
        </Button>
      </div>
    </div>
  );
};

export default Landing;
