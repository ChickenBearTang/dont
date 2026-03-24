import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useLocation, useNavigate } from 'react-router-dom';
import type { UserProfile } from '@/features/auth/types';
import { useNotificationStore } from '@/features/community/store/useNotificationStore';
import { fetchMyPage } from '@/features/user/api/userApi';
import bellIcon from '@/assets/logo/bell-icon.png';

interface HeaderProps {
  user: UserProfile | null;
  onLogout: () => void;
  isAuthenticated: boolean;
}

const NAV_TABS = [
  { label: '대시보드', path: '/dashboard' },
  { label: '금융', path: '/finance' },
  { label: '소비리포트', path: '/finance/report' },
  { label: '랭킹', path: '/ranking' },
  { label: '커뮤니티', path: '/community' },
];

const Header = ({ user, onLogout, isAuthenticated }: HeaderProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const { data: myPageData } = useQuery({
    queryKey: ['myPage'],
    queryFn: fetchMyPage,
    enabled: isAuthenticated,
    staleTime: 60 * 1000,
    select: (response) => response.data,
  });

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

  const displayEmail = myPageData?.email ?? user?.email ?? '';
  const displayNickname = myPageData?.nickname ?? user?.nickname ?? '사용자';
  const displayProfileImageUrl = myPageData?.profileImageUrl ?? user?.profileImageUrl ?? null;
  const profileInitial = (displayNickname.trim()[0] ?? displayEmail.trim()[0] ?? 'U').toUpperCase();

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
    <header className="fixed top-0 left-0 right-0 z-50 flex h-[64px] w-full justify-center border-b border-gray-100 bg-white/80 backdrop-blur-md transition-all">
      <div className="flex h-full w-full max-w-7xl items-center justify-between px-6 lg:px-10">
        <div
          className="flex cursor-pointer items-center gap-2"
          onClick={() => navigate(isAuthenticated ? '/dashboard' : '/')}
        >
          <div className="text-[24px] font-black text-primary-blue">DON&apos;T</div>
        </div>

        {isAuthenticated && (
          <nav className="ml-12 hidden h-full flex-1 gap-1 font-bold md:flex">
            {NAV_TABS.map((tab, _, allTabs) => {
              const isActive =
                location.pathname.startsWith(tab.path) &&
                !allTabs.some(
                  (candidate) =>
                    candidate.path !== tab.path &&
                    candidate.path.startsWith(tab.path) &&
                    location.pathname.startsWith(candidate.path)
                );

              return (
                <div
                  key={tab.label}
                  onClick={() => navigate(tab.path)}
                  className={`flex cursor-pointer items-center justify-center border-b-[3px] px-5 text-[15px] transition-all duration-300 hover:text-primary-blue ${
                    isActive
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
          <div className="flex items-center gap-4">
            {user?.role === 'ADMIN' && (
              <button
                type="button"
                className="cursor-pointer text-gray-400 transition-all hover:scale-110 hover:text-red-500"
                onClick={() => navigate('/community/admin/reports')}
                title="신고 관리"
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
              </button>
            )}

            <div className="relative" ref={dropdownRef}>
              <button
                type="button"
                className={`relative cursor-pointer transition-transform hover:scale-110 ${
                  isDropdownOpen ? 'opacity-70' : ''
                }`}
                onClick={() => setIsDropdownOpen((prev) => !prev)}
              >
                <img src={bellIcon} alt="Notifications" className="h-5 w-5 object-contain" />
                {unreadCount > 0 && (
                  <span className="absolute -top-[2px] -right-[2px] flex h-[16px] min-w-[16px] items-center justify-center rounded-full border-2 border-white bg-red-500 px-1 text-[10px] font-bold text-white">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
              </button>

              {isDropdownOpen && (
                <div className="animate-dropdown absolute right-0 mt-3 w-80 overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-xl">
                  <div className="flex items-center justify-between border-b border-gray-50 bg-gray-50/50 px-4 py-3">
                    <span className="text-[14px] font-bold text-gray-900">알림</span>
                    {unreadCount > 0 && (
                      <button
                        type="button"
                        onClick={() => markAllAsRead()}
                        className="text-[12px] font-semibold text-primary-blue hover:underline"
                      >
                        모두 읽음
                      </button>
                    )}
                  </div>

                  <div className="max-h-96 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <div className="py-10 text-center text-[13px] text-gray-400">
                        새로운 알림이 없습니다.
                      </div>
                    ) : (
                      notifications.map((notif) => (
                        <div
                          key={notif.notificationId}
                          className={`group relative flex cursor-pointer flex-col gap-0.5 border-b border-gray-50 px-4 py-3 transition-colors last:border-0 hover:bg-gray-50 ${
                            !notif.isRead ? 'bg-blue-50/30' : ''
                          }`}
                          onClick={() => void handleNotificationClick(notif)}
                        >
                          <div className="flex items-start justify-between gap-2 pr-5">
                            <span className="line-clamp-1 text-[13px] font-bold text-gray-900">
                              {notif.title}
                            </span>
                            <span className="shrink-0 text-[11px] text-gray-400">
                              {formatTime(notif.createdAt)}
                            </span>
                          </div>

                          <p className="line-clamp-2 pr-5 text-[12px] leading-relaxed text-gray-600">
                            {notif.body}
                          </p>

                          {!notif.isRead && <div className="mt-1 h-1.5 w-1.5 rounded-full bg-blue-500" />}

                          <button
                            type="button"
                            onClick={async (event) => {
                              event.stopPropagation();
                              await dismissNotification(notif.notificationId);
                            }}
                            className="absolute top-2.5 right-2 p-1 text-gray-300 opacity-0 transition-opacity group-hover:opacity-100 hover:text-gray-600"
                            title="알림 지우기"
                          >
                            <svg
                              className="h-3 w-3"
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
                    className="cursor-pointer border-t border-gray-50 bg-gray-50/30 px-4 py-2.5 text-center transition-colors hover:bg-gray-50"
                    onClick={() => setIsDropdownOpen(false)}
                  >
                    <span className="text-[12px] font-bold text-gray-500">닫기</span>
                  </div>
                </div>
              )}
            </div>

            <button
              type="button"
              onClick={() => navigate('/mypage')}
              className="flex items-center gap-3 rounded-2xl border border-gray-200 bg-white px-3 py-2 text-left shadow-sm transition-all hover:-translate-y-0.5 hover:border-primary-blue hover:shadow-md"
              title={`${displayNickname}의 마이페이지`}
            >
              {displayProfileImageUrl ? (
                <img
                  src={displayProfileImageUrl}
                  alt={`${displayNickname} 프로필 이미지`}
                  className="h-10 w-10 rounded-xl border border-gray-100 object-cover"
                />
              ) : (
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-sm font-black text-primary-blue">
                  {profileInitial}
                </div>
              )}

              <div className="min-w-0">
                <p className="max-w-[180px] truncate text-[11px] font-semibold text-gray-400">
                  {displayEmail}
                </p>
                <p className="max-w-[180px] truncate text-[14px] font-bold text-eel">
                  {displayNickname}
                </p>
              </div>
            </button>

            <button
              type="button"
              className="ml-1 px-3 py-1.5 text-[13px] font-bold text-eel transition-colors hover:border-primary-blue hover:text-primary-blue"
              onClick={onLogout}
            >
              로그아웃
            </button>
          </div>
        ) : (
          <div className="flex gap-2.5">
            <button
              type="button"
              className="px-4 py-2 text-[13px] font-bold text-eel transition-colors hover:text-primary-blue"
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
