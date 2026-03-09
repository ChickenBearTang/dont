import React from 'react';

interface MascotProps {
  src: string;
  speech?: string;
  className?: string;
  style?: React.CSSProperties;
}

export const Mascot = ({ src, speech, className = '', style = {} }: MascotProps) => (
  <div className={`flex flex-col items-center gap-2 ${className}`}>
    {speech && (
      <div className="relative bg-white rounded-[20px] px-[1.6rem] py-[1rem] shadow-[0_4px_15px_rgba(0,0,0,0.06)] font-bold text-[15px] text-center text-eel leading-[1.5] max-w-[80%] break-keep before:content-[''] before:absolute before:bottom-[-9px] before:left-1/2 before:-translate-x-1/2 before:-translate-y-px before:border-l-[10px] before:border-l-transparent before:border-r-[10px] before:border-r-transparent before:border-t-[10px] before:border-t-white after:content-[''] after:absolute after:bottom-[-10px] after:left-1/2 after:-translate-x-1/2 after:border-l-[10px] after:border-l-transparent after:border-r-[10px] after:border-r-transparent after:border-t-[10px] after:border-t-[rgba(0,0,0,0.03)] after:-z-10">
        {speech}
      </div>
    )}
    <img
      src={src}
      alt="Mascot"
      className="w-[120px] h-auto drop-shadow-[0_10px_20px_rgba(0,0,0,0.1)] object-contain"
      style={style}
    />
  </div>
);
