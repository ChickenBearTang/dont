import axios from 'axios';
import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, Card } from '@/shared/components';
import { fetchMyPage, updateMyPage } from '@/features/user/api/userApi';
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

  const updateMutation = useMutation({
    mutationFn: (payload: MyPageUpdateRequest) => updateMyPage(payload),
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
  const form = draftForm ?? initialForm;
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

  const handleCancel = () => {
    setDraftForm(null);
  };

  const handleSave = async () => {
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
      queryClient.invalidateQueries({ queryKey: ['myPage'] });
      success('마이페이지 정보가 수정되었습니다.');
    } catch (mutationError) {
      const code = axios.isAxiosError(mutationError)
        ? (mutationError.response?.data as ApiResponse<unknown> | undefined)?.code
        : undefined;
      error(mapMyPageUpdateErrorMessage(code));
    }
  };

  return (
    <div className="mx-auto w-full max-w-5xl">
      <Card className="rounded-none border border-line-soft p-0 shadow-none">
        <div className="border-b border-line-soft px-6 py-5">
          <h2 className="text-[30px] font-black text-text-strong">프로필</h2>
          <p className="mt-1 text-sm font-medium text-text-muted">
            이름과 생년월일을 수정할 수 있습니다.
          </p>
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
                >
                  사진변경
                </button>
                <button
                  type="button"
                  className="border border-line-soft px-3 py-2 text-xs font-bold text-text-muted"
                >
                  삭제
                </button>
              </div>
            </div>
          </div>

          <div className="border-b border-line-soft bg-surface-soft px-6 py-6 text-sm font-extrabold text-text-strong">
            닉네임
          </div>
          <div className="border-b border-line-soft px-6 py-6 text-[15px] font-semibold text-text-strong">
            {data.nickname}
          </div>

          <div className="border-b border-line-soft bg-surface-soft px-6 py-6 text-sm font-extrabold text-text-strong">
            이름
          </div>
          <div className="border-b border-line-soft px-6 py-4">
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
            <input
              type="date"
              value={form.birthDate}
              max={maxBirthDate}
              onChange={(event) =>
                setDraftForm((prev) => ({
                  ...(prev ?? initialForm),
                  birthDate: event.target.value,
                }))
              }
              disabled={isSaving}
              className="w-full rounded-[8px] border border-line-soft px-3 py-2 text-[15px] font-semibold text-text-strong outline-none transition-colors focus:border-accent"
            />
          </div>

          <div className="border-b border-line-soft bg-surface-soft px-6 py-6 text-sm font-extrabold text-text-strong">
            월 저축 목표 금액
          </div>
          <div className="border-b border-line-soft px-6 py-4">
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
          </div>

          <div className="bg-surface-soft px-6 py-6 text-sm font-extrabold text-text-strong">
            기수 번호
          </div>
          <div className="px-6 py-6 text-[15px] font-semibold text-text-strong">
            {data.cohortGenerationNo ? `${data.cohortGenerationNo}기` : '-'}
          </div>
        </div>

        <div className="flex justify-center gap-3 border-t border-line-soft px-6 py-5">
          <Button
            fullWidth={false}
            variant="outline"
            className="min-w-24"
            onClick={handleCancel}
            disabled={isSaving || !isChanged}
          >
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
      </Card>
    </div>
  );
};
