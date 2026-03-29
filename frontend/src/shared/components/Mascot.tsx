import type { CSSProperties } from 'react';

interface MascotProps {
  src: string;
  speech?: string;
  className?: string;
  style?: CSSProperties;
}

export const Mascot = ({ src, speech, className = '', style = {} }: MascotProps) => (
  <div className={`flex flex-col items-center gap-6 ${className}`}>
    <div className="relative inline-block">
      <img
        src={src}
        alt="Mascot"
        className="w-[180px] lg:w-[220px] h-auto drop-shadow-2xl object-contain animate-bounce-slow"
        style={style}
      />

      {speech && (
        <div className="absolute bottom-[85%] left-[60%] lg:bottom-[80%] lg:left-[70%] bg-white/70 backdrop-blur-md rounded-2xl px-4 lg:px-5 py-3 lg:py-4 shadow-[0_8px_24px_rgba(30,58,138,0.08)] font-bold text-[13px] lg:text-[14px] text-gray-800 leading-[1.5] w-max max-w-[200px] lg:max-w-[240px] break-keep tracking-tight z-20 transition-all duration-700 hover:scale-[1.02] hover:-rotate-1">
          <span className="relative z-10">{speech}</span>

          {}
          <svg
            className="absolute -bottom-[12px] left-[16px] w-[20px] h-[16px] text-white/70 drop-shadow-[0_4px_8px_rgba(30,58,138,0.05)]"
            viewBox="0 0 24 20"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M4 0 L24 0 L0 20 Z" fill="currentColor" />
          </svg>
        </div>
      )}
    </div>
  </div>
);
