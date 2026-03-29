import argparse
import sys
import json
from pathlib import Path

from strict_secretary.models import PurchaseRequest
from strict_secretary.service import evaluate_purchase_intention

def main():
    parser = argparse.ArgumentParser(description="Test Strict Fact Violence AI Secretary")
    parser.add_argument("--user_id", type=str, required=True, help="User ID (e.g., U1001)")
    parser.add_argument("--item_text", type=str, required=True, help="Item name or text description")
    parser.add_argument("--item_link", type=str, required=True, help="Item product link")
    parser.add_argument("--user_reason", type=str, required=True, help="Reason/excuse for buying")

    args = parser.parse_args()

    data_dir = Path("data")
    if not data_dir.exists():
        print(f"Error: data directory not found at {data_dir.absolute()}")
        sys.exit(1)

    request = PurchaseRequest(
        user_id=args.user_id,
        item_text=args.item_text,
        item_link=args.item_link,
        user_reason=args.user_reason
    )

    print(f"\n--- 깐깐한 비서에게 결재 올리는 중... ---")
    print(f"사용자: {request.user_id}")
    print(f"품목: {request.item_text}")
    print(f"링크: {request.item_link}")
    print(f"변명: {request.user_reason}")
    print("-" * 40)

    try:
        response = evaluate_purchase_intention(data_dir, request)
        print("\n[비서의 답변]")
        print(f"결재 승인: {'승인 O' if response.is_approved else '반려 X'}")
        print(f"\n팩트폭력 코멘트:\n{response.fact_violence_comment}")
        print("\n판단 근거:")
        for idx, reason in enumerate(response.reasoning, 1):
            print(f"{idx}. {reason}")

    except Exception as e:
        print(f"\n오류 발생: {e}")

if __name__ == "__main__":
    main()
