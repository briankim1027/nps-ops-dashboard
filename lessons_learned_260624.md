# Lessons Learned — NPS Ops Dashboard 작업 메모 (2026-06-24)

## 1. 오늘 작업 범위

### 구현한 기능
- **Action Sheet 현장형 개선**
  - 매장별 `이번 주 액션` 문구를 현장 전달용 1~2줄 형태로 정리.
  - 대리점 필터 추가.
  - 현재 보기 CSV 다운로드 추가.
  - TOP 10 CSV 다운로드 추가.
  - Action Sheet TOP 10만 보기 옵션 추가.

- **비판매성 NPS 전용 상세 페이지 강화**
  - 비판매성 집중관리 매장 탭 유지/강화.
  - 비판매성 업무유형별 Risk Top 탭 추가.
  - 매장별 비판매성 추이 탭 추가.
  - 판매성은 양호하지만 비판매성만 낮은 매장 분리 탭 추가.

- **UI 수정사항 반영**
  - `passive = 중립, detractor = 비추천` 용어 확인 blue box 삭제.
  - 기존 `종합진단 범례 / 우선순위점수 산정` popover 제거.
  - `우선순위점수 산정 방식`은 `매장 개입 우선순위` 테이블 하단 주석형 box로 상시 노출.
  - `종합진단 유형구분`은 `진단 유형 분포` 그래프 하단 box로 상시 노출.
  - `진단 유형 분포` 그래프 x축 title `diagnosis_type` 삭제.
  - `비추천/중립 Risk Top` 그래프 x축 title `매장` 삭제.
  - `비추천/중립 Risk Top` 그래프 범례를 `passives/detractors`에서 `중립/비추천`으로 한글화.
  - 비판매성 업무유형 Top의 `Risk비중` 표시 오류를 `Risk비중(%)` 숫자 컬럼 방식으로 수정.

## 2. 수정/생성된 주요 파일

- `app.py`
  - Streamlit UI, 필터, 탭, chart/table 표시 로직 수정.

- `src/nps_ops/insights.py`
  - 비판매성 업무유형 Top 산출.
  - 매장별 비판매성 추이 산출.
  - 판매성 양호·비판매성 취약 매장 분리 로직 추가.
  - Action Sheet 실행 문구 생성 로직 개선.

- `scripts/build_data.py`
  - 신규 산출물 parquet 저장.
  - Excel export sheet 추가.
  - Markdown summary 섹션 추가.

- 신규/갱신 산출물 예시
  - `data/processed/non_sales_business_type_top_전북_20260623.parquet`
  - `data/processed/store_non_sales_trend_전북_20260623.parquet`
  - `data/processed/sales_good_non_sales_weak_전북_20260623.parquet`
  - `data/processed/store_action_sheet_전북_20260623.parquet`
  - `data/exports/nps_ops_summary_전북_20260623.xlsx`
  - `data/exports/nps_ops_summary_전북_20260623.md`

## 3. 검증한 내용

### 문법 검증

```bash
. .venv/bin/activate
python -m py_compile app.py scripts/build_data.py src/nps_ops/*.py
```

### 데이터 빌드 검증

```bash
python scripts/build_data.py
```

확인 결과:

```text
BUILD_OK
raw_vs_store_promoters_delta = 0
raw_vs_store_passives_delta = 0
raw_vs_store_detractors_delta = 0
raw_vs_store_total_delta = 0
```

### Streamlit smoke test

```bash
streamlit run app.py --server.headless true --server.port 8503
curl -fsS http://localhost:8503/_stcore/health
```

확인 결과:

```text
ok
HEALTH_OK
```

브라우저 확인:
- 앱 정상 렌더링.
- 주요 탭 정상 표시.
- 비판매성 업무유형 Top 탭 클릭 시 JS/syntax error 없음.
- 브라우저 console error 없음.

## 4. 오늘 발견한 주의사항

### 4.1 `sales_nps_score`, `non_sales_nps_score` 스케일 혼재 이슈

`data/processed/store_priority_전북_20260623.parquet` 안의 `sales_nps_score`, `non_sales_nps_score` 컬럼은 현재 일부가 아니라 **전체적으로 -1~1 범위의 비율값**처럼 들어와 있다.

예:

```text
sales_nps_score range: -1.0 ~ 1.0
non_sales_nps_score range: 0.3333 ~ 1.0
```

즉, 일반 대시보드 표시 기준인 `-100~100` NPS 점수가 아니라, `NPS / 100` 형태에 가까운 값이다.

예시:

```text
1.000000  -> 100점
0.857143  -> 85.7143점
0.666667  -> 66.6667점
-1.000000 -> -100점
```

중요: 이 말은 **응답 raw 원장 한 줄 한 줄이 0~1이라는 뜻이 아니다.**

현재 확인된 것은:
- `store_priority` processed 파일의 매장별 집계 컬럼 `sales_nps_score`, `non_sales_nps_score`가 `-1~1` 스케일로 들어와 있다는 의미.
- 이 컬럼은 `src/nps_ops/parser.py`에서 엑셀의 매장/집계 시트 컬럼(`NPS.3`, `NPS.4` 또는 `종합NPS.1`, `종합NPS.2`)을 rename해서 들어오는 컬럼으로 보인다.
- 반면 응답 원장 기반으로 추천/중립/비추천 count를 다시 계산하는 `nps_score()` 함수는 `-100~100` 스케일을 반환한다.

따라서 같은 NPS라도 다음 두 출처가 섞일 수 있다.

1. 엑셀 집계 시트에서 온 NPS 컬럼
   - 현재 processed 기준 `-1~1` 비율 형태로 보임.

2. 응답 원장 count로 재계산한 NPS
   - `(추천 - 비추천) / 총응답 * 100`
   - `-100~100` 점수 형태.

오늘 임시 대응:
- `build_sales_good_non_sales_weak()`에서는 `abs(value) <= 1`이면 `* 100` 해서 표시/판단하도록 보정했다.

추가 개선 필요:
- parser 또는 store_priority 생성 단계에서 NPS 스케일을 한 번만 표준화하는 것이 더 안전하다.
- `metrics.diagnose_store()`에서도 `sales_nps_score`, `non_sales_nps_score`를 목표점수 87과 비교하므로, 현재처럼 `0~1` 값이면 진단 분류가 왜곡될 수 있다.
- 내일 개선 시 `normalize_nps_scale()` 같은 공통 함수를 만들어 모든 NPS 컬럼을 `-100~100` 기준으로 통일하는 것을 우선 검토한다.

## 5. 내일 이어서 보면 좋은 개선 후보

### 우선순위 높음
1. **NPS 스케일 표준화**
   - `sales_nps_score`, `non_sales_nps_score`, `nps_score`, `nps_recalc`의 스케일 일관성 점검.
   - parser/metrics/insights/app 중 어디서 표준화할지 결정.
   - 표준화 후 진단 유형, 비판매성 취약 분리, 목표Gap, 필요추천수 재검증.

2. **진단 유형 분류 재검증**
   - 현재 `metrics.diagnose_store()`가 `sales_nps_score`, `non_sales_nps_score`를 직접 `target_score=87`과 비교한다.
   - 원천 값이 0~1이면 `비판매성 취약형`, `판매성 취약형`, `구조 개선형` 분류가 과대/오분류될 수 있음.

3. **비판매성 양호/취약 구분 기준 정리**
   - 원천 집계 NPS 기준으로 볼지, 응답 count 재계산 기준으로 볼지 결정 필요.
   - 현재는 source display 값과 응답 재계산 값을 함께 표시해 혼선을 줄였지만, 최종 운영 기준은 하나로 정하는 것이 좋음.

### UI/사용성 개선
4. **범례/주석 box 폭과 위치 미세 조정**
   - 종합진단 유형구분 box가 진단 유형 분포 그래프와 시각적으로 같은 폭/높이 느낌이 나는지 확인.

5. **Action Sheet 문구 품질 개선**
   - `무의미/내용없음` VOC가 대표로 잡히는 경우 문구가 다소 약함.
   - VOC 원문이 실질 코칭 단서가 약할 때는 `동일 업무유형 반복 여부 확인` 중심으로 별도 문구 분기 필요.

6. **다운로드 파일명/컬럼 순서 정리**
   - 대리점 담당자에게 바로 전달할 CSV 기준으로 컬럼 순서를 더 현장형으로 조정 가능.

## 6. 앞으로 복잡한 코딩 작업 운영 원칙

Brian 요청 반영:

- 단순 UI 문구/위치 수정은 Hermes 단독 구현 + 실행 검증으로 진행.
- 데이터 산식, KPI, 진단 분류, 대시보드 구조 변경처럼 영향도가 큰 작업은 다음 방식으로 진행.

```text
1. Hermes가 구현 계획 작성
2. Claude Code reviewer 호출
3. reviewer 의견 반영 여부 판단
4. Hermes가 구현
5. py_compile / build / Streamlit smoke test
6. 필요 시 browser console 확인
7. 변경 내용과 리스크 보고
```

특히 다음 작업은 Claude Code review를 붙인다.
- NPS 스케일 표준화
- 진단 유형 분류 로직 변경
- 우선순위점수 산식 변경
- build_data pipeline 구조 변경
- 여러 파일을 동시에 수정하는 리팩토링

## 7. 오늘의 핵심 교훈

- UI 개선보다 **NPS 스케일 일관성**이 더 중요한 잠재 리스크다.
- raw response 기반 재계산 값과 엑셀 집계 시트 기반 값이 같은 스케일이라고 가정하면 안 된다.
- Streamlit chart/table 표시 오류는 브라우저 클릭 + console 확인까지 해야 안정적으로 잡힌다.
- 복잡한 데이터 로직은 단독 구현보다 reviewer agent를 붙여 산식/스케일/분류 기준을 교차검증하는 편이 안전하다.
