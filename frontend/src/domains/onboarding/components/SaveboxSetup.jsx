import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import mascot5 from '../../../assets/character/luluddun5.png';
import { Button, Card, Input, Modal } from '../../../components/common/UI';
import { Mascot } from '../../../components/common/Feedback';

const SaveboxSetup = ({ userData, onComplete }) => {
  const navigate = useNavigate();
  const [goalAmount, setGoalAmount] = useState(userData.goalAmount || 0);
  const [agreed, setAgreed] = useState(false);
  const [showModal, setShowModal] = useState(false);

  const handleConfirm = () => {
    if (!agreed) return;
    onComplete({ goalAmount: Number(goalAmount) });
    navigate('/success');
  };

  return (
    <div className="container" style={{ padding: '20px', maxWidth: '480px' }}>
      <Mascot
        src={mascot5}
        speech={
          <>
            연동 완료! 이제 목돈을 모아볼까요?
            <br />
            <strong>'세이프박스'</strong>에 가입해 드릴게요! 🏦
          </>
        }
        style={{ width: '180px' }}
      />

      <Card>
        <h2
          className="text-center"
          style={{ fontSize: '24px', color: 'var(--primary-blue)', marginBottom: '8px' }}
        >
          세이프박스 개설
        </h2>
        <p
          className="text-center"
          style={{ color: 'var(--gray)', fontSize: '15px', marginBottom: '24px' }}
        >
          가입 즉시 연 1.6% 이자 혜택!
          <br />
          목표 금액을 최종 확인해 주세요.
        </p>

        <div
          style={{
            backgroundColor: '#f0faff',
            padding: '20px',
            borderRadius: '18px',
            marginBottom: '24px',
          }}
        >
          <Input
            label="최종 목표 금액"
            unit="만원"
            type="number"
            value={goalAmount}
            onChange={(e) => setGoalAmount(e.target.value)}
            style={{ backgroundColor: 'white' }}
            className="mt-0"
          />
        </div>

        <div
          className="info-box"
          style={{
            border: '2px solid var(--gray-light)',
            borderRadius: '16px',
            padding: '16px',
            marginBottom: '12px',
            fontSize: '14px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ color: 'var(--gray)', fontWeight: '700' }}>적용 금리</span>
            <span style={{ color: 'var(--eel)', fontWeight: '800' }}>연 1.6%</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ color: 'var(--gray)', fontWeight: '700' }}>이자 지급</span>
            <span style={{ color: 'var(--eel)', fontWeight: '800' }}>매월 세 번째 일요일</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--gray)', fontWeight: '700' }}>중도 해지</span>
            <span style={{ color: 'var(--green)', fontWeight: '800' }}>언제든 가능!</span>
          </div>
        </div>

        <div style={{ marginBottom: '24px', textAlign: 'right' }}>
          <Button
            variant="outline"
            onClick={() => setShowModal(true)}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--primary-blue)',
              fontWeight: '800',
              padding: 0,
              fontSize: '13px',
              boxShadow: 'none',
            }}
          >
            세이프박스 이용 약관 보기 &gt;
          </Button>
        </div>

        <div className="custom-checkbox-container" onClick={() => setAgreed(!agreed)}>
          <input type="checkbox" className="custom-checkbox" checked={agreed} readOnly />
          <span style={{ fontSize: '15px', fontWeight: '700', color: 'var(--eel)' }}>
            상품 설명서를 확인하고 동의합니다.
          </span>
        </div>

        <Button
          variant="primary"
          className="mt-4 w-full"
          onClick={handleConfirm}
          disabled={!agreed}
        >
          세이프박스 가입 완료하기
        </Button>
      </Card>

      {/* Terms Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="세이프박스 이용 약관"
        footer={
          <Button variant="primary" className="w-full" onClick={() => setShowModal(false)}>
            확인했습니다
          </Button>
        }
      >
        <p style={{ fontWeight: '700', color: 'var(--eel)' }}>
          본 약관은 DON'T 세이프박스 예금 상품 서비스 이용을 위한 약관입니다.
        </p>

        <h3>제1조 (상품 개요)</h3>
        <p>
          세이프박스는 사용자의 여유 자금을 안전하게 보관하고, 연 1.6%의 이자를 제공하는
          수시입출금식 예금 서비스입니다.
        </p>

        <h3>제2조 (이자 지급)</h3>
        <p>1. 금리는 연 1.6%(세전)이며, 시장 상황에 따라 변동될 수 있습니다.</p>
        <p>2. 이자는 매월 세 번째 일요일에 사용자의 연동 계좌로 자동 지급됩니다.</p>

        <h3>제3조 (예금자 보호)</h3>
        <p>
          본 금융상품은 예금자보호법에 따라 예금보험공사가 보호하되, 보호 한도는 본 은행에 있는
          귀하의 모든 보호 대상 금융상품의 원금과 소정의 이자를 합하여 1인당 "최고 5천만원"이며,
          5천만원을 초과하는 나머지 금액은 보호하지 않습니다.
        </p>

        <h3>제4조 (계약 해지)</h3>
        <p>
          사용자는 언제든지 본 서비스를 해지할 수 있으며, 해지 시점까지 적립된 이자는 다음 이자
          지급일에 정산됩니다.
        </p>
      </Modal>
    </div>
  );
};

export default SaveboxSetup;
