import axios from 'axios';
import { useMemo, useRef, useState, type ChangeEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { BirthDateField, Button, Card, Input, Modal } from '@/shared/components';
import {
  changePassword,
  changeNickname,
  completeProfileImage,
  createProfileImagePresign,
  deleteProfileImage,
  fetchMyPage,
  updateMyPage,
  withdraw,
  resetOnboarding,
} from '@/features/user/api/userApi';
import { useAuthStore } from '@/features/auth/store/useAuthStore';
import { useToast } from '@/shared/hooks';
import type { ApiResponse } from '@/shared/types';
import type { MyPageUpdateRequest } from '@/features/user/mypage/types';

interface MyPageFormState {
  name: string;
  birthDate: string;
  monthlySavingGoalAmount: string;
}

const toInitialForm = (
  name: string | null,
  birthDate: string | null,
  monthlySavingGoalAmount: number | null
): MyPageFormState => ({
  name: name ?? '',
  birthDate: birthDate ?? '',
  monthlySavingGoalAmount:
    monthlySavingGoalAmount === null || monthlySavingGoalAmount === undefined
      ? ''
      : String(monthlySavingGoalAmount),
});

const getTodayMinusOne = () => {
  const date = new Date();
  date.setDate(date.getDate() - 1);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const mapMyPageUpdateErrorMessage = (code?: string) => {
  switch (code) {
    case 'USER_400_3':
      return '수정할 정보가 없습니다.';
    case 'USER_400_4':
      return '이름은 공백만 입력할 수 없습니다.';
    default:
      return '마이페이지 수정에 실패했습니다.';
  }
};

const formatBirthDateLabel = (birthDate: string) => {
  const [year, month, day] = birthDate.split('-');
  if (!year || !month || !day) {
    return birthDate;
  }
  return `${year}.${month}.${day}`;
};

const formatAmountLabel = (value: string) => {
  if (!value) return '-';
  const amount = Number(value);
  if (!Number.isFinite(amount)) return value;
  return `${amount.toLocaleString()}원`;
};

const NICKNAME_PATTERN = /^[a-zA-Z0-9가-힣_]+$/;
const MAX_PROFILE_IMAGE_SIZE_BYTES = 10 * 1024 * 1024;
const ALLOWED_PROFILE_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

const mapNicknameChangeErrorMessage = (code?: string) => {
  switch (code) {
    case 'USER_400_1':
      return '닉네임은 2자 이상 20자 이하여야 합니다.';
    case 'USER_400_2':
      return '닉네임은 한글, 영문, 숫자, 밑줄(_)만 사용할 수 있습니다.';
    case 'USER_409_1':
      return '이미 사용 중인 닉네임입니다.';
    default:
      return '닉네임 변경에 실패했습니다.';
  }
};

const mapProfileImageErrorMessage = (code?: string) => {
  switch (code) {
    case 'S3_400_1':
      return '지원하지 않는 프로필 이미지 형식입니다.';
    case 'S3_400_2':
      return '파일명이 유효하지 않습니다.';
    case 'S3_400_3':
      return '프로필 이미지 key가 유효하지 않습니다.';
    default:
      return '프로필 이미지 처리에 실패했습니다.';
  }
};

const mapPasswordChangeErrorMessage = (code?: string) => {
  switch (code) {
    case 'USER_401_1':
      return '현재 비밀번호가 일치하지 않습니다.';
    case 'USER_400_5':
      return '새 비밀번호는 현재 비밀번호와 달라야 합니다.';
    default:
      return '비밀번호 변경에 실패했습니다.';
  }
};

const mapWithdrawErrorMessage = (code?: string) => {
  switch (code) {
    case 'USER_401_1':
      return '현재 비밀번호가 일치하지 않습니다.';
    default:
      return '회원 탈퇴에 실패했습니다.';
  }
};

export const MyPagePage = () => {
  const navigate = useNavigate();
  const logout = useAuthStore((state) => state.logout);
  const { success, error, info } = useToast();
  const queryClient = useQueryClient();
  const maxBirthDate = useMemo(() => getTodayMinusOne(), []);

  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['myPage'],
    queryFn: () => fetchMyPage().then((res) => res.data),
  });

  const [draftForm, setDraftForm] = useState<MyPageFormState | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isNicknameModalOpen, setIsNicknameModalOpen] = useState(false);
  const [nicknameDraft, setNicknameDraft] = useState('');
  const [nicknameErrorMessage, setNicknameErrorMessage] = useState('');
  const [isProfileImageProcessing, setIsProfileImageProcessing] = useState(false);
  const [currentPasswordDraft, setCurrentPasswordDraft] = useState('');
  const [newPasswordDraft, setNewPasswordDraft] = useState('');
  const [newPasswordConfirmDraft, setNewPasswordConfirmDraft] = useState('');
  const [withdrawPasswordDraft, setWithdrawPasswordDraft] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [passwordErrorMessage, setPasswordErrorMessage] = useState('');
  const [withdrawErrorMessage, setWithdrawErrorMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const updateMutation = useMutation({
    mutationFn: (payload: MyPageUpdateRequest) => updateMyPage(payload),
  });
  const nicknameMutation = useMutation({
    mutationFn: (nickname: string) => changeNickname({ nickname }),
  });
  const profileDeleteMutation = useMutation({
    mutationFn: deleteProfileImage,
  });
  const passwordChangeMutation = useMutation({
    mutationFn: changePassword,
  });
  const withdrawMutation = useMutation({
    mutationFn: withdraw,
  });
  const resetOnboardingMutation = useMutation({
    mutationFn: resetOnboarding,
  });

  if (isLoading) {
    return (
      <div className="space-y-5">
        <div className="h-[220px] animate-pulse rounded-[28px] bg-surface-base" />
        <div className="h-[280px] animate-pulse rounded-[24px] bg-surface-base" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <Card className="space-y-4 border-danger-soft bg-surface-danger">
        <h2 className="text-xl font-black text-text-strong">마이페이지를 불러오지 못했습니다</h2>
        <p className="text-sm font-semibold text-text-muted">
          네트워크 상태를 확인한 뒤 다시 시도해주세요.
        </p>
        <Button
          fullWidth={false}
          onClick={() => void refetch()}
          disabled={isFetching}
          variant="outline"
        >
          다시 불러오기
        </Button>
      </Card>
    );
  }

  const initialForm = toInitialForm(data.name, data.birthDate, data.monthlySavingGoalAmount);
  const form = isEditing ? (draftForm ?? initialForm) : initialForm;
  const profileInitial = (data.nickname?.trim()?.[0] ?? 'U').toUpperCase();
  const trimmedName = form.name.trim();
  const initialTrimmedName = initialForm.name.trim();

  const isNameValid = trimmedName.length > 0 && trimmedName.length <= 50;
  const isBirthDateValid =
    form.birthDate.length === 0 || (form.birthDate.length === 10 && form.birthDate <= maxBirthDate);
  const isMonthlyDigits = /^\d+$/.test(form.monthlySavingGoalAmount);
  const monthlyAmount =
    form.monthlySavingGoalAmount.length > 0 && isMonthlyDigits
      ? Number(form.monthlySavingGoalAmount)
      : NaN;
  const isMonthlyValid =
    form.monthlySavingGoalAmount.length > 0 &&
    isMonthlyDigits &&
    Number.isSafeInteger(monthlyAmount) &&
    monthlyAmount >= 0;
  const isChanged =
    trimmedName !== initialTrimmedName ||
    form.birthDate !== initialForm.birthDate ||
    form.monthlySavingGoalAmount !== initialForm.monthlySavingGoalAmount;
  const isSaving = updateMutation.isPending;

  const handleStartEdit = () => {
    setDraftForm(initialForm);
    setIsEditing(true);
  };

  const handleCancel = () => {
    setDraftForm(null);
    setIsEditing(false);
  };

  const handleSave = async () => {
    if (!isEditing) {
      return;
    }

    if (!isChanged) {
      info('변경된 내용이 없습니다.');
      return;
    }

    if (!isNameValid) {
      error('이름은 1~50자로 입력해주세요.');
      return;
    }

    if (!isBirthDateValid) {
      error('생년월일은 오늘 이전 날짜로 입력해주세요.');
      return;
    }

    if (!isMonthlyValid) {
      error('월 저축 목표 금액을 0 이상의 숫자로 입력해주세요.');
      return;
    }

    try {
      await updateMutation.mutateAsync({
        name: trimmedName,
        birthDate: form.birthDate || null,
        monthlySavingGoalAmount: monthlyAmount,
      });
      setDraftForm(null);
      setIsEditing(false);
      queryClient.invalidateQueries({ queryKey: ['myPage'] });
      success('마이페이지 정보가 수정되었습니다.');
    } catch (mutationError) {
      const code = axios.isAxiosError(mutationError)
        ? (mutationError.response?.data as ApiResponse<unknown> | undefined)?.code
        : undefined;
      error(mapMyPageUpdateErrorMessage(code));
    }
  };

  const handleOpenNicknameModal = () => {
    setNicknameDraft(data.nickname);
    setNicknameErrorMessage('');
    setIsNicknameModalOpen(true);
  };

  const handleCloseNicknameModal = () => {
    if (nicknameMutation.isPending) {
      return;
    }
    setIsNicknameModalOpen(false);
    setNicknameErrorMessage('');
  };

  const handleChangeNickname = async () => {
    const nickname = nicknameDraft.trim();
    if (nickname.length < 2 || nickname.length > 20) {
      setNicknameErrorMessage('닉네임은 2자 이상 20자 이하여야 합니다.');
      return;
    }
    if (!NICKNAME_PATTERN.test(nickname)) {
      setNicknameErrorMessage('닉네임은 한글, 영문, 숫자, 밑줄(_)만 사용할 수 있습니다.');
      return;
    }

    try {
      await nicknameMutation.mutateAsync(nickname);
      setIsNicknameModalOpen(false);
      setNicknameErrorMessage('');
      queryClient.invalidateQueries({ queryKey: ['myPage'] });
      success('닉네임이 변경되었습니다.');
    } catch (mutationError) {
      const code = axios.isAxiosError(mutationError)
        ? (mutationError.response?.data as ApiResponse<unknown> | undefined)?.code
        : undefined;
      const message = mapNicknameChangeErrorMessage(code);
      setNicknameErrorMessage(message);
      error(message);
    }
  };

  const handleClickChangeProfileImage = () => {
    fileInputRef.current?.click();
  };

  const handleProfileImageFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = '';

    if (!file) {
      return;
    }

    if (!ALLOWED_PROFILE_IMAGE_TYPES.includes(file.type)) {
      error('jpg, jpeg, png, webp 형식만 업로드할 수 있습니다.');
      return;
    }

    if (file.size <= 0 || file.size > MAX_PROFILE_IMAGE_SIZE_BYTES) {
      error('프로필 이미지는 10MB 이하만 업로드할 수 있습니다.');
      return;
    }

    try {
      setIsProfileImageProcessing(true);
      const presignResponse = await createProfileImagePresign({
        fileName: file.name,
        contentType: file.type,
        contentLength: file.size,
      });

      const { uploadUrl, headers, key } = presignResponse.data;

      await axios.put(uploadUrl, file, {
        headers,
      });

      await completeProfileImage({ key });
      queryClient.invalidateQueries({ queryKey: ['myPage'] });
      success('프로필 이미지가 변경되었습니다.');
    } catch (mutationError) {
      const code = axios.isAxiosError(mutationError)
        ? (mutationError.response?.data as ApiResponse<unknown> | undefined)?.code
        : undefined;
      error(mapProfileImageErrorMessage(code));
    } finally {
      setIsProfileImageProcessing(false);
    }
  };

  const handleDeleteProfileImage = async () => {
    try {
      setIsProfileImageProcessing(true);
      await profileDeleteMutation.mutateAsync();
      queryClient.invalidateQueries({ queryKey: ['myPage'] });
      success('기본 프로필 이미지로 변경되었습니다.');
    } catch (mutationError) {
      const code = axios.isAxiosError(mutationError)
        ? (mutationError.response?.data as ApiResponse<unknown> | undefined)?.code
        : undefined;
      error(mapProfileImageErrorMessage(code));
    } finally {
      setIsProfileImageProcessing(false);
    }
  };

  const handlePasswordSectionSubmit = async () => {
    const currentPassword = currentPasswordDraft.trim();
    const newPassword = newPasswordDraft.trim();
    const newPasswordConfirm = newPasswordConfirmDraft.trim();
    setPasswordErrorMessage('');

    if (currentPassword.length < 8 || newPassword.length < 8 || newPasswordConfirm.length < 8) {
      const message = '비밀번호는 8자 이상이어야 합니다.';
      setPasswordErrorMessage(message);
      error(message);
      return;
    }

    if (
      currentPassword.length > 255 ||
      newPassword.length > 255 ||
      newPasswordConfirm.length > 255
    ) {
      const message = '비밀번호는 255자 이하여야 합니다.';
      setPasswordErrorMessage(message);
      error(message);
      return;
    }

    if (newPassword !== newPasswordConfirm) {
      const message = '새 비밀번호와 새 비밀번호 확인이 일치하지 않습니다.';
      setPasswordErrorMessage(message);
      error(message);
      return;
    }

    if (currentPassword === newPassword) {
      const message = '새 비밀번호는 현재 비밀번호와 달라야 합니다.';
      setPasswordErrorMessage(message);
      error(message);
      return;
    }

    try {
      const response = await passwordChangeMutation.mutateAsync({
        currentPassword,
        newPassword,
      });

      if (response.data.passwordChanged) {
        setCurrentPasswordDraft('');
        setNewPasswordDraft('');
        setNewPasswordConfirmDraft('');
        setPasswordErrorMessage('');
        logout();
        success('비밀번호가 변경되었습니다. 다시 로그인해주세요.');
        navigate('/login', { replace: true });
        return;
      }

      const message = '비밀번호 변경에 실패했습니다.';
      setPasswordErrorMessage(message);
      error(message);
    } catch (mutationError) {
      const code = axios.isAxiosError(mutationError)
        ? (mutationError.response?.data as ApiResponse<unknown> | undefined)?.code
        : undefined;
      const message = mapPasswordChangeErrorMessage(code);
      setPasswordErrorMessage(message);
      error(message);
    }
  };

  const handleWithdrawSectionSubmit = async () => {
    const currentPassword = withdrawPasswordDraft.trim();
    setWithdrawErrorMessage('');

    if (currentPassword.length < 8) {
      const message = '비밀번호는 8자 이상이어야 합니다.';
      setWithdrawErrorMessage(message);
      error(message);
      return;
    }

    if (currentPassword.length > 255) {
      const message = '비밀번호는 255자 이하여야 합니다.';
      setWithdrawErrorMessage(message);
      error(message);
      return;
    }

    const confirmed = window.confirm('정말로 탈퇴하시겠습니까? 이 작업은 되돌릴 수 없습니다.');
    if (!confirmed) {
      return;
    }

    try {
      const response = await withdrawMutation.mutateAsync({
        currentPassword,
      });

      if (response.data.withdrawn) {
        setWithdrawPasswordDraft('');
        setWithdrawErrorMessage('');
        logout();
        success('회원 탈퇴가 완료되었습니다.');
        navigate('/login', { replace: true });
        return;
      }

      const message = '회원 탈퇴에 실패했습니다.';
      setWithdrawErrorMessage(message);
      error(message);
    } catch (mutationError) {
      const code = axios.isAxiosError(mutationError)
        ? (mutationError.response?.data as ApiResponse<unknown> | undefined)?.code
        : undefined;
      const message = mapWithdrawErrorMessage(code);
      setWithdrawErrorMessage(message);
      error(message);
    }
  };

  const handleResetOnboarding = async () => {
    const confirmed = window.confirm(
      '온보딩을 다시 시작하시겠습니까? 현재의 자동 저축 설정이 초기화됩니다.'
    );
    if (!confirmed) return;

    try {
      await resetOnboardingMutation.mutateAsync();
      queryClient.invalidateQueries({ queryKey: ['myPage'] });
      queryClient.invalidateQueries({ queryKey: ['account'] });


      sessionStorage.removeItem('onboarding_step');
      sessionStorage.removeItem('onboarding_isKdt');
      sessionStorage.removeItem('onboarding_fixedCost');
      sessionStorage.removeItem('onboarding_variableCost');

      success('온보딩 단계로 이동합니다. 설정을 다시 진행해 주세요!');
      navigate('/onboarding', { replace: true });
    } catch (mutationError) {
      error('초기화 중 오류가 발생했습니다.');
    }
  };

  const eyeButtonClassName =
    'flex h-8 w-8 items-center justify-center rounded-full transition-colors hover:bg-surface-soft';

  const renderPasswordToggle = (visible: boolean, onClick: () => void) => (
    <button
      type="button"
      onClick={onClick}
      className={eyeButtonClassName}
      aria-label={visible ? '비밀번호 숨기기' : '비밀번호 보기'}
    >
      {visible ? (
        <svg
          className="h-4.5 w-4.5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 3l18 18" />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M10.584 10.587A2 2 0 0013.413 13.416M9.88 5.09A9.953 9.953 0 0112 4.875c4.478 0 8.268 2.943 9.542 7.003a9.97 9.97 0 01-2.231 3.592M6.228 6.228A9.956 9.956 0 002.458 11.878a9.97 9.97 0 005.365 6.08A9.953 9.953 0 0012 19.125c1.41 0 2.751-.293 3.966-.82"
          />
        </svg>
      ) : (
        <svg
          className="h-4.5 w-4.5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
          />
          <circle cx="12" cy="12" r="3" />
        </svg>
      )}
    </button>
  );

  return (
    <div className="mx-auto w-full max-w-5xl space-y-6">
      <Card className="rounded-none border border-line-soft p-0 shadow-none">
        <div className="border-b border-line-soft px-6 py-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-[30px] font-black text-text-strong">프로필</h2>
              <p className="mt-1 text-sm font-medium text-text-muted">
                {isEditing
                  ? '수정 중입니다. 변경 후 적용 버튼을 눌러주세요.'
                  : '기본 정보를 확인할 수 있습니다.'}
              </p>
            </div>
            {!isEditing && (
              <Button fullWidth={false} className="min-w-24" onClick={handleStartEdit}>
                수정
              </Button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-[180px_1fr]">
          <div className="border-b border-line-soft bg-surface-soft px-6 py-8 text-sm font-extrabold text-text-strong">
            프로필 사진
          </div>
          <div className="border-b border-line-soft px-6 py-8">
            <div className="flex items-center gap-5">
              {data.profileImageUrl ? (
                <img
                  src={data.profileImageUrl}
                  alt="프로필 이미지"
                  className="h-24 w-24 rounded-full border border-line-soft object-cover"
                />
              ) : (
                <div className="flex h-24 w-24 items-center justify-center rounded-full border border-line-soft bg-surface-soft text-3xl font-black text-text-muted">
                  {profileInitial}
                </div>
              )}
              <div className="flex gap-2">
                <button
                  type="button"
                  className="border border-line-soft px-3 py-2 text-xs font-bold text-text-strong"
                  onClick={handleClickChangeProfileImage}
                  disabled={isProfileImageProcessing}
                >
                  {isProfileImageProcessing ? '처리 중...' : '사진변경'}
                </button>
                <button
                  type="button"
                  className="border border-line-soft px-3 py-2 text-xs font-bold text-text-muted"
                  onClick={() => void handleDeleteProfileImage()}
                  disabled={isProfileImageProcessing}
                >
                  삭제
                </button>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                onChange={(event) => void handleProfileImageFileChange(event)}
              />
            </div>
          </div>

          <div className="border-b border-line-soft bg-surface-soft px-6 py-6 text-sm font-extrabold text-text-strong">
            닉네임
          </div>
          <div className="border-b border-line-soft px-6 py-6">
            <div className="flex items-center justify-between gap-3">
              <p className="text-[15px] font-semibold text-text-strong">{data.nickname}</p>
              <Button
                fullWidth={false}
                variant="outline"
                className="min-w-20 px-3 py-2 text-xs"
                onClick={handleOpenNicknameModal}
                disabled={nicknameMutation.isPending}
              >
                닉네임 변경
              </Button>
            </div>
          </div>

          <div className="border-b border-line-soft bg-surface-soft px-6 py-6 text-sm font-extrabold text-text-strong">
            이름
          </div>
          <div className="border-b border-line-soft px-6 py-4">
            {isEditing ? (
              <input
                value={form.name}
                maxLength={50}
                onChange={(event) =>
                  setDraftForm((prev) => ({
                    ...(prev ?? initialForm),
                    name: event.target.value,
                  }))
                }
                disabled={isSaving}
                className="w-full rounded-[8px] border border-line-soft px-3 py-2 text-[15px] font-semibold text-text-strong outline-none transition-colors focus:border-accent"
                placeholder="이름을 입력하세요"
              />
            ) : (
              <p className="py-2 text-[15px] font-semibold text-text-strong">{form.name || '-'}</p>
            )}
          </div>

          <div className="border-b border-line-soft bg-surface-soft px-6 py-6 text-sm font-extrabold text-text-strong">
            이메일
          </div>
          <div className="border-b border-line-soft px-6 py-6 text-[15px] font-semibold text-text-strong">
            {data.email}
          </div>

          <div className="border-b border-line-soft bg-surface-soft px-6 py-6 text-sm font-extrabold text-text-strong">
            생년월일
          </div>
          <div className="border-b border-line-soft px-6 py-4">
            {isEditing ? (
              <BirthDateField
                className="mt-0"
                value={form.birthDate}
                max={maxBirthDate}
                onChange={(value) =>
                  setDraftForm((prev) => ({
                    ...(prev ?? initialForm),
                    birthDate: value,
                  }))
                }
                disabled={isSaving}
              />
            ) : (
              <p className="py-2 text-[15px] font-semibold text-text-strong">
                {form.birthDate ? formatBirthDateLabel(form.birthDate) : '-'}
              </p>
            )}
          </div>

          <div className="border-b border-line-soft bg-surface-soft px-6 py-6 text-sm font-extrabold text-text-strong">
            월 저축 목표 금액
          </div>
          <div className="border-b border-line-soft px-6 py-4">
            {isEditing ? (
              <input
                type="text"
                inputMode="numeric"
                value={form.monthlySavingGoalAmount}
                onChange={(event) =>
                  setDraftForm((prev) => ({
                    ...(prev ?? initialForm),
                    monthlySavingGoalAmount: event.target.value.replace(/[^0-9]/g, ''),
                  }))
                }
                disabled={isSaving}
                className="w-full rounded-[8px] border border-line-soft px-3 py-2 text-[15px] font-semibold text-text-strong outline-none transition-colors focus:border-accent"
                placeholder="예: 300000"
              />
            ) : (
              <p className="py-2 text-[15px] font-semibold text-text-strong">
                {formatAmountLabel(form.monthlySavingGoalAmount)}
              </p>
            )}
          </div>

          <div className="bg-surface-soft px-6 py-6 text-sm font-extrabold text-text-strong">
            기수 번호
          </div>
          <div className="px-6 py-6 text-[15px] font-semibold text-text-strong">
            {data.cohortGenerationNo ? `${data.cohortGenerationNo}기` : '-'}
          </div>
        </div>

        {isEditing && (
          <div className="flex justify-center gap-3 border-t border-line-soft px-6 py-5">
            <Button fullWidth={false} variant="outline" className="min-w-24" onClick={handleCancel}>
              취소
            </Button>
            <Button
              fullWidth={false}
              className="min-w-24"
              onClick={() => void handleSave()}
              disabled={
                isSaving || !isChanged || !isNameValid || !isBirthDateValid || !isMonthlyValid
              }
            >
              {isSaving ? '저장 중...' : '적용'}
            </Button>
          </div>
        )}
      </Card>

      <Card className="rounded-none border border-line-soft p-0 shadow-none">
        <div className="border-b border-line-soft px-6 py-5">
          <h3 className="text-[24px] font-black text-text-strong">비밀번호 변경</h3>
          <p className="mt-1 text-sm font-medium text-text-muted">
            본인 확인 후 새 비밀번호로 변경할 수 있습니다.
          </p>
        </div>
        <div className="space-y-1 px-6 py-5">
          <Input
            className="mt-0"
            label="현재 비밀번호"
            type="password"
            value={currentPasswordDraft}
            onChange={(event) => {
              setCurrentPasswordDraft(event.target.value);
              if (passwordErrorMessage) {
                setPasswordErrorMessage('');
              }
            }}
            placeholder="현재 비밀번호를 입력하세요"
          />
          <Input
            label="새 비밀번호"
            type={showNewPassword ? 'text' : 'password'}
            value={newPasswordDraft}
            onChange={(event) => {
              setNewPasswordDraft(event.target.value);
              if (passwordErrorMessage) {
                setPasswordErrorMessage('');
              }
            }}
            placeholder="8자 이상 입력하세요"
            endAdornment={renderPasswordToggle(showNewPassword, () =>
              setShowNewPassword((prev) => !prev)
            )}
          />
          <Input
            label="새 비밀번호 확인"
            type={showNewPassword ? 'text' : 'password'}
            value={newPasswordConfirmDraft}
            onChange={(event) => {
              setNewPasswordConfirmDraft(event.target.value);
              if (passwordErrorMessage) {
                setPasswordErrorMessage('');
              }
            }}
            placeholder="새 비밀번호를 다시 입력하세요"
          />
          {passwordErrorMessage && (
            <p className="mt-2 text-[12px] font-semibold text-danger">{passwordErrorMessage}</p>
          )}
        </div>
        <div className="flex justify-end border-t border-line-soft px-6 py-5">
          <Button
            fullWidth={false}
            className="min-w-28"
            onClick={() => void handlePasswordSectionSubmit()}
            disabled={
              !currentPasswordDraft ||
              !newPasswordDraft ||
              !newPasswordConfirmDraft ||
              passwordChangeMutation.isPending
            }
          >
            {passwordChangeMutation.isPending ? '변경 중...' : '비밀번호 변경'}
          </Button>
        </div>
      </Card>

      <Card className="rounded-none border border-line-soft p-0 shadow-none">
        <div className="border-b border-line-soft px-6 py-5">
          <h3 className="text-[24px] font-black text-text-strong">온보딩 다시하기</h3>
          <p className="mt-1 text-sm font-medium text-text-muted">
            자동 저축 규칙을 다시 설정하고 추천 저축액을 새롭게 계산합니다.
          </p>
        </div>
        <div className="flex justify-between items-center px-6 py-5">
          <div className="text-sm font-semibold text-text-muted">
            온보딩 정보 및 저축 규칙 재설정
          </div>
          <Button
            fullWidth={false}
            variant="outline"
            className="border-danger text-danger hover:bg-danger/5"
            onClick={() => void handleResetOnboarding()}
            disabled={resetOnboardingMutation.isPending}
          >
            온보딩 다시하기
          </Button>
        </div>
      </Card>

      <Card className="rounded-none border border-danger-soft p-0 shadow-none">
        <div className="border-b border-danger-soft bg-surface-danger px-6 py-5">
          <h3 className="text-[24px] font-black text-danger">회원 탈퇴</h3>
          <p className="mt-1 text-sm font-semibold text-text-muted">
            탈퇴 시 계정 사용이 중단됩니다. 신중하게 진행해주세요.
          </p>
        </div>
        <div className="space-y-1 px-6 py-5">
          <Input
            className="mt-0"
            label="현재 비밀번호 확인"
            type="password"
            value={withdrawPasswordDraft}
            onChange={(event) => {
              setWithdrawPasswordDraft(event.target.value);
              if (withdrawErrorMessage) {
                setWithdrawErrorMessage('');
              }
            }}
            placeholder="탈퇴 확인을 위해 비밀번호를 입력하세요"
            error={!!withdrawErrorMessage}
            errorMessage={withdrawErrorMessage}
          />
        </div>
        <div className="flex justify-end border-t border-danger-soft px-6 py-5">
          <Button
            fullWidth={false}
            className="min-w-24 border-danger-strong bg-danger-strong text-white shadow-none hover:border-danger hover:bg-danger"
            onClick={() => void handleWithdrawSectionSubmit()}
            disabled={!withdrawPasswordDraft || withdrawMutation.isPending}
          >
            {withdrawMutation.isPending ? '처리 중...' : '탈퇴하기'}
          </Button>
        </div>
      </Card>

      <Modal
        isOpen={isNicknameModalOpen}
        onClose={handleCloseNicknameModal}
        title="닉네임 변경"
        closeOnBackdropClick={false}
        footer={
          <div className="flex justify-end gap-2">
            <Button
              fullWidth={false}
              variant="outline"
              className="min-w-20 px-4 py-2 text-sm"
              onClick={handleCloseNicknameModal}
              disabled={nicknameMutation.isPending}
            >
              취소
            </Button>
            <Button
              fullWidth={false}
              className="min-w-20 px-4 py-2 text-sm"
              onClick={() => void handleChangeNickname()}
              disabled={nicknameMutation.isPending}
            >
              {nicknameMutation.isPending ? '변경 중...' : '변경'}
            </Button>
          </div>
        }
      >
        <Input
          className="mt-0"
          label="새 닉네임"
          value={nicknameDraft}
          onChange={(event) => {
            setNicknameDraft(event.target.value);
            if (nicknameErrorMessage) {
              setNicknameErrorMessage('');
            }
          }}
          maxLength={20}
          placeholder="2~20자, 한글/영문/숫자/_"
          error={!!nicknameErrorMessage}
          errorMessage={nicknameErrorMessage}
          disabled={nicknameMutation.isPending}
        />
      </Modal>
    </div>
  );
};
