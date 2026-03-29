import type { ReactNode } from 'react';

interface LinkifiedTextProps {
  text: string;
  className?: string;
}

const URL_PATTERN = /(https?:\/\/[^\s]+|www\.[^\s]+)/gi;
const TRAILING_PUNCTUATION = /[),.!?:;]+$/;

const splitTrailingPunctuation = (value: string) => {
  let linkText = value;
  let trailing = '';

  while (TRAILING_PUNCTUATION.test(linkText)) {
    trailing = linkText.at(-1)! + trailing;
    linkText = linkText.slice(0, -1);
  }

  return { linkText, trailing };
};

const normalizeHref = (value: string) =>
  value.startsWith('www.') ? `https://${value}` : value;

export const LinkifiedText = ({ text, className }: LinkifiedTextProps) => {
  const matches = Array.from(text.matchAll(URL_PATTERN));
  const combinedClassName = ['block', className].filter(Boolean).join(' ');

  if (matches.length === 0) {
    return <span className={combinedClassName}>{text}</span>;
  }

  const nodes: ReactNode[] = [];
  let currentIndex = 0;

  matches.forEach((match, index) => {
    const rawValue = match[0];
    const matchIndex = match.index ?? 0;

    if (matchIndex > currentIndex) {
      nodes.push(text.slice(currentIndex, matchIndex));
    }

    const { linkText, trailing } = splitTrailingPunctuation(rawValue);

    if (linkText) {
      nodes.push(
        <a
          key={`${linkText}-${matchIndex}-${index}`}
          href={normalizeHref(linkText)}
          target="_blank"
          rel="noreferrer noopener"
          className="text-blue-600 underline underline-offset-2 break-all hover:text-blue-700"
        >
          {linkText}
        </a>
      );
    }

    if (trailing) {
      nodes.push(trailing);
    }

    currentIndex = matchIndex + rawValue.length;
  });

  if (currentIndex < text.length) {
    nodes.push(text.slice(currentIndex));
  }

  return <span className={combinedClassName}>{nodes}</span>;
};
