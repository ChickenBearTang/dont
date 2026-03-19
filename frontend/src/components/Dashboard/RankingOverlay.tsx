import type { RecommendationPayload } from './types';

function formatCurrency(value: number) {
  return new Intl.NumberFormat("ko-KR").format(value || 0) + "원";
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  allCards: RecommendationPayload['all_cards'];
}

export function RankingOverlay({ isOpen, onClose, allCards }: Props) {
  if (!isOpen) return null;

  return (
    <div className="ranking-overlay" style={{ display: 'block' }}>
      <div className="ranking-header">
        <button className="ranking-back" onClick={onClose}>←</button>
        <h2>카드 혜택 랭킹 전체보기</h2>
      </div>
      <div className="ranking-list">
        {(allCards || []).map((card, idx) => {
          const rank = idx + 1;
          const topClass = rank <= 3 ? "top3" : "";
          
          return (
            <div className={`ranking-item ${topClass}`} key={card.card_id}>
              <div className="ranking-rank" style={{ alignSelf: 'flex-start', paddingTop: 4 }}>{rank}</div>
              <div className="ranking-details">
                <div className="ranking-name">{card.name}</div>
                <div style={{ fontSize: 14, marginBottom: 6, color: '#fff', lineHeight: 1.4 }}>{card.main_text || ''}</div>
                
                {card.sub_text && card.sub_text.length > 0 && (
                  <ul style={{ margin: '4px 0 0', paddingLeft: 18, color: 'var(--muted)', fontSize: 13, lineHeight: 1.5 }}>
                    {card.sub_text.map((t, i) => <li key={i}>{t}</li>)}
                  </ul>
                )}
                
                <div style={{ marginTop: 12, padding: 12, background: 'rgba(255,255,255,0.05)', borderRadius: 8 }}>
                  <span className="ranking-savings" style={{ display: 'block', marginBottom: 6 }}>
                    예상 할인액: {formatCurrency(card.estimated_savings)}
                    <span style={{ fontWeight: 'normal', fontSize: 13, color: 'var(--muted)', marginLeft: 4 }}>
                      (피킹률 {card.picking_rate}%)
                    </span>
                  </span>
                  <span style={{ fontSize: 13, color: 'var(--yellow)', lineHeight: 1.4, display: 'block' }}>💡 {card.comment}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
