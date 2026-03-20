import type { CSSProperties } from 'react';

interface MascotProps {
  src: string;
  speech?: string;
  className?: string;
  style?: CSSProperties;
}

export const Mascot = ({ src, speech, className = '', style = {} }: MascotProps) => (
  <div className={`flex flex-col items-center gap-6 ${className}`}>
    <div className="relative">
      <img
        src={src}
        alt="Mascot"
        className="w-[180px] lg:w-[220px] h-auto drop-shadow-2xl object-contain animate-bounce-slow"
        style={style}
      />

      {speech && (
        <div className="absolute -top-8 -right-8 lg:-right-12 bg-white rounded-3xl rounded-bl-none px-6 py-4 shadow-[0_10px_30px_rgba(0,0,0,0.08)] border border-gray-50 font-bold text-[14px] lg:text-[16px] text-gray-800 leading-relaxed max-w-[220px] lg:max-w-[280px] break-keep">
          {speech}
          <div className="absolute bottom-[-6px] left-0 w-4 h-4 bg-white border-l border-b border-gray-50 rotate-45 -translate-x-1/2"></div>
        </div>
      )}
    </div>
  </div>
);
