import React from 'react';

export const Button = ({ children, variant = 'primary', className = '', ...props }) => {
  const baseClass =
    variant === 'primary'
      ? 'btn-primary'
      : variant === 'outline'
        ? 'btn-outline'
        : variant === 'oauth'
          ? 'btn-oauth'
          : '';

  return (
    <button className={`${baseClass} ${className}`} {...props}>
      {children}
    </button>
  );
};

export const Card = ({ children, className = '', ...props }) => (
  <div className={`card ${className}`} {...props}>
    {children}
  </div>
);

export const Input = ({ label, unit, className = '', ...props }) => (
  <div className={`mt-4 ${className}`}>
    {label && (
      <label style={{ fontWeight: '800', fontSize: '15px', color: 'var(--eel)' }}>{label}</label>
    )}
    <div className={unit ? 'input-with-unit mt-2' : 'mt-2'}>
      <input {...props} />
      {unit && <span className="input-unit-text">{unit}</span>}
    </div>
  </div>
);

export const Modal = ({ isOpen, onClose, title, children, footer }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{title}</h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '28px',
              cursor: 'pointer',
              color: '#afafaf',
            }}
          >
            ×
          </button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  );
};
