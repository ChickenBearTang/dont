/**
 * 숫자 관련 포맷팅 유틸리티
 */

/**
 * 숫자를 한국어 통화 형식(원)으로 변환합니다.
 * @param amount 금액
 * @returns 포맷팅된 문자열 (예: 10,000원)
 */
export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('ko-KR').format(amount) + '원';
};

/**
 * 숫자에 콤마(,)를 추가합니다.
 * @param num 숫자
 * @returns 콤마가 포함된 문자열
 */
export const formatNumber = (num: number): string => {
  return new Intl.NumberFormat('ko-KR').format(num);
};

/**
 * 큰 수(만, 억 단위)를 한글 단위로 변환합니다.
 * @param amount 금액
 * @returns 한글 단위 문자열 (예: 1.2만)
 */
export const formatKoreanUnit = (amount: number): string => {
  if (amount >= 100000000) {
    return (amount / 100000000).toFixed(1).replace(/\.0$/, '') + '억';
  }
  if (amount >= 10000) {
    return (amount / 10000).toFixed(1).replace(/\.0$/, '') + '만';
  }
  return formatNumber(amount);
};
