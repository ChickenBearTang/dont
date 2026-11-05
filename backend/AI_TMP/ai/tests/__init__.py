"""테스트 패키지.

실행 중에 파일을 쓰는 저장소(사용자 반응, 감사 로그, 입력 스냅샷)가 저장소 안의 data/ 를 건드리지 않도록
테스트가 쓰는 위치를 임시 디렉터리로 돌린다. config 가 import 되기 전에 정해져야 해서 여기서 한다.
"""

import os
import tempfile

os.environ.setdefault("AI_RUNTIME_DIR", tempfile.mkdtemp(prefix="ai-test-runtime-"))
