import './StrictSecretaryResult.css';

export interface AIResultData {
  is_approved: boolean;
  fact_violence_comment: string;
  reasoning: string[];
}

interface StrictSecretaryResultProps {
  status: 'RESULT' | 'RETRY';
  data?: AIResultData;
  onRetry: () => void;
  onReset: () => void;
}

export default function StrictSecretaryResult({ status, data, onRetry, onReset }: StrictSecretaryResultProps) {
  if (status === 'RETRY' || !data) {
    return (
      <div className="ss-result-container retry">
        <h2>AI 응답 지연</h2>
        <p>엄격한 비서가 아직 답변을 준비하지 못했어요.</p>
        <div className="ss-result-actions">
          <button className="ss-retry-btn" onClick={onRetry}>다시 확인하기</button>
          <button className="ss-reset-btn" onClick={onReset}>처음으로</button>
        </div>
      </div>
    );
  }

  const { is_approved, fact_violence_comment, reasoning } = data;

  return (
    <div className={`ss-result-container ${is_approved ? 'approved' : 'rejected'}`}>
      <div className="ss-result-status">
        {is_approved ? '✅ 구매 승인' : '❌ 구매 기각'}
      </div>
      
      <div className="ss-fact-violence">
        <h3>비서의 팩트 폭력</h3>
        <p>"{fact_violence_comment}"</p>
      </div>

      <div className="ss-reasoning">
        <h3>판단 이유</h3>
        <ul className="ss-reasoning-list">
          {reasoning.map((reason, index) => (
            <li key={index}>{reason}</li>
          ))}
        </ul>
      </div>

      <button className="ss-reset-btn" onClick={onReset}>다른 물건 물어보기</button>
    </div>
  );
}
