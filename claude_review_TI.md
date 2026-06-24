# Claude Code Review — NPS 개선방향 TI

실행일: 2026-06-24
대상: `/home/mysktelecom/workplace/nps-ops-dashboard`
역할: reviewer only, no edits

## 결론

Claude 검토 결론은 명확했다. 현재 이슈는 단순 표시 문제가 아니라, `sales_nps_score`, `non_sales_nps_score`가 `0~1` 또는 `-1~1` 스케일인 상태에서 `target_score=87`과 직접 비교되어 진단 유형이 왜곡될 수 있다는 점이다.

특히 `비판매성 취약형` / `판매성 취약형`은 스케일이 0~1이면 조건상 도달이 어렵고, 대신 `구조 개선형` 또는 다른 유형으로 흘러갈 위험이 있다. 따라서 UI 미세 개선보다 NPS 스케일 표준화와 진단 분류 재검증을 먼저 해야 한다.

## 위험도 높은 이슈 Top 5

1. `diagnose_store()`에서 판매성/비판매성 축 비교가 `target_score=87`과 같은 스케일을 전제로 하고 있어, 0~1 값이 들어오면 분류가 왜곡됨.
2. `build_store_priority()`가 `sales_nps_score`, `non_sales_nps_score`를 표준화하지 않은 채 downstream parquet에 저장함.
3. `회복 가능형`이 `비판매성 취약형` / `판매성 취약형`보다 먼저 잡히면 축 기반 코칭 신호가 가려질 수 있음.
4. `build_store_action_sheet()`의 store_code fallback 조인이 store_name 기반이라 동명 매장이 있으면 VOC 연결 오류 가능성이 있음.
5. Markdown export에서 `nps_score=None`인 경우 formatting 오류 가능성이 있음.

## Claude 권장 구현 순서

1. `metrics.py`에 `normalize_nps_series()` 추가
2. `build_store_priority()` 진입 시 NPS 원천 컬럼 표준화
3. `diagnose_store()` 단위 테스트 추가 및 분류 재검증
4. `비판매성/판매성 취약형`을 `회복 가능형`보다 앞쪽으로 이동 검토
5. `build_sales_good_non_sales_weak()`의 임시 보정을 공통 함수로 대체
6. build 후 스케일 범위와 진단 유형 분포 regression check 추가
7. Markdown None-safe formatting 보완

## Hermes 반영 결정

Claude 의견 중 즉시 반영할 항목:

- 공통 `normalize_nps_series()` 추가
- `build_store_priority()`에서 `nps_score`, `prev_nps_score`, `hq_nps_score`, `sales_nps_score`, `non_sales_nps_score` 표준화
- `diagnose_store()` 룰 순서 조정: `즉시 개선형` 우선, 이후 `우수 확산형`, 축 취약형, 구조 개선형, 회복 가능형 순
- `build_sales_good_non_sales_weak()`에서 임시 보정 대신 공통 normalize 함수 사용
- build 결과에 `scale_warnings` 추가
- Markdown score formatting을 None-safe로 수정
- `tests/test_metrics.py` 추가

보류/후속 검토:

- store_name fallback 조인 개선은 실제 동명 매장 여부 확인 후 별도 보완
- 원천 NPS vs count 재계산 NPS 중 운영 기준을 어느 쪽에 둘지는 Brian과 기준 합의 후 추가 정리
