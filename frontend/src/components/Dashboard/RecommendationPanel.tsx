import type { RecommendationPayload } from './types';

function formatCurrency(value: number) {
  return new Intl.NumberFormat("ko-KR").format(value || 0) + "원";
}

interface Props {
  data: RecommendationPayload | null;
  onOpenRanking: () => void;
}

export function RecommendationPanel({ data, onOpenRanking }: Props) {
  return (
    <section className="panel">
      <h2>💳 AI 맞춤 카드 추천</h2>
      {!data ? (
        <div className="status" style={{ marginTop: 6 }}>추천 엔진을 구동하는 중입니다...</div>
      ) : data.error || !data.user_persona ? (
        <div className="status" style={{ marginTop: 6, color: 'var(--red)' }}>
          {data.error || "추천 엔진을 사용할 수 없습니다."}
        </div>
      ) : (
        <div className="ai-panel" style={{ marginTop: 12 }}>
          <article className="ai-card" style={{ borderLeft: '4px solid var(--yellow)' }}>
            <div style={{ fontSize: 12, color: 'var(--yellow)', fontWeight: 'bold', marginBottom: 4 }}>당신의 소비 페르소나</div>
            <h3 style={{ fontSize: 18, color: '#fff', margin: '0 0 10px' }}>{data.user_persona.nickname}</h3>
            <p style={{ color: 'var(--muted)', fontSize: 13, margin: '0 0 10px', lineHeight: 1.4 }}>{data.user_persona.description}</p>
          </article>
          <article className="ai-card" style={{ borderLeft: '4px solid var(--blue)' }}>
            <div style={{ fontSize: 12, color: 'var(--blue)', fontWeight: 'bold', marginBottom: 4 }}>1위 추천 카드</div>
            {!data.best_card ? (
              <>
                <h3 style={{ fontSize: 18, color: '#fff', margin: '0 0 10px' }}>최적의 카드를 찾지 못했어요</h3>
                <p style={{ color: 'var(--muted)', fontSize: 13, margin: '0 0 10px', lineHeight: 1.4 }}>현재 소비 패턴으로 혜택을 받을 수 있는 카드가 없습니다.</p>
                <div style={{ background: 'rgba(255,255,255,0.05)', padding: 10, borderRadius: 8, marginTop: 10 }}>
                  <div style={{ fontSize: 13, color: 'var(--muted)' }}>예상 월 혜택</div>
                  <strong style={{ fontSize: 20, color: 'var(--blue)', display: 'block', marginTop: 4 }}>0원</strong>
                </div>
              </>
            ) : (
              <>
                <h3 style={{ fontSize: 18, color: '#fff', margin: '0 0 10px' }}>{data.best_card.name}</h3>
                <p style={{ color: 'var(--muted)', fontSize: 13, margin: '0 0 10px', lineHeight: 1.4 }}>{data.best_card.comment}</p>
                <div style={{ background: 'rgba(255,255,255,0.05)', padding: 10, borderRadius: 8, marginTop: 10 }}>
                  <div style={{ fontSize: 13, color: 'var(--muted)' }}>예상 월 혜택</div>
                  <strong style={{ fontSize: 20, color: 'var(--blue)', display: 'block', marginTop: 4 }}>
                    {formatCurrency(data.best_card.estimated_savings)} <span style={{fontSize: 14, fontWeight:'normal', color: 'var(--muted)'}}>(피킹률 {data.best_card.picking_rate}%)</span>
                  </strong>
                </div>
              </>
            )}
            <button 
              onClick={onOpenRanking} 
              style={{ marginTop: 12, background: 'rgba(255,255,255,0.08)', color: '#fff' }}
            >
              전체 순위 보기
            </button>
          </article>
        </div>
      )}
    </section>
  );
}
