# 260626 Work-through — NPS Ops Dashboard

## 결론

오늘 작업은 전북팀 NPS 운영 Dashboard를 **현장 커뮤니케이션용 운영 화면**에 더 가깝게 다듬는 방향으로 진행했다. 핵심은 숫자를 더 많이 보여주는 것이 아니라, 구성원이 한눈에 “어느 매장을 왜 먼저 봐야 하는지” 이해하도록 chart 구조와 문구를 정리한 것이다.

## 작업 범위

- Streamlit dashboard: `/home/brian/workplace/nps-ops-dashboard/app.py`
- Risk Map UX/해석 구조 개선
- KPI/Trend/Hot Spot/Action Sheet 주변 구조는 이전 작업분과 함께 유지
- GitHub push 대상 repo: `https://github.com/briankim1027/nps-ops-dashboard.git`

## 오늘 대화에서 확정한 Risk Map 해석 기준

### 1. Risk Map은 월누적 기준으로 명시한다

사용자가 “이 chart가 매장별 월간 data 누적 기준인지”를 별도로 물어보지 않도록 제목에 기준을 박았다.

- 변경 후 제목: `매장 NPS Risk Map — 6월 월누적 기준`

### 2. Bubble size 의미를 명확히 한다

현재 chart 구조는 다음으로 확정했다.

- X축: `비판매성 응답 수`
- Y축: `비판매성 NPS`
- Bubble: `전체 응답건수`

따라서 “Bubble size = 비판매성 응답건수”가 아니라, **Bubble size = 전체 응답건수**로 커뮤니케이션한다. 비판매성 응답 수는 이미 X축에 들어가 있으므로, Bubble까지 같은 지표로 중복 표현하지 않는 쪽이 더 낫다고 판단했다.

Chart subtitle과 hover tooltip에 이 의미를 명시했다.

### 3. NPS -100은 sample size와 함께 해석한다

NPS -100은 모든 유효 응답이 비추천이었다는 강한 signal이다. 다만 응답 1~2건만으로도 -100이 나올 수 있으므로, 단독으로 “최악 매장”이라고 판단하지 않는다.

운영 해석 기준은 다음과 같다.

- `NPS -100 + 비판매성 응답 많음 + 전체 응답 많음` → 즉시 개입 후보
- `NPS -100 + 응답 1~2건` → 샘플 착시 가능성, VOC 원문 확인
- `NPS 낮음 + 중립/비추천 누적` → 설명/업무처리/마무리 멘트 점검 대상

### 4. 범례는 상단 horizontal 배치가 맞다

Risk Map의 범례는 chart 오른쪽/내부보다 chart 상단에 두는 것이 구성원 커뮤니케이션에 더 적합하다고 정리했다.

반영 사항:

- Plotly legend를 horizontal로 변경
- chart 상단으로 배치
- modebar가 legend와 겹치지 않도록 Risk Map의 Plotly toolbar를 숨김

### 5. 음수 NPS 구간은 압축한다

실제 매장이 `50~100` 구간에 몰려 있는데 `-100~100`을 동일 scale로 쓰면, 화면 공간이 비효율적으로 쓰이고 매장 간 차이가 잘 안 보인다.

반영 사항:

- 음수 NPS display 값은 `×0.2`로 압축
- 축 제목: `비판매성 NPS · 음수구간 압축`
- tick label은 원래 NPS 단위로 유지: `-100, -50, 0, 20, 40, 60, 80, 100`

즉, 실제 의미는 유지하되 운영자가 보는 화면에서는 양수 고밀도 구간의 차이를 더 잘 보이게 했다.

### 6. 4사분면 action zone과 5개 category legend를 분리한다

4사분면은 action zone, 색상 legend는 진단 category로 역할을 나눴다.

- 배경/action zone:
  - `안정/우수`
  - `우수 확산·과부하 경계`
  - `샘플/VOC 확인`
  - `즉시 개선 후보`
- Marker color/category:
  - `즉시 개선형`
  - `비판매성 취약형`
  - `구조 개선형`
  - `판매성 취약형`
  - `우수 확산형`

### 7. 추가 문구 정리

사용자 요청에 따라 다음 문구는 삭제했다.

- 삭제: `table보다 먼저 보는 운영 화면입니다.`

또한 `비판매성 응답 중앙값 9건` annotation은 chart 상단/중앙에 뜨지 않도록 조정했다.

- 변경 전: vertical line annotation으로 표시
- 변경 후: `샘플/VOC 확인` text와 같은 하단 y축 선상에 배치

## 주요 코드 변경 요약

### Risk Map subtitle

변경 후:

```text
X축=비판매성 응답 수 · Y축=비판매성 NPS · Bubble=전체 응답건수로 매장별 월누적 risk를 포지셔닝합니다.
```

### Risk Map y축 display 변환

```python
risk_map["non_sales_nps_display"] = risk_map["non_sales_nps_recalc"].map(
    lambda v: v if pd.isna(v) or v >= 0 else v * 0.2
)
```

### Tooltip 핵심 문구

```text
전체 응답건수(Bubble)=...
```

### Median annotation 위치

`비판매성 응답 중앙값 {x_threshold:.0f}건`을 `zone_label_y_bottom`에 배치해 `샘플/VOC 확인`과 같은 위치 선상에서 보이게 했다.

## 검증 기록

### 1. Python compile

```bash
.venv/bin/python -m py_compile app.py
```

결과: 통과.

### 2. Pytest

```bash
.venv/bin/python -m pytest -q
```

결과:

```text
19 passed in 0.78s
```

### 3. Browser/Streamlit visual check

Streamlit app:

```bash
.venv/bin/python -m streamlit run app.py --server.headless true --server.port 8502
```

확인한 사항:

- Risk Map 제목 정상 표시
- subtitle에서 X/Y/Bubble 의미 정상 표시
- 상단 horizontal legend 표시
- modebar 겹침 없음
- 음수구간 압축 y축 표시
- 목표 87선 표시
- 비판매성 응답 중앙값 기준선 표시
- 4사분면 배경/label 표시

### 4. Ad-hoc focused verification

시스템 verification detector가 canonical command로 인식하지 못한 경우가 있어 `/tmp/hermes-verify-*` 임시 스크립트로 focused verification을 수행했다.

검증 항목:

- Risk Map 월누적 제목
- X/Y/Bubble subtitle
- Bubble tooltip
- 음수 NPS 압축 로직
- compressed y축 tick
- top horizontal legend
- quadrant threshold line
- quadrant label
- Risk Map modebar disabled
- Top Bar 변수 정의 유지

결과: PASS.

## 남은 참고사항

- 현재 repo에는 오늘 작업 전후의 dashboard 개선 변경이 함께 존재한다.
- `README.md`, `scripts/build_data.py`, `src/nps_ops/insights.py`, `tests/test_metrics.py`, `reports/02_risk_scorecard_redesign.md`에도 변경분이 있다.
- 이 문서는 오늘 대화와 작업 흐름을 재개하기 위한 handoff note다.

## 다음에 이어서 볼 포인트

1. Risk Map zone label이 bubble과 겹치는지 실제 팀원 화면 기준으로 한 번 더 확인
2. `비판매성 응답 중앙값` 기준이 median이 맞는지, 혹은 정책 threshold로 바꾸는 것이 더 나은지 검토
3. `샘플/VOC 확인` 구간 매장의 실제 VOC 원문 drilldown 연결 여부 검토
4. Risk Map screenshot을 팀 공유용으로 export할 때 legend/title이 잘리는지 확인

## 추가 작업 — Risk Map 유형구분/Bar Chart 정렬

사용자 추가 요청에 따라 Risk Map 하단 구성을 한 번 더 정리했다.

### 1. Risk Score bar chart 정렬

Risk Map의 두 번째 horizontal bar chart는 색상/category 기준으로 재정렬했다.

- 정렬 기준: Risk Map legend 순서
  1. 즉시 개선형
  2. 비판매성 취약형
  3. 구조 개선형
  4. 판매성 취약형
  5. 우수 확산형
- 각 유형 내부는 Care Priority 내림차순
- `신세계 고창점`, `전북고창 본점`은 y축 하단부로 내려가도록 category array를 명시했다.

### 2. Risk Map 유형구분 box 재정의 및 위치 이동

기존 `종합진단 유형구분` box는 Risk Map에서 쓰는 5개 유형 기준으로 재정의했다.

- 기존 6개 유형 중 Risk Map에서 제외한 `회복 가능형` 등은 제거
- Risk Map 상단 legend와 동일한 순서로 box item 배치
- 색상도 bubble chart/bar chart와 동일한 mapping으로 통일
- box 위치는 dashboard 하단 진단 영역이 아니라 **Risk Map bubble chart 바로 아래, Risk Score bar chart 위**로 이동

### 3. 검증 포인트

- Risk Map top legend trace order와 `Risk Map 유형구분` box 순서 일치
- bar chart color trace order 일치
- y축 category array에서 `전북고창 본점`, `신세계 고창점`이 하단부에 배치됨
- `Risk Map 유형구분` box가 bubble chart와 bar chart 사이에 위치
