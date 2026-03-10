import type { ReactNode } from 'react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  footer?: ReactNode;
}

export const Modal = ({ isOpen, onClose, title, children, footer }: ModalProps) => {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-5 z-[999] animate-[fadeInEffect_0.2s_ease-out_forwards]"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-[24px] w-full max-w-[400px] overflow-hidden shadow-[0_10px_40px_rgba(0,0,0,0.15)] animate-[slideUp_0.3s_cubic-bezier(0.17,0.67,0.83,1.3)_forwards]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center p-6 border-b border-[#f0f4f8]">
          <h2 className="m-0 text-[18px] font-extrabold text-eel">{title}</h2>
          <button
            onClick={onClose}
            className="bg-transparent border-none text-[28px] cursor-pointer text-[#afafaf] hover:text-eel transition-colors p-0 leading-none"
          >
            ×
          </button>
        </div>
        <div className="p-6">{children}</div>
        {footer && <div className="p-6 bg-[#f8f9fa] border-t border-[#f0f4f8]">{footer}</div>}
      </div>
    </div>
  );
};
