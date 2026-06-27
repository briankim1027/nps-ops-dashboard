# 260627 Work-through — Care Priority Light Revision & Hot Spot 반복성 view

## 결론

오늘은 Care Priority 산식을 **full redesign이 아니라 Light Revision** 범위로 정리했다. 핵심은 두 가지다.

1. Care Priority를 `Base Risk Score × Sample Confidence` 구조로 바꿔 **소표본 매장이 과도하게 상위에 올라오는 착시를 완화**했다.
2. Hot Spot 날짜×매장 heatmap을 **반복 발생(2일 이상) 매장 강조 view**로 바꾸고, 요일 그래프 tooltip에 risk율을 추가했다.

기존 운영 흐름·UX 개선사항(jitter, legend top, dynamic count, quadrant, 공통매장 강조 등)은 그대로 유지했다.

## 작업 범위

- `src/nps_ops/config.py` — Sample Confidence 티어 상수
- `src/nps_ops/metrics.py` — `sample_confidence()` 헬퍼 + `priority_score` multiplier
- `src/nps_ops/insights.py` — `_axis_calc` 축별 점수 multiplier
- `app.py` — 화면 label/note/tooltip, 선택축 점수 multiplier, Risk Map 유형구분 box 레이아웃, Hot Spot 반복성 view, 요일 tooltip

## 1. Care Priority Light Revision

### 1-1. 산식 구조 변경

```text
Care Priority = Base Risk Score × Sample Confidence
Base Risk Score = 비추천×10 + 중립×3 + 목표까지 필요추천수×2 + min(응답,30)/10 + 목표미달Gap절대값/10
```

- Base 산식 자체는 **유지**하고, 가산이 아닌 **곱셈 보정(Sample Confidence)** 만 추가했다.
- 산식이 계산되는 3곳에 일관 적용:
  - `metrics.py build_store_priority` → `priority_score` (비판매성 응답수 기준 multiplier)
  - `insights.py _axis_calc` → `axis_priority_score` (해당 축 응답수 기준)
  - `app.py prepare_axis_table` → `선택축_priority_score` (선택축 응답수 기준)

### 1-2. Sample Confidence 기준 (config 상수, 비판매성 응답 n)

| n | multiplier |
|---|---:|
| 20+ | ×1.00 |
| 10~19 | ×0.85 |
| 5~9 | ×0.70 |
| <5 | ×0.50 (`샘플 착시형` 분류 제외 구조는 유지) |

`config.py`의 `CARE_PRIORITY_SAMPLE_CONFIDENCE` / `CARE_PRIORITY_LOW_SAMPLE_MULTIPLIER`로 분리해 튜닝 가능.

### 1-3. 명칭 통일

- 사용자-facing label `우선순위점수` → `Care Priority`로 통일 (내부 변수명은 유지).
- formula note 2개를 `Base Risk Score × Sample Confidence` 설명으로 갱신.

### 1-4. 실데이터 효과 확인 (6/24)

- **순창 본점**(비판매성 n=2): base 75.97 → ×0.50 = 37.98 → 기존 #3에서 Top 8 밖으로 하락.
- 고표본 매장(군산진포 희망점 n=27, 전북정읍 본점 n=32, ×1.0) 상대 상승.
- Sample Confidence 분포: ×0.5=10곳 / ×0.7=26곳 / ×0.85=23곳 / ×1.0=5곳.

## 2. 업데이트한 graph 4개

### 2-1. Risk Map 2개

- **버블 scatter**: tooltip에 `Sample Confidence=×N.NN` 추가. jitter/음수압축/legend top/quadrant/dynamic count 유지.
- **Risk Score Top 20 bar**: `prepare_axis_table` multiplier 자동 반영. hover에 `비판매성 응답`, `Sample Confidence` 추가.

### 2-2. Hot Spot 2개

- **날짜×매장 heatmap → 반복성 강조 view**:
  - `hot_spot_store_rank`에 `risk_days`(risk 발생한 서로 다른 날 수) 계산.
  - **risk_days >= 2 매장만** 추려 발생일 수 → risk건수 → 응답 순 정렬.
  - 매장 라벨에 `(N일)` 표기, 공통 action 매장은 `<b><i>` 강조 유지.
  - 필터 결과 0이면 안내 메시지 가드.
- **요일 bar**: tooltip에 `Risk율` 추가 (`risk_count / total_responses`). 별도 캡션 없이 금요일 risk율↑이 hover로 읽힘.

### 데이터 근거 (왜 반복성 view인가)

- 6월 날짜×매장 cell 464개 중 risk>0은 61개(13%)뿐이고 risk_count 분포가 `0:403 / 1:59 / 2:2`.
- 거의 모든 hot cell이 1건짜리 단발 → 색 농도(heat) 신호가 약함.
- 진짜 반복 신호는 16곳(2일+): 군산진포 희망점(4일), 전북정읍 본점·서정 호성점·본 본텔점(각 3일) 등.
- 요일은 금요일 risk율 14.1%가 유일한 약한 패턴(표본 작음) → tooltip 참고 수준으로만 노출.

## 3. Risk Map 유형구분 box 레이아웃

- `.skt-help-grid` 4열 → 3열로 변경 → 상단 3개(즉시 개선형·비판매성 취약형·구조 개선형) / 하단 2개(판매성 취약형·우수 확산형).
- `.skt-chip`에 `white-space:nowrap` 추가 → 라벨 제목 2줄 줄바꿈 방지, chip 높이 통일.
- `skt-help-grid`는 이 box 전용이라 Time Intelligence box 등엔 영향 없음.

## 4. 검증 기록

```bash
.venv/bin/python -m py_compile app.py src/nps_ops/config.py src/nps_ops/metrics.py src/nps_ops/insights.py   # COMPILE_OK
.venv/bin/python -m pytest -q                                                                                 # 19 passed
bash scripts/run_build.sh                                                                                      # 전 parquet 재생성 OK
.venv/bin/python -m streamlit run app.py --server.headless true --server.port 8505                            # 정상 기동, 전 차트/표 렌더 에러 없음
```

- 테스트는 `priority_score` 수치를 직접 단언하지 않고 `nps_recalc`/`diagnosis_type`만 보므로 multiplier 적용해도 그대로 통과.

## 5. 다음 작업 — Action Card (별도 새 세션)

다음 세션에서 **단일 매장 Action Card** 신규 설계/개발을 진행한다. (이번 scope에서 의도적으로 제외)

참고:
- 설계 메모: `reports/02_risk_scorecard_redesign.md`의 "우선순위 1: 단일 매장 Action Card 고도화".
- 현재 `build_store_action_sheet`(insights.py) / Action Sheet table이 이미 있으니, 이를 선택형 Card로 확장하는 방향.
- 구성 후보: 매장명/대리점, 월누적·최근7일·오늘 NPS, 응답/추천/중립/비추천, 판매성/비판매성 NPS, 주요 비추천 업무유형 Top3, 대표 VOC, 추천 action.

## 6. 후속 개선사항 (보류)

- Recent Trend badge / 점수 반영 (소표본에서 noise 우려 → 보류)
- Care Priority full redesign (NPS Gap/Detractor/Trend/Pressure/Sample 5요소 모델)
- 결과 라벨 기반 가중치 검증, 산식 A/B·backtesting
- 반복 view에서 응답 5건 미만 매장 추가 제외 여부 (순창 본점 n=2 등)
- Hot Spot 요일×4개 시간대 heatmap (원장에 시간 컬럼 들어오면 자동 전환)

## 재개 명령어

```bash
cd /home/brian/workplace/nps-ops-dashboard
.venv/bin/python -m streamlit run app.py --server.headless true --server.port 8502
.venv/bin/python -m pytest -q
```
