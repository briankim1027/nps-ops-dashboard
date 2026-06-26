# NPS 운영 Dashboard 개편안 — Risk Scorecard 중심 전환

## 결론

NPS 운영 Dashboard는 `문제 매장 table` 중심에서 **Care Priority Map + Risk Scorecard + Hot Spot Mesh + 매장 Action Card** 구조로 전환한다.

이번 개편의 핵심은 table을 없애는 것이 아니다. table은 마지막 확인/다운로드/원장 검증 용도로 남기고, 앞단은 운영자가 바로 판단할 수 있는 그래프형 scorecard로 바꾼다.

---

## 1. 화면 구조 변경 방향

기존 흐름은 매장별 table이 빨리 등장해서 정확해 보이지만, 운영자가 실제로 판단해야 하는 질문에는 약하다.

운영자가 보고 싶은 것은 이 순서다.

1. 이번 달 NPS가 목표권인가?
2. 최근 흐름이 좋아지는가, 나빠지는가?
3. 오늘 어디가 흔들리는가?
4. 어떤 매장을 먼저 봐야 하는가?
5. 왜 그 매장이 문제인가?
6. 어떤 업무유형을 코칭해야 하는가?
7. 원장/상세 table로 검증할 수 있는가?

따라서 화면 순서는 아래로 정리한다.

1. 월 전체 KPI Top Line
2. 월 전체 NPS Trend
3. 날짜/주차 Picker 기반 Flow 분석
4. 오늘 Snapshot
5. **매장 NPS Risk Map**
6. **Risk Score Top 20 Bar**
7. **NPS Hot Spot Mesh**
8. 단일 매장 Action Card
9. 상세 Table / 다운로드

---

## 2. 이번에 추가한 핵심 화면

### 2.1 매장 NPS Risk Map

첫 번째 문제 발견 화면은 table이 아니라 scatter/bubble chart다.

현재 구현 기준:

- X축: 비판매성 응답 수
- Y축: 비판매성 NPS
- Bubble size: 총응답 수
- Color: 진단 유형 / Care 등급
- Hover: 대리점, 총응답, 비판매성 응답, 비추천, 중립, priority score

해석은 명확하다.

- 오른쪽 아래: 비판매성 업무량이 많고 NPS가 낮음 → 즉시 케어
- 왼쪽 아래: 업무량은 적지만 NPS가 낮음 → 표본 확인 필요
- 오른쪽 위: 업무량이 많지만 NPS 양호 → 우수 사례 후보
- 왼쪽 위: 정상/관찰

이 화면은 `어느 매장을 먼저 봐야 하는가`를 table보다 빠르게 보여준다.

### 2.2 Risk Score Top 20 Bar

두 번째 화면은 horizontal bar chart다.

현재 구현 기준:

- Y축: 매장명
- X축: 비판매성 Care Priority Score
- Color: 진단 유형
- Hover: 대리점, NPS, 응답 수, 비추천 수

이 화면은 단순히 NPS 낮은 순서가 아니라, **오늘 케어해야 할 순서**를 보여준다.

현재 score는 기존 dashboard의 운영 우선순위 산식과 연결되어 있다.

```text
우선순위점수 = 비추천×10
            + 중립×3
            + 목표까지 필요추천수×2
            + min(총응답자,30)/10
            + 목표미달Gap절대값/10
```

다음 단계에서는 이 score를 `Care Priority Score`라는 명칭으로 정리하고, 최근 7일 악화 추세와 비판매 업무 부담도를 추가한다.

---

## 3. Hot Spot Mesh 추가 방향

### 3.1 날짜 × 매장 Heatmap

이번 개편에 포함한다.

현재 구현 기준:

- X축: 업무처리일
- Y축: 매장
- 색상: 중립/비추천 Risk 건수
- 표시 대상: Risk/응답량 기준 상위 25개 매장

이 화면은 아래 질문에 답한다.

- 특정 날짜에 전체적으로 나빠졌는가?
- 특정 매장만 반복적으로 흔들리는가?
- 특정 대리점 산하 매장이 같이 흔들리는가?
- 월말/주말/정책 변경일 근처에 risk가 몰리는가?

즉, `어디가 문제인가`에서 `언제부터 문제인가`까지 확장한다.

### 3.2 요일 × 4개 시간대 Hotspot

Brian 의견을 반영해 같이 구현 대상으로 넣었다.

목표 화면:

- X축: 4개 시간대
  - 오전 09-12
  - 점심 12-14
  - 오후 14-17
  - 저녁 17-21
- Y축: 요일
- 색상: Hotspot Score
- Hover: 응답 수, 중립, 비추천, NPS

다만 현재 6월 NPS 원장에는 고객 방문/처리 **시간 컬럼이 없다**. 현재 들어있는 것은 `process_date`, `evaluation_date`처럼 날짜 수준이다.

그래서 구현은 두 단계로 처리했다.

1. 현재 데이터 기준
   - 요일별 비판매성 응답량과 Risk 건수를 bar chart로 표시
   - 4개 시간대는 데이터 계약 메시지로 노출

2. 향후 시간 컬럼이 들어오는 경우
   - `고객방문일시`, `방문시간`, `처리일시`, `처리시간`, `visit_datetime`, `process_datetime` 등 컬럼을 자동 인식
   - 오전/점심/오후/저녁 4구간 heatmap으로 자동 전환

이렇게 해두면 지금 화면은 거짓 패턴을 만들지 않고, 추후 source가 보강되면 바로 Mesh 화면으로 확장된다.

---

## 4. 구현 파일

### 데이터 산출

- `src/nps_ops/insights.py`
  - `build_store_daily_heatmap()` 추가
  - `build_weekday_time_hotspots()` 추가
  - timestamp 후보 컬럼 자동 탐색 로직 추가

- `scripts/build_data.py`
  - `store_daily_heatmap_전북_YYYYMMDD.parquet` 산출
  - `weekday_time_hotspots_전북_YYYYMMDD.parquet` 산출
  - Excel export에 `store_daily_heatmap`, `weekday_time_hotspots` sheet 추가

### Dashboard UI

- `app.py`
  - `매장 NPS Risk Map` section 추가
  - `Risk Score Top 20 Bar` 추가
  - `NPS Hot Spot Mesh` 추가
  - 시간 컬럼 부재 시 안내 메시지 + 요일 workload bar 표시

### Test

- `tests/test_metrics.py`
  - 날짜×매장 heatmap 집계 test 추가
  - 시간 컬럼 존재 시 4개 시간대 bucket test 추가
  - 날짜-only source일 때 `시간정보 없음` 처리 test 추가

---

## 5. 검증 결과

실행 결과:

```bash
.venv/bin/python -m pytest -q
# 19 passed in 0.53s

bash scripts/run_build.sh
# BUILD_OK
# store_daily_heatmap: data/processed/store_daily_heatmap_전북_20260624.parquet
# weekday_time_hotspots: data/processed/weekday_time_hotspots_전북_20260624.parquet
```

Dashboard 확인:

```bash
.venv/bin/python -m streamlit run app.py --server.headless true --server.port 8503
curl -I http://localhost:8503
# HTTP/1.1 200 OK
```

브라우저에서 Streamlit 화면 로딩과 console error 없음 확인.

---

## 6. 다음 작업

### 우선순위 1: 단일 매장 Action Card 고도화

현재 Action Sheet table은 이미 있다. 다음 단계는 선택형 Action Card로 바꾸는 것이다.

구성:

- 매장명 / 대리점명
- 월누적 NPS / 최근 7일 NPS / 오늘 NPS
- 응답 수 / 추천 / 중립 / 비추천
- 판매성 NPS / 비판매성 NPS
- 주요 비추천 업무유형 Top 3
- 대표 VOC
- 추천 action

### 우선순위 2: Care Priority Score 재정의

현재 score는 기존 운영 우선순위 산식이다. 다음 단계에서는 아래 5요소로 명시적으로 재정의한다.

| 구성요소 | 점수 | 의미 |
|---|---:|---|
| NPS Gap | 30 | 목표 대비 낮은 정도 |
| Detractor Count | 25 | 실제 비추천 절대량 |
| Recent Trend | 20 | 최근 7일 악화 여부 |
| Non-sales Pressure | 15 | 비판매성 업무 부담 |
| Sample Weight | 10 | 표본 신뢰도 보정 |

### 우선순위 3: 시간 컬럼 source 확보

요일×4개 시간대 hotspot을 완성하려면 source에 시간 정보가 필요하다.

필요 컬럼 후보:

- 고객방문일시
- 방문시간
- 처리일시
- 처리시간
- visit_datetime
- process_datetime

현재 코드는 위 컬럼이 들어오면 자동으로 4개 시간대 heatmap을 만든다.
