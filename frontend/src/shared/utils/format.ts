


export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('ko-KR').format(amount) + '원';
};


export const formatNumber = (num: number): string => {
  return new Intl.NumberFormat('ko-KR').format(num);
};


export const formatKoreanUnit = (amount: number): string => {
  if (amount >= 100000000) {
    return (amount / 100000000).toFixed(1).replace(/\.0$/, '') + '억';
  }
  if (amount >= 10000) {
    return (amount / 10000).toFixed(1).replace(/\.0$/, '') + '만';
  }
  return formatNumber(amount);
};
