"""랩 페이지가 보여줄 성능 스냅샷을 만든다 (약 1~2분).

    cd backend/AI_TMP
    python -m ai.scripts.build_lab_snapshot

결과: ai/data/lab/evaluation_snapshot.json
점수는 합성 데이터(라벨=규칙)에서 '규칙을 얼마나 흉내 냈나'다. 정확도가 아니다.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT_PARENT = Path(__file__).resolve().parents[2]
if str(ROOT_PARENT) not in sys.path:
    sys.path.insert(0, str(ROOT_PARENT))

from ai.scripts.eval_finance_model import evaluate, evaluate_by_persona  # noqa: E402

OUTPUT = Path(__file__).resolve().parents[1] / "data" / "lab" / "evaluation_snapshot.json"


def main() -> None:
    by_persona = evaluate_by_persona(train_rows=8_000, test_rows=40_000, train_seeds=(1, 2, 3), test_seed=999)
    input_sets = evaluate(train_rows=8_000, test_rows=40_000, train_seeds=(1, 2, 3), test_seed=998)
    snapshot = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "by_persona": by_persona,
        "input_sets": input_sets,
        "disclaimer": "라벨이 규칙으로 만든 합성 데이터라서 점수는 '규칙을 얼마나 흉내 냈나'다. 실제 사용자에 대한 정확도가 아니다.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"saved {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
