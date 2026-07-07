# 260708 Work-through — NPS Ops Dashboard VOC 보강 및 Benchmark Gap UI 개선

## 결론

오늘 작업의 핵심은 NPS Ops Dashboard의 비판매성 Drill-down 영역에 **상반기 누적 VOC 보강 레이어**를 추가하고, `본부 Benchmark Gap` 탭을 현장 코칭용으로 더 바로 읽히게 정리한 것입니다.

최종 반영 방향은 다음과 같습니다.

- 운영 기준일 Action Card와 상반기 누적 VOC 보강 데이터를 분리했습니다.
- `본부 Benchmark Gap` 탭에 매장×업무유형 기준 본부 평균 대비 Gap을 추가했습니다.
- `상반기 누적 업무유형 Risk 분포`와 `상반기 누적 Risk 상위 20개 매장` 차트를 추가했습니다.
- Risk 상위 매장 그래프는 **Top 15 → Top 20**으로 확장했습니다.
- Top 20 stacked bar는 화면 기준 **위에서부터 Risk건수 내림차순**으로 보이게 수정했습니다.
- 동일 `business_type`은 상단 업무유형 bar와 하단 Top 20 stacked bar에서 **동일 색상**을 사용하도록 고정했습니다.

---

## 1. 수정 파일 요약

현재 작업 트리 기준 주요 수정 파일은 아래 4개입니다.

| 파일 | 주요 변경 |
|---|---|
| `app.py` | Dashboard UI 탭 확장, VOC 보강 reference layer 로딩, `본부 Benchmark Gap`/`매장별 VOC Theme`/`우수 VOC Library` 탭 추가, Benchmark Gap 내 신규 차트 및 색상/정렬 보정 |
| `scripts/build_data.py` | raw VOC ledger/reference workbook 처리 경로 추가, VOC 보강 artifact 생성 및 audit export 추가 |
| `src/nps_ops/insights.py` | VOC 분류/우수 VOC 분류, 본부 Benchmark Gap, 반복 VOC Theme, 우수 VOC Library builder 추가 |
| `src/nps_ops/parser.py` | raw ledger workbook 감지 및 raw response/store/agency/negative/crew parsing 추가 |

---

## 2. 데이터 운영 기준 정리

이번 수정에서 가장 중요한 기준은 **운영 기준 데이터와 reference 보강 데이터의 분리**입니다.

### 2.1 운영 NPS 기준

기존 Action Card, 우선관리 매장, 일별 추이 등은 사용자가 선택한 `selected_date` 기준의 운영 데이터로 유지했습니다.

- 예: `store_priority_전북_YYYYMMDD.parquet`
- 목적: 오늘/기준일 기준으로 어느 매장을 먼저 볼지 판단

### 2.2 VOC 보강 기준

`voc_benchmark_gap`, `repeated_voc_themes`, `positive_voc_library`는 최신 reference layer를 사용하도록 분리했습니다.

- 예: `voc_benchmark_gap_전북_20260707.parquet`
- 목적: 운영 당일 지표가 아니라, **'26년 상반기 누적 VOC 패턴**을 참고해 코칭 포인트를 보강

사이드바에는 아래처럼 기준을 분리 표시하도록 했습니다.

```text
운영 NPS 기준: YYYY-MM-DD · VOC 보강 기준: YYYY-MM-DD
```

---

## 3. 비판매성 Drill-down 탭 확장

기존 비판매성 Drill-down은 4개 탭이었습니다.

1. 집중관리 매장
2. 업무유형 Top
3. 매장별 추이
4. 판매성 양호·비판매성 취약

이번 작업 후 7개 탭으로 확장했습니다.

1. 집중관리 매장
2. 업무유형 Top
3. 매장별 추이
4. 판매성 양호·비판매성 취약
5. **본부 Benchmark Gap**
6. **매장별 VOC Theme**
7. **우수 VOC Library**

단, 이번 중점 수정은 `본부 Benchmark Gap` 탭이며, `매장별 VOC Theme`와 `우수 VOC Library`는 상반기 누적 VOC 보강 레이어로 분리해 배치했습니다.

---

## 4. 본부 Benchmark Gap 탭 개선

### 4.1 본부 평균 대비 매장×업무유형 Gap

`본부 Benchmark Gap` 탭에서는 매장×업무유형 단위로 아래 값을 비교하도록 했습니다.

```text
본부 평균 대비 차이 = 해당 매장×업무유형 NPS - 본부 전체 같은 업무유형 NPS
```

해석 기준은 다음과 같습니다.

- `- Gap`: 본부 평균보다 낮음 → 코칭 우선 확인 후보
- `+ Gap`: 본부 평균보다 높음 → 우수 사례·벤치마크 후보
- 기준기간: `'26년 상반기(1월~6월) 누적 데이터`

### 4.2 상반기 누적 업무유형 Risk 분포 추가

`voc_benchmark_gap` artifact에는 `voc_category`나 원문 `reason_text`가 없고, `business_type`과 `risk_count`가 있습니다.

따라서 Benchmark 탭의 누적 Risk 분포는 임의 VOC Theme가 아니라, 실제 컬럼으로 검증 가능한 `business_type` 기준으로 집계했습니다.

차트 목적은 다음과 같습니다.

- 전북팀 상반기 누적 비판매성 Risk가 어느 업무유형에 집중되어 있는지 확인
- 운영 기준일 Action Card가 아니라, 상반기 전체 패턴을 보는 reference chart로 사용

확인된 업무유형 예시는 다음과 같습니다.

- `요금수납`
- `요금제변경`
- `약정할인`
- `USIM카드변경`
- `기기변경`
- `부가서비스`
- `부가요금제`
- `명의변경`

### 4.3 상반기 누적 Risk 상위 매장 Top 20 추가

기존 요청 흐름에서 `상반기 누적 Risk 상위 15개 매장`을 **Top 20**으로 확장했습니다.

정렬 기준은 다음과 같습니다.

```text
store_name별 risk_count 합산 → risk_count 내림차순 → 상위 20개
```

최종 화면 검증 기준 상단 순서는 다음처럼 확인했습니다.

1. `군산진포 희망점`
2. `전북정읍 본점`
3. `김제중앙 본점`
4. 이후 Risk건수 순
...
20. `전북나은 부안점`

Plotly horizontal stacked bar는 y축 category 표시가 직관과 다르게 보일 수 있어, 실제 브라우저 렌더링 기준으로 재검증했습니다. 최종 코드는 `top_store_order`를 그대로 `category_orders`에 전달하는 방식이 화면상 위→아래 내림차순과 일치했습니다.

```python
category_orders={"store_name": top_store_order, "business_type": business_type_order}
```

---

## 5. 업무유형별 색상 일관성 수정

사용자 확인 중, 상단 `상반기 누적 업무유형 Risk 분포`와 하단 `상반기 누적 Risk 상위 20개 매장` stacked bar에서 같은 업무유형인데 색상이 다르게 보이는 문제가 있었습니다.

원인은 Plotly Express가 각 chart에서 `color_discrete_sequence`를 별도로 적용하면서, 차트별 등장 순서에 따라 색상을 다시 할당했기 때문입니다.

해결 방식은 공통 color map을 생성하고 두 그래프에 동일하게 주입하는 방식으로 정리했습니다.

```python
business_type_order = team_type_risk["business_type"].tolist()
benchmark_type_palette = px.colors.qualitative.Set2 + px.colors.qualitative.Bold + px.colors.qualitative.Pastel
benchmark_type_color_map = {
    business_type: benchmark_type_palette[i % len(benchmark_type_palette)]
    for i, business_type in enumerate(business_type_order)
}
```

두 chart 모두 아래 설정을 공유합니다.

```python
color_discrete_map=benchmark_type_color_map
category_orders={"business_type": business_type_order}
```

Top 20 stacked bar에서는 매장 순서와 업무유형 순서를 함께 고정했습니다.

```python
category_orders={"store_name": top_store_order, "business_type": business_type_order}
color_discrete_map=benchmark_type_color_map
```

검증된 색상 매핑은 다음과 같습니다.

| 업무유형 | 색상 |
|---|---|
| 요금수납 | `rgb(102,194,165)` |
| 요금제변경 | `rgb(252,141,98)` |
| 약정할인 | `rgb(141,160,203)` |
| USIM카드변경 | `rgb(231,138,195)` |
| 기기변경 | `rgb(166,216,84)` |
| 부가서비스 | `rgb(255,217,47)` |
| 부가요금제 | `rgb(229,196,148)` |
| 명의변경 | `rgb(179,179,179)` |

---

## 6. 빌드 및 검증 내역

### 6.1 코드 컴파일

```bash
. .venv/bin/activate && python -m py_compile app.py scripts/build_data.py src/nps_ops/*.py
```

결과: 성공

추가 UI 수정 후 개별 검증도 수행했습니다.

```bash
. .venv/bin/activate && python -m py_compile app.py
```

결과: 성공

### 6.2 데이터 빌드

```bash
. .venv/bin/activate && python scripts/build_data.py
```

결과: `BUILD_OK`

확인된 운영 기준 source는 `●26년07월 NPS평가 통계_0706.xlsx`이며, report date는 `2026-07-06` 기준으로 확인했습니다.

### 6.3 테스트

```bash
. .venv/bin/activate && python -m pytest -q tests
```

결과:

```text
23 passed in 1.64s
```

### 6.4 Streamlit 브라우저 검증

Streamlit을 로컬에서 실행해 실제 UI를 확인했습니다.

확인 항목:

- `본부 Benchmark Gap` 탭 노출
- `상반기 누적 업무유형 Risk 분포` chart 노출
- `상반기 누적 Risk 상위 20개 매장` chart 노출
- Top 20 y축 표시 순서가 화면 위에서부터 내림차순인지 확인
- `군산진포 희망점`이 최상단, `전북정읍 본점`이 두 번째인지 확인
- 동일 `business_type` 색상이 두 차트에서 일치하는지 Plotly trace 기준 확인
- 브라우저 JS console error 및 Streamlit exception 없음 확인

검증 완료 후 Streamlit 검증 프로세스는 종료했습니다.

---

## 7. 현재 Git 상태 메모

작업 후 `git status --short` 기준 주요 변경 상태는 다음과 같습니다.

```text
 M app.py
 M scripts/build_data.py
 M src/nps_ops/insights.py
 M src/nps_ops/parser.py
?? 260629_workthru.md
?? codex.jpg
?? reports/nps_voc_260707_analysis.md
```

이번 문서 생성으로 아래 파일이 추가됩니다.

```text
?? 260708_workthru.md
```

아직 commit/push는 하지 않았습니다.

---

## 8. 운영 관점 시사점

이번 변경의 의미는 단순 차트 추가가 아니라, **기준일 운영관리와 상반기 누적 coaching reference를 한 화면 안에서 구분해 보여주는 것**입니다.

- Action Card는 오늘 기준 “어디를 먼저 볼 것인가”를 담당합니다.
- Benchmark Gap은 상반기 누적 기준 “어떤 업무유형/매장 조합이 구조적으로 취약한가”를 보여줍니다.
- Top 20 stacked bar는 매장별 Risk 크기와 업무유형 구성을 한 번에 보여줘, 현장 코칭 시 우선순위와 대화 주제를 같이 잡을 수 있습니다.
- 업무유형별 색상을 통일해, 상단 분포와 하단 매장별 breakdown을 같은 언어로 읽을 수 있게 했습니다.

---

## 9. 남은 주의사항

- `voc_benchmark_gap` artifact에는 현재 `voc_category`와 `reason_text`가 없으므로, Benchmark 탭에서는 VOC Theme가 아니라 `business_type` 기준으로 보는 것이 맞습니다.
- `매장별 VOC Theme` 탭은 운영 데이터/반복 VOC Theme 관점이고, `본부 Benchmark Gap` 탭은 상반기 누적 benchmark 관점입니다. 두 탭의 목적을 섞지 않는 것이 좋습니다.
- 현재 변경사항은 로컬 작업 트리에만 있으며, 배포하려면 별도 commit/push가 필요합니다.
