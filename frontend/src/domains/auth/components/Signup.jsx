import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Input } from '../../../components/common/UI';
import { ProgressBar } from '../../../components/common/Feedback';

const Signup = ({ onNext }) => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    passwordConfirm: '',
    realName: '',
    birthday: '',
    emailVerified: false,
    tos: false,
    privacy: false,
    marketing: false,
  });

  const [isVerifying, setIsVerifying] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleEmailVerify = () => {
    setIsVerifying(true);
    setTimeout(() => {
      setFormData((prev) => ({ ...prev, emailVerified: true }));
      setIsVerifying(false);
    }, 1200);
  };

  const isFormValid = () => {
    return (
      formData.email &&
      formData.password &&
      formData.password === formData.passwordConfirm &&
      formData.realName &&
      formData.birthday &&
      formData.emailVerified &&
      formData.tos &&
      formData.privacy
    );
  };

  return (
    <div className="container" style={{ maxWidth: '500px' }}>
      <div style={{ marginBottom: '40px' }}>
        <ProgressBar progress={80} />
      </div>

      <h2 className="text-center" style={{ fontSize: '36px', marginBottom: '8px' }}>
        마지막 단계!
      </h2>
      <p
        className="text-center"
        style={{ color: 'var(--gray)', fontWeight: '700', marginBottom: '32px' }}
      >
        계정을 생성하고 분석 결과를 저장하세요.
      </p>

      <Card className="flex-col gap-6">
        <div>
          <Input
            label="이메일"
            name="email"
            type="email"
            placeholder="email@ssafy.com"
            value={formData.email}
            onChange={handleChange}
            className="mt-0"
          />
          <Button
            variant="primary"
            className="mt-6 w-full"
            style={{ fontSize: '14px' }}
            onClick={handleEmailVerify}
            disabled={!formData.email || formData.emailVerified || isVerifying}
          >
            {formData.emailVerified ? '인증완료' : '이메일 인증하기'}
          </Button>
        </div>

        <div className="grid-cols-2">
          <Input
            label="비밀번호"
            name="password"
            type="password"
            placeholder="8자 이상"
            value={formData.password}
            onChange={handleChange}
            className="mt-0"
          />
          <Input
            label="비밀번호 확인"
            name="passwordConfirm"
            type="password"
            placeholder="한 번 더!"
            value={formData.passwordConfirm}
            onChange={handleChange}
            className="mt-0"
            style={{
              borderColor:
                formData.passwordConfirm && formData.password !== formData.passwordConfirm
                  ? 'var(--red)'
                  : '',
            }}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: '16px' }}>
          <Input
            label="실명"
            name="realName"
            type="text"
            placeholder="성함 입력"
            value={formData.realName}
            onChange={handleChange}
            className="mt-0"
          />
          <Input
            label="생년월일"
            name="birthday"
            type="date"
            value={formData.birthday}
            onChange={handleChange}
            className="mt-0"
          />
        </div>

        <div style={{ borderTop: '2px solid var(--gray-light)', paddingTop: '24px' }}>
          <p style={{ fontWeight: '900', fontSize: '17px', marginBottom: '20px' }}>약관 동의</p>
          <div className="flex-col gap-4">
            {['tos', 'privacy', 'marketing'].map((name, i) => (
              <label
                key={name}
                className="flex-row items-center"
                style={{ gap: '14px', cursor: 'pointer', fontSize: '15px', fontWeight: '700' }}
              >
                <input
                  type="checkbox"
                  name={name}
                  checked={formData[name]}
                  onChange={handleChange}
                  style={{ width: '22px', height: '22px' }}
                />
                <span style={{ color: i === 2 ? 'var(--gray)' : 'inherit' }}>
                  ({i === 2 ? '선택' : '필수'}){' '}
                  {i === 0 ? '이용약관' : i === 1 ? '개인정보 처리방침' : '마케팅 수신'} 동의
                </span>
              </label>
            ))}
          </div>
        </div>

        <Button
          variant="primary"
          style={{ width: '100%', padding: '20px', marginTop: '12px' }}
          onClick={onNext}
          disabled={!isFormValid()}
        >
          환영합니다! 시작하기
        </Button>
      </Card>
    </div>
  );
};

export default Signup;
