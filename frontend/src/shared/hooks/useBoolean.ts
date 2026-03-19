import { useState, useCallback } from 'react';

/**
 * 불리언 상태를 다루는 간단한 훅 (모달, 토글 등에 유용)
 */
export const useBoolean = (initialValue = false) => {
  const [value, setValue] = useState(initialValue);

  const toggle = useCallback(() => setValue((v) => !v), []);
  const setTrue = useCallback(() => setValue(true), []);
  const setFalse = useCallback(() => setValue(false), []);

  return [value, { toggle, setTrue, setFalse, setValue }] as const;
};
