import React, { useState, useEffect } from 'react';
import mascot3 from '../../../assets/character/luluddun3.png';
import { Card, Button } from '../../../components/common/UI';
import { Mascot, CircularProgress } from '../../../components/common/Feedback';

const Dashboard = ({ userData, onLogout }) => {
  const [activeTab, setActiveTab] = useState('홈');
  const [showFact, setShowFact] = useState(false);
  const [currentFact, setCurrentFact] = useState('');

  const factBombs = [
    '오늘 평소보다 15,000원 더 쓰셨네요? 혹시 배달 시키셨나요? 🍕',
    '이번 주 주거비 지출이 10% 감소할 예정이에요! 대단한데요? 🏠',
    '닉네임님, 저축 목표까지 35% 남았습니다. 조금만 더 힘내요! 💪',
    '현재 랭킹 5위! 3위까지 12만원 정도 남았어요! 🏆',
  ];

  const handleFactClick = () => {
    const randomFact = factBombs[Math.floor(Math.random() * factBombs.length)];
    setCurrentFact(randomFact.replace('닉네임', userData.nickname || '귀하'));
    setShowFact(true);
    setTimeout(() => setShowFact(false), 4000);
  };

  return (
    <div className="dashboard">
      <div className="dashboard-container">
        {/* Greeting Section */}
        <div className="greeting-section">
          <h1 className="greeting-text">
            안녕하세요,{' '}
            <span style={{ color: 'var(--primary-blue)' }}>{userData.nickname || '싸피인'}</span>님!
            <br />
            오늘도 똑똑한 저축 습관을 이어가볼까요?
          </h1>
        </div>

        <div className="dashboard-grid">
          {/* Savebox Status */}
          <Card style={{ gridColumn: 'span 2' }}>
            <div className="card-header">
              <h3 className="card-title">현금 세이프박스 현황</h3>
              <span className="card-action">상세보기 +</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '40px', padding: '10px 0' }}>
              <CircularProgress progress={65} size={150} />
              <div style={{ flex: 1 }}>
                <div
                  style={{
                    fontSize: '16px',
                    color: 'var(--gray)',
                    fontWeight: '700',
                    marginBottom: '8px',
                  }}
                >
                  현재 모인 금액
                </div>
                <div style={{ fontSize: '36px', fontWeight: '900', color: 'var(--eel)' }}>
                  {(userData.goalAmount * 0.65).toLocaleString()}만원{' '}
                  <span style={{ fontSize: '18px', color: 'var(--gray)' }}>
                    / {userData.goalAmount.toLocaleString()}만원
                  </span>
                </div>
                <div style={{ marginTop: '20px' }}>
                  <div className="progress-bar-container" style={{ height: '10px' }}>
                    <div className="progress-bar-fill" style={{ width: '65%' }}></div>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Community Preview */}
          <Card>
            <div className="card-header">
              <h3 className="card-title">실시간 커뮤니티</h3>
              <span className="card-action">상세보기 +</span>
            </div>
            <div className="ranking-list">
              {[
                { user: '절약왕 개미', text: '오늘 점심은 삼각김밥으로 해결! 🍙', likes: 12 },
                { user: '계획적인 다람쥐', text: '고정지출 드디어 줄였어요!! 🔥', likes: 8 },
                { user: '부엉부엉', text: '충동구매 참기 1일차... 꾹 참습니다.', likes: 15 },
              ].map((item, i) => (
                <div key={i} className="ranking-item">
                  <div style={{ fontWeight: '800', fontSize: '14px', width: '30px' }}>👤</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: '900', fontSize: '13px' }}>{item.user}</div>
                    <div style={{ fontSize: '13px', color: '#666' }}>{item.text}</div>
                  </div>
                  <div
                    style={{ fontSize: '12px', color: 'var(--primary-blue)', fontWeight: '800' }}
                  >
                    ❤️ {item.likes}
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Ranking Preview */}
          <Card>
            <div className="card-header">
              <h3 className="card-title">저축왕 랭킹 🏆</h3>
              <span className="card-action">상세보기 +</span>
            </div>
            <div className="ranking-list">
              {[
                { name: '알뜰가성비', amount: '2,450,000' },
                { name: '싸피12기', amount: '2,200,000' },
                { name: '목돈마련중', amount: '1,980,000' },
              ].map((item, i) => (
                <div key={i} className="ranking-item">
                  <div className="rank-num">{i + 1}</div>
                  <div style={{ flex: 1, fontWeight: '800', fontSize: '14px' }}>{item.name}</div>
                  <div
                    style={{ fontWeight: '900', color: 'var(--primary-blue)', fontSize: '14px' }}
                  >
                    {item.amount}원
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* AI Fact-Bombing Floating Button */}
      <div className="ai-floating-btn" onClick={handleFactClick}>
        <Mascot src={mascot3} />
      </div>
      {showFact && <div className="ai-fact-bubble">{currentFact}</div>}
    </div>
  );
};

export default Dashboard;
