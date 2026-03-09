import React from 'react';

export const Mascot = ({ src, speech, className = '', style = {} }) => (
  <div className={`mascot-container ${className}`}>
    {speech && <div className="speech-bubble">{speech}</div>}
    <img src={src} alt="Mascot" className="mascot-img" style={style} />
  </div>
);

export const ProgressBar = ({ progress, label }) => (
  <div style={{ width: '100%' }}>
    <div className="progress-bar-container">
      <div className="progress-bar-fill" style={{ width: `${progress}%` }}></div>
    </div>
    {label && (
      <p className="mt-2 text-center" style={{ color: 'var(--gray)', fontWeight: '800' }}>
        {label}
      </p>
    )}
  </div>
);

export const CircularProgress = ({ progress, size = 120 }) => {
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (progress / 100) * circumference;

  return (
    <div className="circular-progress-container" style={{ width: size, height: size }}>
      <svg className="circular-progress-svg" viewBox="0 0 100 100">
        <circle className="progress-bg" cx="50" cy="50" r={radius}></circle>
        <circle
          className="progress-bar"
          cx="50"
          cy="50"
          r={radius}
          style={{
            strokeDasharray: circumference,
            strokeDashoffset: offset,
          }}
        ></circle>
      </svg>
      <div className="progress-text">{progress}%</div>
    </div>
  );
};
