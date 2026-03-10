import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Tailwind 클래스들을 조건부로 병합하고 충돌을 해결하는 유틸리티입니다.
 * @param inputs 클래스 값들
 * @returns 병합된 클래스 문자열
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
