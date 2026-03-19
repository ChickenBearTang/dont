import type { AiAnalysis } from './types';

interface Props {
  analysis: AiAnalysis | null | undefined;
  periodLabel: string;
  llmStatusLabel: string;
}

export function AiAnalysisPanel({ analysis, periodLabel, llmStatusLabel }: Props) {
  const renderList = (items: string[] | undefined, emptyText: string) => {
    if (!items || items.length === 0) {
      return <li>{emptyText}</li>;
    }
    return items.map((item, idx) => <li key={idx}>{item}</li>);
  };

  return (
    <section className="panel">
      <h2>AI 분석</h2>
      <div className="ai-status">
        분석 범위: {periodLabel} · LLM 상태: {llmStatusLabel}
      </div>
      <div className="ai-panel" style={{ marginTop: 12 }}>
        <article className="ai-card">
          <h3>소비 패턴</h3>
          <ul className="ai-list">
            {renderList(analysis?.consumption_patterns, "요약된 소비 패턴이 없습니다.")}
          </ul>
        </article>
        <article className="ai-card">
          <h3>이상 거래 설명</h3>
          <ul className="ai-list">
            {renderList(analysis?.anomaly_explanations, "설명할 이상 거래가 없습니다.")}
          </ul>
        </article>
        <article className="ai-card">
          <h3>절약 및 관리 제안</h3>
          <ul className="ai-list">
            {renderList(analysis?.actionable_solutions, "제안할 관리 팁이 없습니다.")}
          </ul>
        </article>
      </div>
    </section>
  );
}
