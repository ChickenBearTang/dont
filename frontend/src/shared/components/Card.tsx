import type { ReactNode, HTMLAttributes } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export const Card = ({ children, className = '', ...props }: CardProps) => (
  <div
    className={`relative bg-glass rounded-[24px] p-7 transition-all duration-300 hover:shadow-[0_12px_44px_rgba(31,38,135,0.08)] hover:-translate-y-1 overflow-hidden group ${className}`}
    {...props}
  >
    {}
    <div className="absolute inset-0 bg-pattern-dots opacity-[0.6] pointer-events-none mix-blend-overlay"></div>

    {}
    <div className="relative z-10 h-full">{children}</div>
  </div>
);
