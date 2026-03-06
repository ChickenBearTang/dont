import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ssafyLogo from '../../../assets/logo/ssafylogo.png';
import { Button, Input, Card } from '../../../components/common/UI';

const Login = ({ onSocialLogin }) => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = (e) => {
    e.preventDefault();
    onSocialLogin('email');
    navigate('/dashboard');
  };

  return (
    <div className="container" style={{ maxWidth: '440px' }}>
      <h2
        className="text-center"
        style={{
          fontSize: '32px',
          fontWeight: '900',
          color: 'var(--primary-blue)',
          marginBottom: '8px',
        }}
      >
        로그인
      </h2>
      <p
        className="text-center"
        style={{ color: 'var(--gray)', fontWeight: '700', marginBottom: '32px' }}
      >
        DON'T에 오신 것을 환영합니다!
      </p>

      <Card className="flex-col gap-2" style={{ padding: '32px 24px' }}>
        <form onSubmit={handleLogin} className="flex-col gap-1">
          <Input
            label="이메일"
            type="email"
            placeholder="email@ssafy.com"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-0"
          />

          <Input
            label="비밀번호"
            type="password"
            placeholder="비밀번호 입력"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ marginTop: '16px' }}
          />

          <Button
            type="submit"
            variant="primary"
            className="mt-8 w-full"
            style={{ padding: '18px' }}
          >
            로그인
          </Button>
        </form>

        <div
          style={{
            position: 'relative',
            textAlign: 'center',
            margin: '24px 0 16px',
            color: 'var(--gray)',
            fontWeight: '800',
            fontSize: '14px',
          }}
        >
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '0',
              width: '100%',
              height: '2px',
              background: 'var(--gray-light)',
              zIndex: '1',
            }}
          ></div>
          <span
            style={{ position: 'relative', background: 'white', padding: '0 12px', zIndex: '2' }}
          >
            또는
          </span>
        </div>

        <div style={{ width: '100%' }}>
          <Button
            variant="oauth"
            className="w-full"
            style={{ maxWidth: 'none', borderRadius: '16px' }}
            onClick={() => onSocialLogin('ssafy')}
          >
            <img src={ssafyLogo} alt="SSAFY" style={{ width: '20px' }} />
            SSAFY 계정으로 시작하기
          </Button>
        </div>
      </Card>

      <p
        className="text-center mt-8"
        style={{ fontSize: '15px', color: 'var(--gray)', fontWeight: '700' }}
      >
        계정이 없으신가요?{' '}
        <span
          style={{ color: 'var(--primary-blue)', fontWeight: '900', cursor: 'pointer' }}
          onClick={() => navigate('/onboarding')}
        >
          회원가입
        </span>
      </p>
    </div>
  );
};

export default Login;
