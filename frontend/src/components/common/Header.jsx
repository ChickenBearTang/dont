import React from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * 전역 상단 네비게이션바 컴포넌트
 * @param {Object} props
 * @param {Object} props.userData - 사용자 정보
 * @param {Function} props.onLogout - 로그아웃 핸들러
 * @param {boolean} props.isAuthenticated - 인증 여부
 */
const Header = ({ userData, onLogout, isAuthenticated }) => {
  const navigate = useNavigate();

  return (
    <header className="nav-bar">
      <div className="nav-content">
        <div
          style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
          onClick={() => navigate(isAuthenticated ? '/dashboard' : '/')}
        >
          <div
            className="logo-text"
            style={{ fontSize: '24px', fontWeight: '900', color: 'var(--primary-blue)' }}
          >
            DON'T
          </div>
        </div>

        {isAuthenticated && (
          <div className="nav-tabs" style={{ marginLeft: '40px', flex: 1 }}>
            {['홈', '세이브박스', '소비리포트', '랭킹', '커뮤니티'].map((tab) => (
              <div
                key={tab}
                className={`nav-tab ${tab === '홈' ? 'active' : ''}`}
                style={{ fontSize: '15px' }}
              >
                {tab}
              </div>
            ))}
          </div>
        )}

        {isAuthenticated ? (
          <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
            <div className="notification-icon">
              🔔
              <span className="notification-badge"></span>
            </div>
            <div
              className="nav-icon"
              style={{ cursor: 'pointer', fontSize: '20px' }}
              title="마이페이지"
            >
              👤
            </div>
            <button
              className="btn-outline"
              onClick={onLogout}
              style={{
                cursor: 'pointer',
                fontSize: '13px',
                padding: '6px 12px',
                borderBottomWidth: '2px',
                marginLeft: '10px',
              }}
            >
              로그아웃
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              className="btn-outline"
              style={{ padding: '8px 16px', fontSize: '13px', borderBottomWidth: '2px' }}
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
