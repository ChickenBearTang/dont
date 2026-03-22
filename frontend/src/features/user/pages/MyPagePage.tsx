import { useQuery } from '@tanstack/react-query';
import { Button, Card } from '@/shared/components';
import { fetchMyPage } from '@/features/user/api/userApi';

const formatBirthDate = (birthDate: string | null) => {
  if (!birthDate) return '-';
  const [year, month, day] = birthDate.split('-');
  if (!year || !month || !day) return birthDate;
  return `${year}.${month}.${day}`;
};

export const MyPagePage = () => {
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['myPage'],
    queryFn: fetchMyPage,
    select: (response) => response.data,
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

  const profileInitial = (data.nickname?.trim()?.[0] ?? 'U').toUpperCase();

  return (
    <div className="mx-auto w-full max-w-5xl">
      <Card className="rounded-none border border-line-soft p-0 shadow-none">
        <div className="border-b border-line-soft px-6 py-5">
          <h2 className="text-[30px] font-black text-text-strong">프로필</h2>
          <p className="mt-1 text-sm font-medium text-text-muted">
            기본 정보를 확인하고, 다음 단계에서 수정 기능을 연결합니다.
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
                <button className="border border-line-soft px-3 py-2 text-xs font-bold text-text-strong">
                  사진변경
                </button>
                <button className="border border-line-soft px-3 py-2 text-xs font-bold text-text-muted">
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
          <div className="border-b border-line-soft px-6 py-6 text-[15px] font-semibold text-text-strong">
            {data.name || '-'}
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
          <div className="border-b border-line-soft px-6 py-6 text-[15px] font-semibold text-text-strong">
            {formatBirthDate(data.birthDate)}
          </div>

          <div className="bg-surface-soft px-6 py-6 text-sm font-extrabold text-text-strong">
            기수 번호
          </div>
          <div className="px-6 py-6 text-[15px] font-semibold text-text-strong">
            {data.cohortGenerationNo ? `${data.cohortGenerationNo}기` : '-'}
          </div>
        </div>

        <div className="flex justify-center gap-3 border-t border-line-soft px-6 py-5">
          <Button fullWidth={false} variant="outline" className="min-w-24">
            취소
          </Button>
          <Button fullWidth={false} className="min-w-24">
            적용
          </Button>
        </div>
      </Card>
    </div>
  );
};
