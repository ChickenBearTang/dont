import axios from 'axios';
import { useMemo, useRef, useState, type ChangeEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { BirthDateField, Button, Card, Input, Modal } from '@/shared/components';
import {
  changeNickname,
  completeProfileImage,
  createProfileImagePresign,
  deleteProfileImage,
  fetchMyPage,
  updateMyPage,
} from '@/features/user/api/userApi';
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

export const MyPagePage = () => {
  const { success, error, info } = useToast();
  const queryClient = useQueryClient();
  const maxBirthDate = useMemo(() => getTodayMinusOne(), []);

  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['myPage'],
    queryFn: fetchMyPage,
    select: (response) => response.data,
  });

  const [draftForm, setDraftForm] = useState<MyPageFormState | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isNicknameModalOpen, setIsNicknameModalOpen] = useState(false);
  const [nicknameDraft, setNicknameDraft] = useState('');
  const [nicknameErrorMessage, setNicknameErrorMessage] = useState('');
  const [isProfileImageProcessing, setIsProfileImageProcessing] = useState(false);
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

  return (
    <div className="mx-auto w-full max-w-5xl">
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
