/**
 * 날짜 관련 유틸리티
 */

/**
 * 날짜를 YY.MM.DD 형식으로 변환합니다.
 */
export const formatDate = (date: Date | string | number): string => {
  const d = new Date(date);
  const year = String(d.getFullYear()).slice(-2);
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}.${month}.${day}`;
};

/**
 * 날짜를 "N분 전", "N시간 전" 같은 상대 시간으로 표현합니다.
 */
export const formatRelativeTime = (date: Date | string | number): string => {
  const start = new Date(date).getTime();
  const end = new Date().getTime();
  const diff = (end - start) / 1000;

  if (Number.isNaN(diff) || diff < 0) {
    return '방금 전';
  }

  const units = [
    { label: '년', seconds: 60 * 60 * 24 * 365 },
    { label: '개월', seconds: 60 * 60 * 24 * 30 },
    { label: '일', seconds: 60 * 60 * 24 },
    { label: '시간', seconds: 60 * 60 },
    { label: '분', seconds: 60 },
  ];

  for (const unit of units) {
    const value = Math.floor(diff / unit.seconds);
    if (value > 0) {
      return `${value}${unit.label} 전`;
    }
  }

  return '방금 전';
};

/**
 * 특정 날짜가 오늘인지 확인합니다.
 */
export const isToday = (date: Date | string | number): boolean => {
  const d = new Date(date);
  const today = new Date();

  return (
    d.getDate() === today.getDate() &&
    d.getMonth() === today.getMonth() &&
    d.getFullYear() === today.getFullYear()
  );
};
