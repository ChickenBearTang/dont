import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import mascot4 from '../../../assets/character/luluddun4.png';
import { Button, Modal } from '../../../components/common/UI';
import { Mascot } from '../../../components/common/Feedback';

const FinanceConnect = ({ updateUser }) => {
  const navigate = useNavigate();
  const [agreed, setAgreed] = useState(false);
  const [showModal, setShowModal] = useState(false);

  const handleConnect = () => {
    updateUser({ connected: true });
    navigate('/loading');
  };

  return (
    <div className="container" style={{ padding: '20px', maxWidth: '480px' }}>
      {/* Mascot Area */}
      <Mascot
        src={mascot4}
        speech={
          <>
            마지막 단계예요!
            <br />
            안전한 자산 관리를 위해 계좌를 연결할까요? 🐷
          </>
        }
        style={{ width: '180px' }}
      />

      <div className="card">
        <h2 className="text-center" style={{ fontSize: '24px', marginBottom: '8px' }}>
          금융 권한 동의
        </h2>
        <p
          className="text-center"
          style={{ color: 'var(--gray)', fontSize: '15px', marginBottom: '24px' }}
        >
          안전한 저축 관리를 위해
          <br />
          오픈뱅킹 연동이 필요합니다.
        </p>

        <div
          style={{
            backgroundColor: 'var(--snow)',
            padding: '20px',
            borderRadius: '18px',
            fontSize: '14px',
            border: '2px solid var(--gray-light)',
            marginBottom: '24px',
          }}
        >
          <p style={{ fontWeight: '800', marginBottom: '8px', color: 'var(--eel)' }}>
            서비스 이용 약관 요약
          </p>
          <p style={{ color: '#666', marginBottom: '12px', lineHeight: '1.5' }}>
            계좌 잔액 및 거래 내역을 오직 저축 목표 달성 확인 용도로만 사용하며, 최고 수준의
            보안으로 보호됩니다.
          </p>
          <Button
            variant="outline"
            onClick={() => setShowModal(true)}
            style={{
              border: 'none',
              background: 'none',
              color: 'var(--primary-blue)',
              fontWeight: '800',
              padding: 0,
              fontSize: '13px',
              boxShadow: 'none',
            }}
          >
            전체 약관 보기 &gt;
          </Button>
        </div>

        <div className="custom-checkbox-container" onClick={() => setAgreed(!agreed)}>
          <input type="checkbox" className="custom-checkbox" checked={agreed} readOnly />
          <span style={{ fontSize: '15px', fontWeight: '700', color: 'var(--eel)' }}>
            모든 약관에 동의합니다.
          </span>
        </div>

        <div style={{ marginTop: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <Button variant="primary" disabled={!agreed} onClick={handleConnect}>
            계좌 연동 시작하기
          </Button>

          <Button
            variant="outline"
            style={{ border: 'none', background: 'none' }}
            onClick={() => navigate('/loading')}
          >
            나중에 하기
          </Button>
        </div>
      </div>

      {/* Terms Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="서비스 이용 약관"
        footer={
          <Button variant="primary" className="w-full" onClick={() => setShowModal(false)}>
            확인했습니다
          </Button>
        }
      >
        <p style={{ fontWeight: '700', color: 'var(--eel)' }}>
          본 약관은 DON'T 서비스의 금융 기능 이용을 위한 약관입니다.
        </p>

        <h3>제1조 (목적)</h3>
        <p>
          이 약관은 DON'T가 제공하는 금융 연동 서비스의 이용 조건 및 절차에 관한 사항을 규정함을
          목적으로 합니다.
        </p>

        <h3>제2조 (개인정보 활용)</h3>
        <p>1. 사용자의 계좌 잔액 및 거래 내역을 저축 목표 달성 확인 용도로만 활용합니다.</p>
        <p>2. 수집된 정보는 암호화되어 관리되며 제3자에게 제공되지 않습니다.</p>

        <h3>제3조 (오픈뱅킹 연동)</h3>
        <p>
          사용자는 금융결제원의 오픈뱅킹 이용약관에 동의함으로써 서비스를 정상적으로 이용할 수
          있습니다.
        </p>

        <h3>제4조 (책임)</h3>
        <p>
          본 서비스는 사용자의 금융 데이터를 보호하기 위해 최선을 다하며, 보안 사고 발생 시 관련
          법규에 따라 책임을 집니다.
        </p>
      </Modal>
    </div>
  );
};

export default FinanceConnect;
