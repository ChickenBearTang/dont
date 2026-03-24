import { useUIStore } from '@/shared/store/useUIStore';
import type { ToastType } from '@/shared/store/useUIStore';

export const ToastContainer = () => {
  const { toasts, removeToast } = useUIStore();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 left-1/2 -translate-x-1/2 z-[100] flex flex-col gap-2 w-[90%] max-w-sm pointer-events-none">
      {toasts.map((toast) => {
        const bgColors: Record<ToastType, string> = {
          success: 'bg-[#00c853]',
          error: 'bg-[#ff3b3b]',
          info: 'bg-[#333333]',
        };

        return (
          <div
            key={toast.id}
            className={`${bgColors[toast.type]} text-white px-5 py-4 rounded-xl shadow-lg flex items-center justify-between pointer-events-auto transform transition-all duration-300 animate-slide-down`}
          >
            <span className="font-semibold text-[15px]">{toast.message}</span>
            <button
              onClick={() => removeToast(toast.id)}
              className="ml-4 opacity-70 hover:opacity-100 transition-opacity"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        );
      })}
    </div>
  );
};
