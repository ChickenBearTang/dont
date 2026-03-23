interface ProgressBarProps {
  progress: number;
  label?: string;
  className?: string;
}

export const ProgressBar = ({ progress, label, className = '' }: ProgressBarProps) => (
  <div className={`w-full ${className}`}>
    <div className="w-full h-2 bg-[#f0f4f8] rounded-full overflow-hidden">
      <div
        className="h-full bg-primary-blue rounded-full transition-all duration-400 ease-[cubic-bezier(0.17,0.67,0.83,1.3)]"
        style={{ width: `${progress}%` }}
      ></div>
    </div>
    {label && <p className="mt-2 text-center text-gray font-extrabold pb-0">{label}</p>}
  </div>
);
