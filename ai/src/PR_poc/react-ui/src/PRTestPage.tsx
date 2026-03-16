import React, { useState } from 'react';
import './PRTestPage.css';

// Type definitions for API response
interface Reason {
  feature: string;
  shap_value: number;
  reason_code: string;
  reason_text: string;
  source_type: string;
}

interface Counterfactual {
  type?: string;
  message?: string;
  current_balance?: number;
  emergency_fund_balance?: number;
  product_price?: number;
}

interface EngineResult {
  decision: 'HOLD' | 'REVIEW' | 'WAIT' | 'BUY_NOW';
  price_engine: {
    price_bucket: string;
    fair_price: number;
    expected_drop_prob: number;
  };
  finance_engine: {
    finance_risk_bucket: string;
    affordability_score: number;
    stress_score: number;
  };
  reasons: Reason[];
  counterfactuals: Counterfactual[];
}

export default function PRTestPage() {
  const [category, setCategory] = useState('earbuds');
  const [currentPrice, setCurrentPrice] = useState('329000');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<EngineResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    setIsLoading(true);
    setError(null);
    setResult(null);

    const priceNum = parseFloat(currentPrice);

    // AI 엔진에서 사용할 더미/디폴트 재무 데이터 구성
    const monthly_spending = 2100000;
    const current_balance = 400000;
    const emergency_fund = 500000;

    const payload = {
      price_data: {
        brand: "Apple",
        category: category,
        seller_type: "official_mall",
        option_name: "pro",
        current_price: priceNum,
        avg_price_7d: priceNum * 1.05,
        avg_price_30d: priceNum * 1.05,
        min_price_30d: priceNum * 0.8,
        max_price_30d: priceNum * 1.2,
        coupon_applied: 1,
        card_discount_applied: 0,
        shipping_fee: 2500,
        inventory_status: "low_stock",
      },
      finance_data: {
        monthly_total_spending: monthly_spending,
        monthly_fixed_spending: monthly_spending * 0.5,
        monthly_variable_spending: monthly_spending * 0.5,
        recent_30d_spending_growth_rate: 0.18,
        recent_90d_spending_trend: "increase",
        current_balance: current_balance,
        emergency_fund_balance: emergency_fund,
        debt_balance: 0,
        expected_card_payment_amount: 320000,
        days_until_card_due: 5,
        avg_monthly_income: monthly_spending * 1.3,
        product_price: priceNum,
        product_price_vs_monthly_spending: priceNum / monthly_spending,
        product_price_vs_balance: priceNum / current_balance,
        projected_balance_after_purchase: current_balance - priceNum,
        product_price_vs_emergency_fund: priceNum / emergency_fund,
        category_purchase_count_90d: 1,
        non_essential_flag: 1
      }
    };

    try {
      const res = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (!res.ok) throw new Error('API Request Failed');
      
      const data: EngineResult = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "서버 통신 중 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="header">
        <h1 className="title">AI 구매 가이드 엔진</h1>
        <p className="subtitle">상품 카테고리와 가격을 입력하면 재무/시장 데이터를 분석해 추천합니다.</p>
      </div>

      <div className="grid">
        {/* Input Panel */}
        <div className="card">
          <h2 className="cardTitle">🛍️ 상품 정보 입력</h2>
          
          <div className="inputGroup">
            <label className="label">카테고리 (Category)</label>
            <select className="select" value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="earbuds">Earbuds (이어폰)</option>
              <option value="tablet">Tablet (태블릿)</option>
              <option value="watch">Watch (워치)</option>
              <option value="laptop">Laptop (노트북)</option>
            </select>
          </div>

          <div className="inputGroup">
            <label className="label">현재 가격 (KRW)</label>
            <input 
              type="number" 
              className="input" 
              value={currentPrice} 
              onChange={(e) => setCurrentPrice(e.target.value)} 
              placeholder="예: 329000"
            />
          </div>

          <button className="button" onClick={handleAnalyze} disabled={isLoading}>
            {isLoading ? 'AI가 고민 중입니다...' : '구매 타당성 분석하기'}
          </button>
        </div>

        {/* Result Panel */}
        <div className="card">
          <h2 className="cardTitle">🤖 AI 분석 결과</h2>
          
          {isLoading && (
            <div className="loading">
              SHAP 및 반사실적(DiCE) 시나리오 탐색 중...
            </div>
          )}

          {error && <div style={{color: 'red'}}>{error}</div>}

          {!isLoading && !result && !error && (
            <div style={{color: '#9ca3af', textAlign: 'center', marginTop: '2rem'}}>
              왼쪽에서 정보를 입력하고 분석 버튼을 눌러주세요.
            </div>
          )}

          {result && (
            <div className="resultBox">
              <div className={`decisionBadge decision-${result.decision}`}>
                {result.decision}
              </div>

              <div className="scoreGrid">
                <div className="scoreItem">
                  <div className="scoreValue">{result.finance_engine.finance_risk_bucket.toUpperCase()}</div>
                  <div className="scoreLabel">내 재무 위험도</div>
                </div>
                <div className="scoreItem">
                  <div className="scoreValue">{result.price_engine.price_bucket.toUpperCase()}</div>
                  <div className="scoreLabel">현재 가격 매력도</div>
                </div>
              </div>

              <h3 className="sectionTitle">🔍 AI 결정 주요 사유 (SHAP)</h3>
              <ul className="reasonList">
                {result.reasons.map((r, i) => (
                  <li key={i} className={`reasonItem ${r.source_type}`}>
                    {r.reason_text}
                  </li>
                ))}
              </ul>

              <h3 className="sectionTitle">💡 AI의 재무 방어 제안 (DiCE)</h3>
              <div className="counterfactualList">
                {result.counterfactuals.slice(0, 3).map((cf, i) => {
                  if (cf.message) {
                    return <div key={i} className="counterfactualItem">{cf.message}</div>;
                  }
                  
                  // 디테일한 DiCE 스펙 노출
                  return (
                    <div key={i} className="counterfactualItem">
                      현재 재무 상태에서 
                      <span className="highlight"> 비상자금 {Math.round(cf.emergency_fund_balance || 0).toLocaleString()}원 확보 </span> 
                      또는 
                      <span className="highlight"> 잔고 {Math.round(cf.current_balance || 0).toLocaleString()}원 </span>
                      수준일 때 구매 결정이 '안전'으로 전환될 수 있습니다.
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
