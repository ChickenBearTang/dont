import type { CategoryData } from './types';

function formatCurrency(value: number) {
  return new Intl.NumberFormat("ko-KR").format(value || 0) + "원";
}

const palette = ["#7187ff", "#ffd400", "#ffab19", "#c6df4d", "#34d7cf", "#d0d4dd", "#9ea6b7", "#7c8799", "#5f697a", "#474f5f"];

interface Props {
  categories: CategoryData[];
}

export function CategoryPanel({ categories }: Props) {
  return (
    <section className="panel">
      <h2>카테고리별 소비</h2>
      
      <div className="category-bar">
        {categories.map((row, index) => row.amount > 0 ? (
          <div 
            key={row.category_display}
            style={{ width: `${row.share_percent}%`, background: palette[index % palette.length] }} 
          />
        ) : null)}
      </div>
      
      <div className="category-list">
        {categories.map((row, index) => {
          const deltaClass = row.delta_amount > 0 ? "increase" : row.delta_amount < 0 ? "decrease" : "flat";
          const deltaText = row.delta_amount > 0 ? `지난달보다 +${formatCurrency(row.delta_amount)}` :
            row.delta_amount < 0 ? `지난달보다 -${formatCurrency(Math.abs(row.delta_amount))}` : "지난달과 동일";

          return (
            <div className="category-item" key={row.category_display}>
              <div>
                <div className="category-name">
                  <span className="dot" style={{ background: palette[index % palette.length] }}></span>
                  <span>{row.category_display}</span>
                  <span className="muted">{row.share_percent}%</span>
                </div>
              </div>
              <div className="category-amount">
                <strong>{formatCurrency(row.amount)}</strong>
                <div className={`delta ${deltaClass}`}>{deltaText}</div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
