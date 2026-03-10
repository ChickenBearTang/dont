interface CircularProgressProps {
  progress: number;
  size?: number;
  strokeWidth?: number;
  className?: string;
}

export const CircularProgress = ({ 
  progress, 
  size = 120, 
  strokeWidth = 8, 
  className = '' 
}: CircularProgressProps) => {
  const radius = 50 - strokeWidth / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (progress / 100) * circumference;

  return (
    <div className={`relative flex items-center justify-center ${className}`} style={{ width: size, height: size }}>
      <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
        <circle
          className="fill-none stroke-gray-100"
          cx="50"
          cy="50"
          r={radius}
          strokeWidth={strokeWidth}
        ></circle>
        <circle
          className="fill-none stroke-current transition-[stroke-dashoffset] duration-1000 ease-out"
          cx="50"
          cy="50"
          r={radius}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          style={{
            strokeDasharray: circumference,
            strokeDashoffset: offset,
          }}
        ></circle>
      </svg>
    </div>
  );
};
