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

---

# 260627 (오후 추가) — 단일 매장 Action Card 구현

## 결론

`reports/02_risk_scorecard_redesign.md`의 "우선순위 1: 단일 매장 Action Card"를 실제 구현했다.
기존 `매장 개입 우선순위` 섹션(종합/판매성/비판매성 축 재정렬 table)은 Risk Map·Top20 bar와 기능이
겹쳐 유효성이 떨어져 **삭제**하고, 그 자리에 **`유형별 대응방안`** 섹션을 신설했다.

핵심 구조: **유형 탭 3개 → 대리점 expander → 2열 매장 Action Card.**

## 1. 설계 결정 (Brian과 논의 확정)

- **카드 제공 대상 = Care 3유형** (우선순위 = 심각도가 아니라 *행동 시급성·실행 가능성* 순):
  1. 즉시 개선형 (비추천≥2, 이미 터진 손상 복구)
  2. 비판매성 취약형 (비판매<목표·판매 OK, 코칭 전환)
  3. 구조 개선형 (양축 동시 미달, 대리점 단위 에스컬레이션)
- 회복 가능형(Quick Win)은 이번 scope에서 제외, 액션 문구는 **rule-based 유지**(재현성·검증성).
- UX는 (C) 카테고리 탭 + 대리점 expander 선택 → 스크롤 압박 최소화. default 탭 = 즉시 개선형.
- 정렬 = Care Priority 순(대리점 = 소속 최고 매장 점수 기준, 매장 = 점수순). 빈 탭 가드.
- redundant했던 `priority_formula_html`은 삭제(Top20 bar 아래 `risk_score_formula_html`이 이미 동일 설명).

## 2. 카드 4-zone 템플릿

운영자 질문 흐름(누구를 / 지금 상태 / 왜 문제 / 뭘 할지 / 다음 확인)을 4 zone으로:

- **① 식별** — 매장명·대리점·담당 marketer, 유형 badge, Care Priority #N, Sample Confidence
- **② 상태** — 월누적/최근7일/오늘 NPS(+▲▼ 추세 화살표), 목표Gap, 판매성/비판매성 NPS, 추천/중립/비추천
- **③ 근거** — 비추천 업무유형 Top, 대표 VOC 실인용
- **④ 액션** — 유형별 체크리스트 + 🎯정량 목표(필요추천수) + ✔다음 점검 지표

"손에 잡히게" 원칙: 대표 VOC 실인용 · 정량 목표 명시 · 체크리스트형 · 유형별 차별화 · 다음 확인 지표.

## 3. 유형별 분기 (③근거·④액션)

| | 즉시 개선형 | 비판매성 취약형 | 구조 개선형 |
|---|---|---|---|
| ③ biz Top 집계 | **비추천만** | 중립+비추천 | 중립+비추천 |
| ④ 액션 핵심 | 비추천 N건 전수 확인·클로징 | 중립 N건 추천 전환 | 대리점 합동 점검·2개월 로드맵 |
| 🎯 목표 | 비추천 → 0 | 추천 N건 확보(중립 우선 전환) | 이달+다음달 분할 |

## 4. 데이터 헬퍼 (`src/nps_ops/insights.py`)

- `build_store_action_card(store_row, store_negative, daily_lookup, target_score)` → 단일 매장 4-zone dict.
- `build_store_daily_lookup(response_fact, team)` → `{store_code: {today, recent7}}` (매장×날짜 1회 집계).
- `_card_actions()` 유형별 rule-based 문구, `ACTION_CARD_TYPES`, `NO_ISSUE_RE` 상수.

## 5. 실데이터 검증 중 발견한 품질 이슈 2건 (수정)

1. **대표 VOC가 "불편한 점 없었습니다" 류 무이슈 중립 코멘트를 끌어옴**
   (비추천 reason_text가 비어 중립 긍정 코멘트로 fallback).
   → 대표 VOC = **비추천 우선 + 무이슈 패턴 제외**(`NO_ISSUE_RE`). 부정 대상 단어(불편/문제/이상)를
   함께 봐서 "친절하지 않았어요"(=불친절) 같은 **진짜 불만은 보존**. 없으면 "대표 VOC 없음"으로 정직하게 degrade.
2. **"중립 6건 중 16건 전환"(필요추천>중립) 모순 문구**
   → "추천 N건 확보 — 중립 M건 우선 전환 대상"으로 정정.

## 6. 검증 기록

```bash
.venv/bin/python -m py_compile app.py src/nps_ops/insights.py            # COMPILE_OK
.venv/bin/python -m pytest -q                                            # 23 passed (19→23, Action Card 4건 추가)
.venv/bin/python -c "from streamlit.testing.v1 import AppTest; ..."      # 예외 0건, 신규 탭 3개·expander 19개 렌더
.venv/bin/python -m streamlit run app.py --server.headless --port 8502   # HTTP 200
# 실데이터 6/24: 29개 카드 생성 (즉시 14·비판매 13·구조 2)
```

## 7. 다음 후보

- 카드 밀도/2열 균형 등 시각 다듬기(브라우저 확인 피드백 반영)
- 회복 가능형 Quick Win 카드(보류) 재검토
- VOC 축 정밀 분리(response_fact NCSI 조인)로 비판매성 취약형 카드 biz Top 정확도 향상
- 카드 → CSV/PDF 현장 배포 export

---

# 260627 (저녁 추가) — Action Card 유형별 목표Gap 정합화 & 대리점별 출력

## 결론

Action Card의 `목표Gap`을 **종합 NPS 고정에서 "해당 카드가 문제 삼는 축" 기준으로** 바꿨다.
KPI 라벨도 비판매성 care 카드 성격에 맞게 명확화하고, **대리점 단위 출력(🖨️)** 기능을 추가했다.
구현 중 발견한 렌더링 버그 3건(비판매성 KPI·Gap 미표시, 출력 무반응)도 같은 뿌리에서 해결했다.

## 1. 유형별 목표Gap 기준 (지시서 반영)

`목표Gap`은 카드가 문제 삼는 축 기준으로 표시한다.

| 유형 | 표시 기준 | 예시 |
|---|---|---|
| 즉시 개선형 | 비판매성 Gap 우선 (판매성만 문제 시 fallback) | `비판매성 Gap -37.0p · 판매성 91 / 비판매성 50` |
| 비판매성 취약형 | 비판매성 Gap | `비판매성 Gap -9.2p · 판매성 89 / 비판매성 78` |
| 구조 개선형 | **양축 Gap 동시** + 종합 | `판매성 Gap -7.0p / 비판매성 Gap -37.0p · 종합 71` (+ 뒷줄 판매성 80 / 비판매성 50) |
| (향후) 판매성 취약형 | 판매성 Gap | — |

- 구조 개선형은 "양축이 같이 흔들리는 매장"이라 단일 Gap만 보여주면 부족 → 반드시 둘 다 표기.

## 2. KPI 라벨 비판매성 정합화

- `월누적` → **`종합`** (종합 NPS임을 명확화, 오해 방지).
- `최근7일`/`오늘` → **`최근7일 비판매성`/`오늘 비판매성`**: 종합값이 아니라 **비판매성 전용 일별 NPS**를 표시하도록 변경 (Care 카드가 비판매성 중심이므로 자연스러움).
- 이를 위해 `build_store_daily_lookup`에 비판매성(`NCSI=비판매성`)만 필터한 `ns_today`/`ns_recent7` 집계 추가.
- `build_store_action_card`에 `ns_recent7_nps`/`ns_today_nps`, `non_sales_gap`/`sales_gap` 필드 추가.

## 3. 렌더링 버그 3건 — 단일 뿌리 (Streamlit sanitizer)

증상: ① 최근7일/오늘 비판매성 숫자 미표시 ② 비판매성 Gap 미표시 ③ 🖨️ 출력 클릭 무반응.

- **원인**: `st.markdown(unsafe_allow_html=True)`의 보안 sanitizer가 `<script>`·`<button onclick>`을 제거.
  전체 카드를 `<button onclick>` + 통합 HTML 한 덩어리로 `st.markdown`에 넘겨, 비표준 요소 제거 과정에서
  블록이 깨져 숫자 누락 + 스크립트 제거로 출력 무반응이 동시 발생.
- **해결**: 대리점 카드 블록을 **`st.components.v1.html()` (iframe)** 으로 렌더.
  iframe 안에서는 JS 실행 + HTML이 sanitize 없이 그대로 렌더된다.
  - iframe은 부모 CSS 미상속 → 카드 CSS를 self-contained(`AC_CARD_CSS`, literal 색상)로 인라인.
  - `AC_COMPONENT_TEMPLATE` + `render_agency_action_block()`로 대리점별 iframe HTML/높이 생성.

## 4. 대리점별 출력 (🖨️)

- 각 대리점 expander 우측 상단 **🖨️ 아이콘 버튼** (텍스트 없이 아이콘만, 설명은 `title` 툴팁).
- 클릭 시 새 창에 해당 대리점 카드 HTML+CSS를 복사하고 `window.print()` 호출 → 대리점 단위 인쇄/PDF 저장.
- 사용자 클릭 기반이라 팝업 차단에 안 걸림(차단 시 안내 alert). 출력 제목 = 대리점명(특수문자 sanitize).

## 5. 검증 기록 (본텔점 지시서 검산 일치)

```bash
.venv/bin/python -m py_compile app.py src/nps_ops/insights.py   # COMPILE_OK
.venv/bin/python -m pytest -q                                   # 23 passed
.venv/bin/python -m streamlit run app.py --server.headless --port 8501   # HTTP 200
```

| 유형 | 매장 | 종합 | 최근7일 비판매성 | 오늘 비판매성 | Gap |
|---|---|---|---|---|---|
| 즉시 개선형 | 본텔점(본점) | 70 | 100 (n7) | – | 비판매성 Gap -37.0p · 판매성 91 / 비판매성 50 |
| 비판매성 취약형 | 군산진포 희망점 | 83 | 69 (n13) | – | 비판매성 Gap -9.2p · 판매성 89 / 비판매성 78 |
| 구조 개선형 | 신세계 고창점 | 71 | 0 (n2) | – | 판매성 Gap -7.0p / 비판매성 Gap -37.0p · 종합 71 |

- 본텔점 지시서 기준 일치: 비판매성 50.0 → Gap -37.0 ✓, 최근7일 100 ✓, 오늘 null(–) ✓, 판매성 90.9(91)·종합 69.6(70) 참조 ✓.

## 6. 운영 메모

- 깨진 `.venv/bin/streamlit` 런처(shebang이 `/home/mysktelecom/...` 가리킴) → **`python -m streamlit`** 로 실행.
