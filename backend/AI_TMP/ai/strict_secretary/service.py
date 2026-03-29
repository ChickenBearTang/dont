from __future__ import annotations

from pathlib import Path

from strict_secretary.models import PurchaseRequest, SecretaryResponse
from strict_secretary.loader import (
    get_user_profile,
    get_recent_card_transactions,
    get_explain_logs,
    get_latest_ai_report
)
from strict_secretary.agent import StrictSecretaryAgent
import urllib.request
import re

def fetch_url_text(url: str) -> str:
    if not url or not url.startswith("http"):
        return "유효한 링크가 아닙니다."
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            html = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', html, flags=re.IGNORECASE | re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()[:20000]  # Increased limit
    except Exception as e:
        return f"웹페이지 내용을 가져오지 못했습니다. 오류: {str(e)}"

def evaluate_purchase_intention(data_dir: Path, request: PurchaseRequest) -> SecretaryResponse:
    """
    Main orchestrator for the 'Fact Violence AI Secretary'.
    Gathers user data and evaluates the purchase intention using LLM.
    """
    profile = get_user_profile(data_dir, request.user_id)
    recent_txs = get_recent_card_transactions(data_dir, request.user_id, months_back=2)
    explain_logs = get_explain_logs(data_dir, request.user_id)
    ai_report = get_latest_ai_report(data_dir, request.user_id)

    tx_summary = []
    for tx in recent_txs[-50:]:  # max 50 recent transactions
        tx_summary.append({
            "date": tx.approved_at.strftime("%Y-%m-%d"),
            "merchant": tx.merchant_name,
            "amount": tx.amount,
            "category": tx.category
        })

    profile_dict = {
        "monthly_income": profile.monthly_income,
        "job": profile.job,
        "age": profile.age,
        "residence": profile.residence_type
    }

    page_content = fetch_url_text(request.item_link)

    agent = StrictSecretaryAgent()
    response = agent.evaluate_purchase(
        item_text=request.item_text,
        item_link=request.item_link,
        user_reason=request.user_reason,
        page_content=page_content,
        profile=profile_dict,
        recent_txs=tx_summary,
        explain_logs=explain_logs,
        ai_report=ai_report
    )

    return response
