import requests
import json
from datetime import datetime

def test_ai_analyze():
    url = "http://localhost:8000/api/v1/analyze"

    payload = {
        "user_profile": {
            "user_id": "user123",
            "name": "홍길동",
            "monthly_income": 5000000
        },
        "card_transactions": [
            {
                "transaction_date": "20240322",
                "transaction_time": "123000",
                "merchant_name": "스타벅스",
                "category_name": "coffee",
                "transaction_amount": 5500,
                "description": "cafe"
            },
            {
                "transaction_date": "20240321",
                "transaction_time": "190000",
                "merchant_name": "배달의민족",
                "category_name": "food",
                "transaction_amount": 25000,
                "description": "delivery"
            }
        ],
        "account_transactions": [
            {
                "transaction_date": "20240322",
                "transaction_time": "090000",
                "transaction_type": "2",
                "transaction_amount": 5500,
                "after_balance": 1000000,
                "transaction_summary": "스타벅스 결제"
            }
        ],
        "start_date": "2024-03",
        "end_date": "2024-03",
        "include_ai": True
    }

    print(f"Testing AI Server at: {url}")
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            print("Successfully received AI report!")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"Error ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"Failed to connect to AI server: {e}")
        print("Tip: Make sure to start the AI server first with 'uvicorn main:app' in ai/src")

def test_strict_sec():
    url = "http://localhost:8000/api/v1/strict-secretary"

    payload = {
        "user_profile": {
            "user_id": "user123",
            "name": "홍길동",
            "monthly_income": 5000000
        },
        "item_text": "최신형 노트북",
        "item_link": "https://example.com/laptop",
        "user_reason": "코딩 공부를 더 열심히 하려고요!",
        "recent_transactions": [
            {
                "transaction_date": "20240320",
                "transaction_time": "150000",
                "merchant_name": "애플스토어",
                "category_name": "shopping",
                "transaction_amount": 2500000
            }
        ]
    }

    print(f"\nTesting Strict Secretary at: {url}")
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            print("Successfully received Fact Violence!")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
            return response.json().get("fact_violence_comment")
        else:
            print(f"Error ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"Failed to connect to AI server: {e}")
    return None

def test_tts(text):
    if not text: return
    url = "http://localhost:8000/api/v1/strict-secretary/tts"
    payload = {"text": text}

    print(f"\nTesting TTS at: {url}")
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            print(f"Successfully received TTS audio! Size: {len(response.content)} bytes")
        else:
            print(f"Error ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"Failed to connect to AI server: {e}")

if __name__ == "__main__":
    test_ai_analyze()
    comment = test_strict_sec()
    test_tts(comment)
