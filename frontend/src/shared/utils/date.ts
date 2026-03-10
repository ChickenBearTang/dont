/**
 * 날짜 관련 포맷팅 유틸리티
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
 * 날짜를 "N분 전", "N시간 전" 등 상대적인 시간으로 표현합니다.
 */
export const formatRelativeTime = (date: Date | string | number): string => {
  const start = new Date(date).getTime();
  const end = new Date().getTime();
  const diff = (end - start) / 1000;

  const times = [
    { name: '년', milliSeconds: 60 * 60 * 24 * 365 },
    { name: '개월', milliSeconds: 60 * 60 * 24 * 30 },
    { name: '일', milliSeconds: 60 * 60 * 24 },
    { name: '시간', milliSeconds: 60 * 60 },
    { name: '분', milliSeconds: 60 },
  ];

  for (const value of times) {
    const betweenTime = Math.floor(diff / value.milliSeconds);
    if (betweenTime > 0) {
      return `${betweenTime}${value.name} 전`;
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
