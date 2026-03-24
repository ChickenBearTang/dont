import type { UserProfile } from '@/features/auth/types';
import { useNavigate, useLocation } from 'react-router-dom';
import { useNotificationStore } from '@/features/community/store/useNotificationStore';
import { useEffect, useState, useRef } from 'react';
import bellIcon from '@/assets/logo/bell-icon.png';
import profileIcon from '@/assets/logo/profile.png';

interface HeaderProps {
  user: UserProfile | null;
  onLogout: () => void;
  isAuthenticated: boolean;
}

/**
 * 전역 상단 네비게이션바 컴포넌트
 */
const Header = ({ user, onLogout, isAuthenticated }: HeaderProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  const dropdownRef = useRef<HTMLDivElement>(null);

  const {
    unreadCount,
    notifications,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    dismissNotification,
    startPolling,
    stopPolling,
  } = useNotificationStore();

  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      startPolling();
    } else {
      stopPolling();
    }
    return () => stopPolling();
  }, [isAuthenticated, startPolling, stopPolling]);

  useEffect(() => {
    if (isDropdownOpen) {
      fetchNotifications();
    }
  }, [isDropdownOpen, fetchNotifications]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleNotificationClick = async (notif: (typeof notifications)[0]) => {
    if (!notif.isRead) {
      await markAsRead(notif.notificationId);
    }

    setIsDropdownOpen(false);

    if (notif.postId && notif.commentId) {
      navigate(`/community/${notif.postId}?commentId=${notif.commentId}`);
      return;
    }

    if (notif.referenceType === 'POST' && notif.referenceId) {
      navigate(`/community/${notif.referenceId}`);
      return;
    }

    if (notif.referenceType === 'COMMENT' && notif.postId && notif.referenceId) {
      navigate(`/community/${notif.postId}?commentId=${notif.referenceId}`);
      return;
    }

    if (notif.notificationType.includes('REPORT_PROCESSED') && user?.role?.includes('ADMIN')) {
      return;
    }
  };

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return '방금 전';
    if (minutes < 60) return `${minutes}분 전`;
    if (hours < 24) return `${hours}시간 전`;
    return `${days}일 전`;
  };

  return (
    <header className="fixed top-0 left-0 right-0 h-[64px] bg-white/80 backdrop-blur-md border-b border-gray-100 z-50 flex justify-center w-full transition-all">
      <div className="w-full max-w-7xl h-full flex items-center justify-between px-6 lg:px-10">
        <div
          className="flex items-center gap-2 cursor-pointer"
          onClick={() => navigate(isAuthenticated ? '/dashboard' : '/')}
        >
          <div className="text-[24px] font-black text-primary-blue">DON'T</div>
        </div>

        {isAuthenticated && (
          <nav className="hidden md:flex ml-12 flex-1 h-full font-bold gap-1">
            {[
              { label: '홈', path: '/dashboard' },
              { label: '금융', path: '/finance' },
              { label: '소비리포트', path: '/finance/report' },
              { label: '랭킹', path: '/ranking' },
              { label: '커뮤니티', path: '/community' },
            ].map((tab, _, allTabs) => {
              const isActive =
                location.pathname.startsWith(tab.path) &&
                !allTabs.some(
                  (t) =>
                    t.path !== tab.path &&
                    t.path.startsWith(tab.path) &&
                    location.pathname.startsWith(t.path)
                );

              return (
                <div
                  key={tab.label}
                  onClick={() => navigate(tab.path)}
                  className={`flex items-center justify-center px-5 cursor-pointer text-[15px] border-b-[3px] transition-all duration-300 hover:text-primary-blue ${isActive
                      ? 'border-primary-blue text-primary-blue'
                      : 'border-transparent text-gray-500 hover:border-gray-200'
                    }`}
                >
                  {tab.label}
                </div>
              );
            })}
          </nav>
        )}

        {isAuthenticated ? (
          <div className="flex gap-5 items-center">
            {user?.role?.includes('ADMIN') && (
              <div
                className="cursor-pointer transition-all hover:scale-110 text-gray-400 hover:text-red-500"
                onClick={() => navigate('/community/admin/reports')}
                title="신고 관리 (관리자)"
              >
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  <path d="M12 8v4" />
                  <path d="M12 16h.01" />
                </svg>
              </div>
            )}

            <div className="relative" ref={dropdownRef}>
              <div
                className={`relative cursor-pointer transition-transform hover:scale-110 ${isDropdownOpen ? 'opacity-70' : ''
                  }`}
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              >
                <img src={bellIcon} alt="Notifications" className="w-5 h-5 object-contain" />
                {unreadCount > 0 && (
                  <span className="absolute -top-[2px] -right-[2px] min-w-[16px] h-[16px] bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center px-1 border-2 border-white">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
              </div>

              {isDropdownOpen && (
                <div className="absolute right-0 mt-3 w-80 bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden animate-dropdown">
                  <div className="px-4 py-3 border-b border-gray-50 flex items-center justify-between bg-gray-50/50">
                    <span className="text-[14px] font-bold text-gray-900">알림</span>
                    {unreadCount > 0 && (
                      <button
                        onClick={() => markAllAsRead()}
                        className="text-[12px] text-primary-blue font-semibold hover:underline"
                      >
                        모두 읽음
                      </button>
                    )}
                  </div>

                  <div className="max-h-96 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <div className="py-10 text-center text-gray-400 text-[13px]">
                        새로운 알림이 없습니다.
                      </div>
                    ) : (
                      notifications.map((notif) => (
                        <div
                          key={notif.notificationId}
                          className={`group px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors flex flex-col gap-0.5 border-b border-gray-50 last:border-0 relative ${!notif.isRead ? 'bg-blue-50/30' : ''
                            }`}
                          onClick={() => handleNotificationClick(notif)}
                        >
                          <div className="flex justify-between items-start gap-2 pr-5">
                            <span className="text-[13px] font-bold text-gray-900 line-clamp-1">
                              {notif.title}
                            </span>
                            <span className="text-[11px] text-gray-400 shrink-0">
                              {formatTime(notif.createdAt)}
                            </span>
                          </div>

                          <p className="text-[12px] text-gray-600 line-clamp-2 leading-relaxed pr-5">
                            {notif.body}
                          </p>

                          {!notif.isRead && (
                            <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-1"></div>
                          )}

                          <button
                            onClick={async (e) => {
                              e.stopPropagation();
                              await dismissNotification(notif.notificationId);
                            }}
                            className="absolute top-2.5 right-2 p-1 text-gray-300 hover:text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity"
                            title="알림 지우기"
                          >
                            <svg
                              className="w-3 h-3"
                              fill="none"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                              strokeWidth="3"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M6 18L18 6M6 6l12 12"
                              />
                            </svg>
                          </button>
                        </div>
                      ))
                    )}
                  </div>

                  <div
                    className="px-4 py-2.5 text-center border-t border-gray-50 bg-gray-50/30 cursor-pointer hover:bg-gray-50 transition-colors"
                    onClick={() => {
                      setIsDropdownOpen(false);
                    }}
                  >
                    <span className="text-[12px] font-bold text-gray-500">전체 보기</span>
                  </div>
                </div>
              )}
            </div>

            <div
              onClick={() => navigate('/mypage')}
              className="cursor-pointer transition-transform hover:scale-110"
              title={user?.nickname ? `${user.nickname}님의 마이페이지` : '마이페이지'}
            >
              <img src={profileIcon} alt="Profile" className="w-6 h-6 object-contain" />
            </div>

            <button
              className="px-3 py-1.5 text-[13px] font-bold text-eel border-b-2 border-eel hover:text-primary-blue hover:border-primary-blue transition-colors ml-2.5"
              onClick={onLogout}
            >
              로그아웃
            </button>
          </div>
        ) : (
          <div className="flex gap-2.5">
            <button
              className="px-4 py-2 text-[13px] font-bold text-eel border-b-2 border-eel hover:text-primary-blue hover:border-primary-blue transition-colors"
              onClick={() => navigate('/login')}
            >
              로그인
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;
