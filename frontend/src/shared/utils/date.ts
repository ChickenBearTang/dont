


export const formatDate = (date: Date | string | number): string => {
  const d = new Date(date);
  const year = String(d.getFullYear()).slice(-2);
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}.${month}.${day}`;
};


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


export const isToday = (date: Date | string | number): boolean => {
  const d = new Date(date);
  const today = new Date();

  return (
    d.getDate() === today.getDate() &&
    d.getMonth() === today.getMonth() &&
    d.getFullYear() === today.getFullYear()
  );
};
