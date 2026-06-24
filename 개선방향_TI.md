# NPS 운영 Dashboard 개선방향_TI

## 0. 결론

다음 개선의 1순위는 **NPS 스케일 표준화와 진단 분류 재검증**이다. UI 추가보다 먼저, `0~1` 비율값과 `-100~100` 점수값이 섞이는 구조를 정리해야 매장 진단, 비판매성 취약 매장 분리, 목표 Gap, 필요추천수, Action Sheet가 같은 기준으로 움직인다.

현재 대시보드는 현장 운영 MVP로는 동작하지만, `store_priority`의 일부 NPS 원천 컬럼이 `0~1` 스케일로 들어오고 `nps_recalc`는 `-100~100` 스케일로 계산된다. 이 상태에서 `target_score=87`과 직접 비교하면 일부 진단/분류가 왜곡될 수 있다.

---

## 1. 현재까지 구현된 맥락

### 1.1 프로젝트 목적

- 6월 이후 실운영 Excel `●26년06월 NPS평가 통계_*.xlsx`를 기준으로 전북팀 NPS 운영 Dashboard를 구축한다.
- 단순 점수판이 아니라 **현장 코칭 우선순위 운영판**으로 설계한다.
- 종합 NPS, 판매성 NPS, 비판매성 NPS를 분리해 본다.
- 중립/비추천 절대량, 목표까지 필요 추천수, 샘플 수, VOC 유형을 함께 보고 매장별 action으로 연결한다.

### 1.2 데이터 기준

- 원장 Fact: `AI만족도조사_리스트`
- 집계/검산 View: `매장별`, `대리점별`, `팀별`, `T크루별`, `T매장크루별`, `응답_비추천`, `일별트렌드`
- 매장/대리점 보정: `팀소속_대리점명_매장명_매칭.xlsx`를 store_code 기준으로 적용
- 내부 VOC/매장 데이터는 민감정보이므로 외부 AI 전송 없이 로컬 rule 기반으로 분류

### 1.3 현재 구현 파일

- `src/nps_ops/parser.py`
  - 실운영 Excel 구조 파싱
  - `AI만족도조사_리스트`, `매장별`, `대리점별`, `응답_비추천`, `T크루별`, `T매장크루별` 처리
- `src/nps_ops/metrics.py`
  - `nps_score`, `required_promoters_to_target`, `sample_grade`
  - `diagnose_store`, `build_store_priority`, `summarize_team_from_response`
- `src/nps_ops/insights.py`
  - VOC rule 분류
  - 비판매성 drill-down
  - 비판매성 업무유형 Top
  - 매장별 비판매성 추이
  - 판매성 양호·비판매성 취약 매장 분리
  - 매장별 Action Sheet 문구 생성
- `scripts/build_data.py`
  - 최신 raw Excel 파싱
  - parquet/Excel/Markdown 산출물 생성
  - raw 원장 vs 매장별 집계 검산
- `app.py`
  - Streamlit Dashboard
  - 종합/판매성/비판매성 매장 우선순위
  - 비판매성 전용 상세 탭
  - Action Sheet 및 CSV 다운로드

---

## 2. 검증된 현재 상태

### 2.1 빌드/렌더링 검증 이력

이전 작업에서 다음 검증은 통과했다.

```bash
. .venv/bin/activate
python -m py_compile app.py scripts/build_data.py src/nps_ops/*.py
python scripts/build_data.py
streamlit run app.py --server.headless true --server.port 8503
curl -fsS http://localhost:8503/_stcore/health
```

확인 결과:

```text
BUILD_OK
raw_vs_store_promoters_delta = 0
raw_vs_store_passives_delta = 0
raw_vs_store_detractors_delta = 0
raw_vs_store_total_delta = 0
HEALTH_OK
```

### 2.2 오늘 확인한 스케일 증거

`data/processed/store_priority_전북_20260623.parquet` 기준:

```text
nps_score              min 0.3333 / max 1.0      # Excel 집계 시트 원천값으로 보이며 0~1 스케일
nps_recalc             min 33.3333 / max 100.0   # raw count 재계산값, -100~100 스케일
sales_nps_score        min -1.0 / max 1.0        # 0~1 또는 -1~1 스케일
non_sales_nps_score    min 0.3333 / max 1.0      # 0~1 스케일
```

핵심은 `nps_score`, `sales_nps_score`, `non_sales_nps_score`와 `nps_recalc`가 같은 의미의 NPS처럼 보이지만 스케일이 다르다는 점이다.

---

## 3. 개선방향: 내가 제안하는 순서

### Step 1. NPS 스케일 표준화 기준 확정

**방향:** 내부 계산과 화면 표시 기준을 모두 `-100~100` 점수로 통일한다.

권장 원칙:

1. 원천 Excel에서 들어온 NPS 컬럼이 `abs(value) <= 1`이면 `value * 100`으로 표준화한다.
2. 원장 count에서 재계산 가능한 항목은 `(추천 - 비추천) / 총응답 * 100`을 기준값으로 둔다.
3. 원천 NPS와 재계산 NPS가 모두 존재하면 둘을 분리한다.
   - `*_nps_score_raw`: Excel 원천값
   - `*_nps_score`: 표준화된 `-100~100` 점수
   - `*_nps_recalc`: count 기반 재계산값
4. 목표점수 `target_score=87`과 비교되는 모든 값은 반드시 표준화 후 비교한다.

**권장 구현 위치:** `metrics.py`에 공통 함수 추가 후, `build_store_priority()` 진입 전에 표준화한다.

예상 함수:

```python
def normalize_nps_scale(value):
    # scalar/Series 모두 처리 가능하게 설계
    # abs(value) <= 1이면 *100, 그 외는 그대로
    # NaN 유지
```

또는 Series 중심으로:

```python
def normalize_nps_series(s: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(s, errors="coerce")
    return numeric.where(numeric.abs() > 1, numeric * 100)
```

---

### Step 2. 진단 유형 분류 재검증

현재 `metrics.diagnose_store()`는 다음 컬럼을 `target_score=87`과 직접 비교한다.

- `sales_nps_score`
- `non_sales_nps_score`

이 값이 `0~1`이면 대부분 목표 미달로 판단되거나 분류 순서에 따라 의도와 다른 결과가 나올 수 있다.

개선 방향:

1. `diagnose_store()`가 받는 row 안의 `sales_nps_score`, `non_sales_nps_score`는 이미 `-100~100` 기준이어야 한다.
2. 함수 내부에서 한 번 더 방어적으로 normalize할지 결정한다.
3. 분류 순서를 재검토한다.
   - `샘플 착시형`
   - `우수 확산형`
   - `즉시 개선형`
   - `비판매성 취약형`
   - `판매성 취약형`
   - `구조 개선형`
   - `회복 가능형`
   - `관찰/유지형`
4. 특히 `회복 가능형`이 비판매성/판매성 취약형보다 먼저 잡히는 현재 순서가 현장 목적에 맞는지 검토한다.

내 의견:

- 현장 운영 관점에서는 `즉시 개선형`과 `샘플 착시형`은 앞에 두는 것이 맞다.
- 다만 `회복 가능형`이 너무 앞에 있으면 판매성/비판매성 축의 구조적 취약 신호를 가릴 수 있다.
- 그래서 표준화 후 실제 분포를 보고, `비판매성 취약형`과 `판매성 취약형`을 `회복 가능형`보다 앞에 둘지 검토하는 것이 좋다.

---

### Step 3. 비판매성 양호/취약 구분 기준 정리

현재 `build_sales_good_non_sales_weak()`에서는 임시로 `abs(value) <= 1`이면 `*100` 보정해 사용한다.

개선 방향:

1. 이 함수 안의 임시 보정을 공통 normalize 함수로 대체한다.
2. `sales_good_non_sales_weak`의 판정 기준을 명확히 한다.
   - 판매성 기준: `sales_nps_score >= target_score`
   - 비판매성 기준: `non_sales_nps_score < target_score`
   - 단, count 재계산값 `axis_nps`와 원천 표준화값이 다를 경우 어떤 값을 운영 기준으로 삼을지 결정
3. 화면에서는 혼선 방지를 위해 다음처럼 표기한다.
   - `판매성 NPS`
   - `비판매성 NPS`
   - 필요 시 `비판매성 NPS(응답재계산)`은 보조 컬럼으로 유지

내 의견:

- 운영 기준은 count 기반 재계산값을 우선하는 것이 가장 안전하다.
- Excel 집계 시트 원천값은 검산/참조로 남기되, Dashboard 핵심 판단은 추천/중립/비추천 count에서 재계산한 값을 쓰는 편이 납득시키기 쉽다.

---

### Step 4. 전체 산출물 재생성 및 분포 비교

표준화 후 반드시 아래를 비교한다.

1. 진단 유형 count 변화
2. `비판매성 취약형`, `판매성 취약형`, `구조 개선형`, `회복 가능형` 매장 목록 변화
3. 매장 우선순위 Top 10 변화
4. `sales_good_non_sales_weak` 목록 변화
5. Action Sheet Top 10 변화
6. raw 원장 vs 매장별 집계 검산 delta 유지 여부

검증 명령:

```bash
. .venv/bin/activate
python -m py_compile app.py scripts/build_data.py src/nps_ops/*.py
python scripts/build_data.py
streamlit run app.py --server.headless true --server.port 8503
curl -fsS http://localhost:8503/_stcore/health
```

가능하면 표준화 전/후 요약 비교 스크립트를 한 번 돌린다.

---

### Step 5. UI/Action Sheet 미세 개선

스케일/진단 안정화 후에 진행한다.

우선순위:

1. `Action Sheet`에서 `무의미/내용없음` VOC가 대표 cue로 잡힐 때 문구를 더 현장형으로 개선
2. 다운로드 CSV 컬럼 순서 정리
3. 범례/주석 box 폭과 위치 미세 조정
4. 대리점 담당자 전달용 export sheet 별도 구성

---

## 4. Claude Code reviewer에게 맡길 검토 항목

Claude에게는 구현을 바로 맡기기보다, 우선 reviewer로 다음을 보게 한다.

### 4.1 반드시 검토할 파일

- `src/nps_ops/metrics.py`
- `src/nps_ops/insights.py`
- `scripts/build_data.py`
- `app.py`
- `src/nps_ops/parser.py`
- `lessons_learned_260624.md`
- `README.md`
- `reports/00_design_direction.md`

### 4.2 Claude 검토 질문

1. NPS 스케일 표준화 함수는 어디에 두는 것이 가장 안전한가?
2. 표준화는 parser 단계, metrics 단계, build pipeline 단계 중 어디서 적용해야 부작용이 적은가?
3. `diagnose_store()`의 분류 순서는 현장 운영 목적에 맞는가?
4. `sales_nps_score`, `non_sales_nps_score`, `nps_recalc`, `axis_nps` 중 Dashboard 판단 기준으로 무엇을 써야 하는가?
5. 임시 보정이 들어간 `build_sales_good_non_sales_weak()`를 어떻게 정리해야 하는가?
6. 표준화 전/후 검증 시 어떤 regression check를 추가해야 하는가?
7. 현재 코드에서 스케일 혼재 외에 데이터 품질/분류 왜곡 가능성이 있는 부분은 무엇인가?

### 4.3 Claude에게 요구할 출력 형식

- 결론: 구현 전제/방향
- 위험도 높은 이슈 Top 5
- 권장 구현 순서
- 파일별 수정 제안
- 추가해야 할 검증/테스트
- 구현하지 말아야 할 것 또는 보류할 것

---

## 5. 내 권장안

나는 다음 방식으로 진행하는 것이 가장 안전하다고 본다.

1. Claude reviewer 호출로 산식/분류 리스크를 먼저 교차검증한다.
2. Hermes가 Claude 의견을 반영해 구현 범위를 확정한다.
3. 공통 NPS normalize 함수를 추가한다.
4. `build_store_priority()`에서 표준화된 NPS 컬럼을 보장한다.
5. `diagnose_store()`와 `build_sales_good_non_sales_weak()`를 표준화 기준에 맞춘다.
6. build 재실행 후 전/후 분포를 비교한다.
7. Streamlit smoke test와 브라우저 확인까지 한다.

핵심은 **예쁜 화면을 더 얹기 전에, 현장 판단 기준이 흔들리지 않게 만드는 것**이다. 이 기준만 정리되면 이후 대리점/매장 단위 Action Sheet, 비판매성 코칭, 팀 보고용 요약이 훨씬 안정적으로 확장된다.
