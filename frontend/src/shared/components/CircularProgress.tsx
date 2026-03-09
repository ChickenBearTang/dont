import React from 'react';

interface CircularProgressProps {
  progress: number;
  size?: number;
}

export const CircularProgress = ({ progress, size = 120 }: CircularProgressProps) => {
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (progress / 100) * circumference;

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
        <circle
          className="fill-none stroke-[#f0f4f8] stroke-[8px]"
          cx="50"
          cy="50"
          r={radius}
        ></circle>
        <circle
          className="fill-none stroke-primary-blue stroke-[8px] transition-[stroke-dashoffset] duration-1000 ease-out"
          cx="50"
          cy="50"
          r={radius}
          strokeLinecap="round"
          style={{
            strokeDasharray: circumference,
            strokeDashoffset: offset,
          }}
        ></circle>
      </svg>
      <div className="absolute font-black text-[28px] text-eel">
        {progress}%
      </div>
    </div>
  );
};
