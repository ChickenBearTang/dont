import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Input } from '@/shared/components';
import { useUIStore } from '@/shared/store/useUIStore';
import { confirmPasswordReset, requestPasswordReset } from '@/features/auth/api/authApi';

export const ForgotPasswordPage = () => {
  const navigate = useNavigate();
  const { addToast } = useUIStore();

  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [isCodeRequested, setIsCodeRequested] = useState(false);
  const [expiresIn, setExpiresIn] = useState(0);
  const [isRequesting, setIsRequesting] = useState(false);
  const [isConfirming, setIsConfirming] = useState(false);

  const isValidEmail = email.includes('@');
  const passwordTooShort = newPassword.length > 0 && newPassword.length < 8;
  const passwordMismatch =
    passwordConfirm.length > 0 && newPassword.length > 0 && newPassword !== passwordConfirm;

  const handleRequestCode = async () => {
    if (isRequesting) {
      return;
    }

    if (!isValidEmail) {
      addToast('올바른 이메일 형식을 입력해주세요.', 'error');
      return;
    }

    setIsRequesting(true);
    try {
      const response = await requestPasswordReset({ email });
      setIsCodeRequested(true);
      setExpiresIn(response.data.expiresInSeconds);
      addToast(response.data.message, 'success');
    } catch {
      addToast('재설정 코드 요청에 실패했습니다.', 'error');
    } finally {
      setIsRequesting(false);
    }
  };

  const handleConfirm = async () => {
    if (isConfirming) {
      return;
    }

    if (!isValidEmail) {
      addToast('올바른 이메일 형식을 입력해주세요.', 'error');
      return;
    }

    if (!/^\d{6}$/.test(code)) {
      addToast('6자리 코드를 입력해주세요.', 'error');
      return;
    }

    if (newPassword.length < 8) {
      addToast('비밀번호는 8자 이상이어야 합니다.', 'error');
      return;
    }

    if (newPassword !== passwordConfirm) {
      addToast('비밀번호 확인이 일치하지 않습니다.', 'error');
      return;
    }

    setIsConfirming(true);
    try {
      const response = await confirmPasswordReset({
        email,
        code,
        newPassword,
      });

      if (response.data.resetCompleted) {
        addToast('비밀번호가 재설정되었습니다. 다시 로그인해주세요.', 'success');
        navigate('/login', { replace: true });
      } else {
        addToast('비밀번호 재설정에 실패했습니다.', 'error');
      }
    } catch {
      addToast('코드가 올바르지 않거나 만료되었습니다.', 'error');
    } finally {
      setIsConfirming(false);
    }
  };

  return (
    <div className="max-w-[460px] mx-auto rounded-[28px] border border-line-soft bg-surface-base p-8 shadow-[0_18px_40px_rgba(15,23,42,0.08)]">
      <h2 className="text-[28px] font-black text-text-strong tracking-tight mb-2">비밀번호 찾기</h2>
      <p className="text-[14px] text-text-muted font-semibold mb-6">
        이메일로 받은 코드로 비밀번호를 재설정할 수 있어요.
      </p>

      <div className="space-y-2">
        <Input
          label="이메일"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="example@test.com"
          error={email.length > 0 && !isValidEmail}
          errorMessage="올바른 이메일 형식을 입력해주세요."
        />
        <Button onClick={handleRequestCode} disabled={isRequesting} className="mt-2">
          {isRequesting ? '요청 중...' : '재설정 코드 요청'}
        </Button>
      </div>

      {isCodeRequested && (
        <div className="mt-7 space-y-2">
          <p className="text-[12px] font-semibold text-text-subtle">
            코드 유효시간: 약 {Math.max(1, Math.ceil(expiresIn / 60))}분
          </p>
          <Input
            label="인증 코드"
            value={code}
            onChange={(event) => setCode(event.target.value.replace(/[^0-9]/g, ''))}
            placeholder="6자리 코드"
            maxLength={6}
          />
          <Input
            label="새 비밀번호"
            type="password"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
            placeholder="8자 이상 입력"
            error={passwordTooShort}
            errorMessage="비밀번호는 8자 이상이어야 합니다."
          />
          <Input
            label="새 비밀번호 확인"
            type="password"
            value={passwordConfirm}
            onChange={(event) => setPasswordConfirm(event.target.value)}
            placeholder="비밀번호 다시 입력"
            error={passwordMismatch}
            errorMessage="비밀번호가 일치하지 않습니다."
          />
          <Button
            onClick={handleConfirm}
            disabled={isConfirming || passwordTooShort || passwordMismatch}
          >
            {isConfirming ? '변경 중...' : '비밀번호 재설정'}
          </Button>
        </div>
      )}

      <button
        type="button"
        className="mt-6 text-[13px] font-bold text-accent hover:underline"
        onClick={() => navigate('/login')}
      >
        로그인으로 돌아가기
      </button>
    </div>
  );
};
