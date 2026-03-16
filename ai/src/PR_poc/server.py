import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import pandas as pd
from initial import (
    make_price_data,
    make_finance_data,
    train_price_model,
    train_finance_model,
    train_finance_model_for_dice,
    apply_decision_rule,
    extract_top_reasons_from_shap,
    build_dice_from_finance_training,
    get_desired_finance_class,
    generate_counterfactuals
)
from functools import lru_cache
import shap

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === 1. Server initialization: Data logic + Model training ===
print("Generating Mock Data and Training Models...")
price_df = make_price_data()
finance_df = make_finance_data()

price_model, price_features, _ = train_price_model(price_df)
finance_model, finance_features, _ = train_finance_model(finance_df)
finance_model_for_dice, finance_dice_features = train_finance_model_for_dice(finance_df)

# Initialize and cache Explainers globally here
price_explainer = shap.TreeExplainer(price_model)
finance_explainer = shap.TreeExplainer(finance_model)

dice_exp = build_dice_from_finance_training(
    finance_df,
    finance_model_for_dice,
    finance_dice_features,
)
print("Models are ready!")


@app.post("/analyze")
async def analyze_purchase(request: Request):
    data = await request.json()
    
    price_data = data.get("price_data", {})
    finance_data = data.get("finance_data", {})
    
    # Construct dataframes based on logic
    price_row = pd.DataFrame([price_data])
    finance_row = pd.DataFrame([finance_data])
    
    finance_row_for_model = finance_row.copy()
    finance_row_for_model["recent_90d_spending_trend"] = pd.Categorical(
        finance_row_for_model["recent_90d_spending_trend"],
        categories=["increase", "stable", "decrease"],
    )

    # ------------------------------------------------------------
    # predictions
    # ------------------------------------------------------------
    price_bucket = str(price_model.predict(price_row).flatten()[0])
    price_proba = price_model.predict_proba(price_row)[0]
    cheap_idx = list(price_model.classes_).index("cheap")
    expected_drop_prob = max(0.0, 1.0 - float(price_proba[cheap_idx])) * 0.5
    fair_price = float(price_row["avg_price_30d"].iloc[0] * 0.96)

    finance_bucket = str(finance_model.predict(finance_row_for_model)[0])
    finance_proba = finance_model.predict_proba(finance_row_for_model)[0]
    low_idx = list(finance_model.classes_).index("low")
    affordability_score = float(finance_proba[low_idx])
    stress_score = float(1 - affordability_score)

    # ------------------------------------------------------------
    # decision
    # ------------------------------------------------------------
    decision_code = apply_decision_rule(
        price_bucket=price_bucket,
        expected_drop_prob=float(expected_drop_prob),
        finance_risk_bucket=finance_bucket,
        affordability_score=float(affordability_score),
    )

    # ------------------------------------------------------------
    # SHAP - price
    # ------------------------------------------------------------
    price_shap_values = price_explainer.shap_values(price_row)

    if isinstance(price_shap_values, list):
        price_class_idx = list(price_model.classes_).index("cheap")
        price_shap_1d = price_shap_values[price_class_idx][0]
    else:
        price_class_idx = list(price_model.classes_).index("cheap")
        price_shap_1d = price_shap_values[0, :, price_class_idx]

    price_reasons = extract_top_reasons_from_shap(
        price_shap_1d,
        price_features,
        top_k=3,
    )

    # ------------------------------------------------------------
    # SHAP - finance
    # ------------------------------------------------------------
    finance_shap_values = finance_explainer.shap_values(finance_row_for_model)

    finance_classes = list(finance_model.classes_)
    target_class = "high" if decision_code == "HOLD" and "high" in finance_classes else finance_bucket
    target_idx = finance_classes.index(target_class)

    if isinstance(finance_shap_values, list):
        finance_shap_1d = finance_shap_values[target_idx][0]
    else:
        finance_shap_1d = finance_shap_values[0, :, target_idx]

    finance_reasons = extract_top_reasons_from_shap(
        finance_shap_1d,
        finance_features,
        top_k=3,
    )

    # ------------------------------------------------------------
    # DiCE
    # ------------------------------------------------------------
    finance_row_for_dice = finance_row[finance_dice_features].copy()
    desired_class = get_desired_finance_class(finance_bucket)
    counterfactuals = generate_counterfactuals(
        dice_exp,
        finance_row_for_dice,
        desired_class=desired_class,
        finance_row_original=finance_row,
    )

    # ------------------------------------------------------------
    # final payload
    # ------------------------------------------------------------
    payload = {
        "decision": decision_code,
        "price_engine": {
            "price_bucket": price_bucket,
            "fair_price": round(fair_price, 2),
            "expected_drop_prob": round(expected_drop_prob, 4),
        },
        "finance_engine": {
            "finance_risk_bucket": finance_bucket,
            "affordability_score": round(affordability_score, 4),
            "stress_score": round(stress_score, 4),
        },
        "reasons": price_reasons + finance_reasons,
        "counterfactuals": counterfactuals,
    }
    
    return payload


@app.get("/")
def get_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>XAI Engine Test Dashboard</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #fdfdfd; margin: 0; padding: 20px; display: flex; gap: 20px; }
            h1 { color: #333; }
            .panel { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); flex: 1; }
            .form-group { margin-bottom: 12px; }
            label { display: block; font-weight: 600; font-size: 13px; color: #555; margin-bottom: 4px; }
            input, select { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
            button { background: #007bff; color: white; padding: 12px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; font-weight: bold; width: 100%; margin-top: 20px; }
            button:hover { background: #0056b3; }
            pre { background: #282c34; color: #abb2bf; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 14px; min-height: 400px; white-space: pre-wrap; }
            .header-bar { background: #eee; padding: 10px; border-radius: 4px; margin-bottom: 20px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="panel" style="max-width: 400px;">
            <h2>Input Parameters</h2>
            
            <div class="header-bar">🛒 Price Engine Inputs</div>
            <div class="form-group"><label>Current Price</label><input type="number" id="current_price" value="329000"></div>
            <div class="form-group"><label>Avg Price 30D</label><input type="number" id="avg_price_30d" value="349000"></div>
            <div class="form-group"><label>Coupon Applied (0/1)</label><input type="number" id="coupon_applied" value="1"></div>
            <div class="form-group"><label>Shipping Fee</label><input type="number" id="shipping_fee" value="2500"></div>
            
            <br>
            <div class="header-bar">💳 Finance Engine Inputs</div>
            <div class="form-group"><label>Current Balance</label><input type="number" id="current_balance" value="400000"></div>
            <div class="form-group"><label>Emergency Fund</label><input type="number" id="emergency_fund" value="500000"></div>
            <div class="form-group"><label>Monthly Total Spending</label><input type="number" id="monthly_spending" value="2100000"></div>
            <div class="form-group"><label>Days Until Card Due</label><input type="number" id="days_due" value="5"></div>
            <div class="form-group"><label>Expected Card Payment</label><input type="number" id="card_payment" value="320000"></div>
            <div class="form-group"><label>30D Spending Growth Rate</label><input type="number" id="growth_rate" step="0.01" value="0.18"></div>

            <button onclick="runAnalysis()">Run Engine Analysis</button>
        </div>
        
        <div class="panel">
            <h2>AI Response</h2>
            <div id="loading" style="display: none; color: #666; font-style: italic;">Analyzing... (Might take a few seconds due to DiCE generation)</div>
            <pre id="result">{ "message": "Click 'Run Engine Analysis' to start." }</pre>
        </div>

        <script>
            async function runAnalysis() {
                const current_price = parseFloat(document.getElementById('current_price').value);
                const avg_price_30d = parseFloat(document.getElementById('avg_price_30d').value);
                const current_balance = parseFloat(document.getElementById('current_balance').value);
                const emergency_fund = parseFloat(document.getElementById('emergency_fund').value);
                const monthly_spending = parseFloat(document.getElementById('monthly_spending').value);

                const price_data = {
                    "brand": "Apple",
                    "category": "earbuds",
                    "seller_type": "official_mall",
                    "option_name": "pro",
                    "current_price": current_price,
                    "avg_price_7d": avg_price_30d * 0.98,
                    "avg_price_30d": avg_price_30d,
                    "min_price_30d": avg_price_30d * 0.85,
                    "max_price_30d": avg_price_30d * 1.15,
                    "coupon_applied": parseInt(document.getElementById('coupon_applied').value),
                    "card_discount_applied": 0,
                    "shipping_fee": parseFloat(document.getElementById('shipping_fee').value),
                    "inventory_status": "low_stock",
                };

                const finance_data = {
                    "monthly_total_spending": monthly_spending,
                    "monthly_fixed_spending": monthly_spending * 0.5,
                    "monthly_variable_spending": monthly_spending * 0.5,
                    "recent_30d_spending_growth_rate": parseFloat(document.getElementById('growth_rate').value),
                    "recent_90d_spending_trend": "increase",
                    "current_balance": current_balance,
                    "emergency_fund_balance": emergency_fund,
                    "debt_balance": 0,
                    "expected_card_payment_amount": parseFloat(document.getElementById('card_payment').value),
                    "days_until_card_due": parseInt(document.getElementById('days_due').value),
                    "avg_monthly_income": monthly_spending * 1.3,
                    "product_price": current_price,
                    "product_price_vs_monthly_spending": current_price / monthly_spending,
                    "product_price_vs_balance": current_price / current_balance,
                    "projected_balance_after_purchase": current_balance - current_price,
                    "product_price_vs_emergency_fund": current_price / emergency_fund,
                    "category_purchase_count_90d": 1,
                    "non_essential_flag": 1
                };

                document.getElementById('loading').style.display = 'block';
                document.getElementById('result').style.opacity = '0.5';

                try {
                    const response = await fetch('/analyze', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ price_data, finance_data })
                    });
                    const data = await response.json();
                    document.getElementById('result').textContent = JSON.stringify(data, null, 2);
                } catch (error) {
                    document.getElementById('result').textContent = "Error: " + error.message;
                } finally {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('result').style.opacity = '1';
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
