import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import mascot1 from '../../../assets/character/luluddun1.png';
import mascot2 from '../../../assets/character/luluddun2.png';
import mascot3 from '../../../assets/character/luluddun3.png';
import mascot4 from '../../../assets/character/luluddun4.png';
import mascot5 from '../../../assets/character/luluddun5.png';
import { Button, Card, Input } from '../../../components/common/UI';
import { Mascot, ProgressBar } from '../../../components/common/Feedback';

const Onboarding = ({ updateUser }) => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [nickname, setNickname] = useState('');
  const [isKdt, setIsKdt] = useState(null);
  const [housingExpense, setHousingExpense] = useState('');
  const [fixedExpense, setFixedExpense] = useState('');
  const [goalAmount, setGoalAmount] = useState(null);

  // UI Feedback states
  const [shake, setShake] = useState(false);
  const [error, setError] = useState(false);

  const mascots = [mascot1, mascot2, mascot3, mascot4, mascot5, mascot1];
  const mascotMessages = [
    '반가워요! 당신의 멋진 닉네임을 알려주세요! ✨',
    '현재 KDT(Korea Digital Training) 지원금을 받고 계신가요? 💸',
    '한 달 주거비(월세/이자 등)는 어느 정도인가요? 🏠',
    '교통비, 통신비 등 숨만 쉬어도 나가는 고정 지출은요? 💸',
    '마지막! 목표로 하는 월 저축액을 선택해주세요! 🎯',
    '모든 준비가 끝났어요! 당신만의 맞춤 리포트를 확인해볼까요? 🚀',
  ];

  useEffect(() => {
    const adjectives = ['똑똑한', '부지런한', '꿈꾸는', '열정적인', '계획적인'];
    const nouns = ['개미', '다람쥐', '거북이', '부엉이', '코끼리'];
    const randomNick = `${adjectives[Math.floor(Math.random() * adjectives.length)]} ${nouns[Math.floor(Math.random() * nouns.length)]}`;
    setNickname(randomNick);
  }, []);

  const triggerError = () => {
    setShake(true);
    setError(true);
    setTimeout(() => setShake(false), 400);
  };

  const isStepValid = () => {
    switch (step) {
      case 1:
        return !!nickname;
      case 2:
        return isKdt !== null;
      case 3:
        return !!housingExpense;
      case 4:
        return !!fixedExpense;
      case 5:
        return !!goalAmount;
      default:
        return true;
    }
  };

  const handleNext = () => {
    if (!isStepValid()) {
      triggerError();
      return;
    }

    setError(false);
    if (step < 6) {
      setStep(step + 1);
    } else {
      updateUser({
        nickname,
        isKdt,
        housingExpense: parseInt(housingExpense) || 0,
        monthlyFixedCost: parseInt(fixedExpense) || 0,
        goalAmount,
      });
      navigate('/signup');
    }
  };

  const getRecommendedGoal = () => {
    const totalExpense = (parseInt(housingExpense) || 0) + (parseInt(fixedExpense) || 0);
    if (isKdt) return 100;
    return totalExpense > 100 ? 100 : 200;
  };

  const recommendedGoal = getRecommendedGoal();

  return (
    <div className="container" style={{ maxWidth: '480px' }}>
      {/* Progress Header */}
      <div
        style={{ marginBottom: '15px', minHeight: '30px', display: 'flex', alignItems: 'center' }}
      >
        <ProgressBar progress={(step / 6) * 100} />
      </div>

      {/* Mascot Area */}
      <Mascot
        src={mascots[Math.min(step - 1, 5)]}
        speech={mascotMessages[step - 1]}
        className={shake ? 'shake' : ''}
      />

      {/* Content Area */}
      <div className={`${shake ? 'shake' : ''}`} style={{ marginBottom: '20px' }}>
        {step === 1 && (
          <div className={`card text-center ${error && !nickname ? 'error-border' : ''}`}>
            <h2>닉네임 설정</h2>
            <input
              type="text"
              className="mt-4"
              style={{ textAlign: 'center' }}
              value={nickname}
              onChange={(e) => {
                setNickname(e.target.value);
                if (e.target.value) setError(false);
              }}
            />
          </div>
        )}

        {step === 2 && (
          <div className={`card text-center ${error && isKdt === null ? 'error-border' : ''}`}>
            <h2>KDT 지원금 여부</h2>
            <div
              className="mt-4"
              style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}
            >
              <button
                className={isKdt === true ? 'btn-primary' : 'btn-outline'}
                onClick={() => {
                  setIsKdt(true);
                  setError(false);
                }}
                style={{ fontSize: '14px', padding: '16px 8px', textTransform: 'none' }}
              >
                네, 받고 있어요
              </button>
              <button
                className={isKdt === false ? 'btn-primary' : 'btn-outline'}
                onClick={() => {
                  setIsKdt(false);
                  setError(false);
                }}
                style={{ fontSize: '14px', padding: '16px 8px', textTransform: 'none' }}
              >
                아니요
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className={`card text-center ${error && !housingExpense ? 'error-border' : ''}`}>
            <h2>월 주거 지출비</h2>
            <div className="input-with-unit mt-4">
              <input
                type="number"
                placeholder="0"
                value={housingExpense}
                onChange={(e) => {
                  setHousingExpense(e.target.value);
                  if (e.target.value) setError(false);
                }}
              />
              <span className="input-unit-text">만원</span>
            </div>
            <button
              class="btn-outline mt-4"
              style={{ width: '100%', fontSize: '14px', background: '#f8f9fa' }}
              onClick={() => {
                setHousingExpense('0');
                setError(false);
              }}
            >
              지출 없음 (0원)
            </button>
          </div>
        )}

        {step === 4 && (
          <div className={`card text-center ${error && !fixedExpense ? 'error-border' : ''}`}>
            <h2>월 고정 지출액</h2>
            <div className="input-with-unit mt-4">
              <input
                type="number"
                placeholder="0"
                value={fixedExpense}
                onChange={(e) => {
                  setFixedExpense(e.target.value);
                  if (e.target.value) setError(false);
                }}
              />
              <span className="input-unit-text">만원</span>
            </div>
            <button
              className="btn-outline mt-4"
              style={{ width: '100%', fontSize: '14px', background: '#f8f9fa' }}
              onClick={() => {
                setFixedExpense('0');
                setError(false);
              }}
            >
              지출 없음 (0원)
            </button>
          </div>
        )}

        {step === 5 && (
          <div className={`card text-center ${error && !goalAmount ? 'error-border' : ''}`}>
            <h2>월 저축 목표 제안</h2>
            <div className="goal-grid mt-4">
              {[100, 200, 300].map((amount) => (
                <div
                  key={amount}
                  className={`goal-item ${goalAmount === amount ? 'recommended' : ''} ${amount === (goalAmount || recommendedGoal) ? 'recommended' : ''}`}
                  onClick={() => {
                    setGoalAmount(amount);
                    setError(false);
                  }}
                  style={{
                    borderColor: goalAmount === amount ? 'var(--primary-blue)' : '',
                    backgroundColor: goalAmount === amount ? '#f0faff' : '',
                  }}
                >
                  월 {amount}만원
                  {amount === recommendedGoal && !goalAmount && (
                    <span
                      style={{
                        display: 'block',
                        fontSize: '11px',
                        color: 'var(--primary-blue)',
                        marginTop: '4px',
                      }}
                    >
                      (추천)
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {step === 6 && (
          <div className="card text-center">
            <h2 style={{ color: 'var(--primary-blue)', fontSize: '28px' }}>분석 완료! ✨</h2>
            <p className="mt-4" style={{ fontWeight: '700', fontSize: '16px' }}>
              당신의 정보를 바탕으로
              <br />
              최적의 저축 플랜을 준비했어요.
            </p>
          </div>
        )}
      </div>

      <Button variant="primary" onClick={handleNext} className="w-full">
        {step === 6 ? '계정 만들러 가기' : '다음'}
      </Button>
    </div>
  );
};

export default Onboarding;
