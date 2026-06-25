# Claude Review 01 Follow-up 정리

**작성일**: 2026-06-25  
**대상 리뷰**: `claude_review_01.md`  
**기준**: Brian/Hermes 2차 확인 + 실제 코드/원천 Excel/processed artifact 대조

---

## 1. 이미 확인한 것

### DATA-1. `promoter_flag` / `passive_flag` / `detractor_flag` 출처

- 최신 원천 Excel `AI만족도조사_리스트` 시트에 `추천`, `중립`, `비추천` 컬럼이 실제 존재함.
- `parser.py`에서 각각 아래와 같이 rename 중임.
  - `추천` → `promoter_flag`
  - `중립` → `passive_flag`
  - `비추천` → `detractor_flag`
- processed `response_fact_20260623.parquet` 기준 flag 컬럼 존재 확인.
- 확인 당시 합계:
  - 추천 6,108
  - 중립 250
  - 비추천 156

**판단**: 현재 운영 파일 기준 blocker 아님. 단, silent failure 방지를 위해 contract validation은 반영함.

### DATA-2. `NCSI` 컬럼명과 값 셋

- 최신 원천 Excel `AI만족도조사_리스트` 시트에 `NCSI` 컬럼 존재 확인.
- processed `response_fact_20260623.parquet` 기준 값 분포 확인.
  - `판매성`: 3,290건
  - `비판매성`: 3,224건

**판단**: 현재 운영 파일 기준 blocker 아님. 단, enum validation은 반영함.

### DATA-3. 주요 header offset

- 최신 원천 Excel 기준 아래 시트 컬럼 헤더가 현재 parser offset으로 정상 확인됨.
  - `AI만족도조사_리스트`
  - `매장별`
  - `대리점별`

**판단**: 현재 주요 사용 시트 기준 즉시 문제 없음. 단, 양식 변경 가능성은 운영 리스크로 남음.

### DATA-4. `build_nps_time_intelligence(report_date=None)` 기준일 해석

- Claude review에는 `report_date=None`이면 현재 날짜(`pd.Timestamp.now()`) 기준으로 계산한다고 되어 있었으나, 현재 코드 기준 사실과 다름.
- 실제 코드는 `report_date=None`일 때 `daily["trend_date"].max()`를 사용함.

**판단**: 현재 코드상 버그 아님. 다만 향후 명시성을 위해 `profile.report_date` 전달 방식으로 개선 여지는 있음.

### DATA-5. mapping join 현재 결과

- processed 기준 `response_fact_20260623.parquet`, `negative_feedback_20260623.parquet`의 `store_name` null rate가 0.0으로 확인됨.

**판단**: 현재 artifact는 정상. 단, 향후 파일/코드 포맷 drift 대응을 위해 매칭 실패율 warning은 반영함.

---

## 2. 이번 패치에 반영한 것

### BUG-1. `app.py` Risk chart의 `DataFrame.get(..., 0)` silent fallback 제거

**기존 문제**

```python
tmp["risk_count"] = tmp.get("passives", 0) + tmp.get("detractors", 0)
```

- 컬럼이 누락되어도 0으로 조용히 계산되어 대시보드가 정상처럼 보일 위험이 있었음.

**반영 내용**

- `passives`, `detractors` 필수 컬럼 존재 여부를 명시 확인.
- 누락 시 Streamlit error 후 stop.
- 존재 시 numeric 변환 후 `risk_count` 산출.

### BUG-3. `find_latest_file()` mtime 기준 선택 개선

**기존 문제**

- 파일 수정시각 기준으로 최신 파일을 고르면, 과거 파일을 열거나 복사한 뒤 오래된 파일이 최신으로 잡힐 수 있음.

**반영 내용**

- `extract_report_date()` 기반 report date를 1차 정렬 기준으로 변경.
- mtime은 같은 report date 내 tie-break로만 사용.
- 테스트 추가: mtime은 오래된 파일이 최신이어도 파일명/report date가 더 최신인 파일을 선택하는지 검증.

### SILENT-2. `apply_store_mapping()` join 실패율 warning 추가

**반영 내용**

- mapping merge 후 `map_store_name` 미매칭 row 비율 계산.
- 미매칭률이 `MAPPING_UNMATCHED_WARN_RATE` 초과 시 warning 출력.
- warning에는 미매칭 row 수/전체 row 수와 sample store_code 최대 10개 포함.

### DATA-1/DATA-2 후속. `validate_response_contract()` 추가

**반영 내용**

- `response_fact` 필수 컬럼 검사:
  - `promoter_flag`
  - `passive_flag`
  - `detractor_flag`
  - `NCSI`
- flag 값이 0/1 binary인지 검사.
- `추천+중립+비추천` one-hot 합계가 row별 1인지 검사.
- `NCSI` 값이 `판매성`/`비판매성` enum에 속하는지 검사.
- `비판매성` row가 없는 경우 warning.
- build 결과와 markdown summary에 `response_contract_warnings` 노출.
- 관련 unit test 추가.

### HARDCODE-1. Excel export Top N 상수화

**기존 문제**

- `.head(64)`, `.head(30)`, `.head(100)`이 build script에 직접 박혀 있었음.

**반영 내용**

- `config.py`에 상수 추가.
  - `EXPORT_TOP_N_STORES = 64`
  - `EXPORT_TOP_N_TYPES = 30`
  - `EXPORT_TOP_N_AUDIT = 100`
- Excel export에서 해당 상수 사용.
- markdown summary 해석 메모에 “Excel 요약 시트는 운영 검토용 Top N”임을 명시.

### HARDCODE-2. `MAPPING_FILE` config 이동

**반영 내용**

- `MAPPING_FILE`을 `scripts/build_data.py` 내부 상수에서 `src/nps_ops/config.py`로 이동.
- build script는 config에서 import하도록 정리.

### BUILD-1. mixed object 컬럼 parquet export 안정화

**발견 배경**

- `0624` 최신 원천 파일로 실제 build 검증 중 `comment_text` 컬럼에 문자열/숫자 object가 혼재되어 pyarrow export가 실패함.

**반영 내용**

- `parquet_safe()` / `write_parquet()` helper 추가.
- parquet 저장 전 object 컬럼을 nullable string으로 정규화.
- 기존 build artifact 생성 경로 전체에 적용.

---

## 3. 아직 남아 있는 것

### REMAIN-1. `REQUIRED_SHEETS`와 `HEADER_ROWS` 구조 정리

**상태**

- `REQUIRED_SHEETS`에는 `■팀별`, `일별트렌드`가 있으나 `HEADER_ROWS`에는 없음.
- 현재 `parse_workbook()`이 이 두 시트를 직접 파싱하지 않아 즉시 KeyError가 나는 상황은 아님.
- 하지만 “필수 시트”와 “파싱 대상 시트”가 섞여 있어 data contract 의미가 불명확함.

**권장 방향**

- `REQUIRED_SHEETS`를 다음처럼 분리.
  - `REQUIRED_INPUT_SHEETS`: build에 반드시 필요한 시트
  - `OPTIONAL_REFERENCE_SHEETS`: 존재하면 참고/검증 가능한 시트
  - `PARSED_SHEETS`: 실제 parser가 읽는 시트

**우선순위**: 중간

### REMAIN-2. header offset 자동 검증 강화

**상태**

- 현재 주요 시트는 최신 파일 기준 정상 확인됨.
- 다만 양식 변경 시 header row가 밀리면 parse 결과가 조용히 이상해질 수 있음.

**권장 방향**

- 각 파싱 함수별 expected source columns set을 두고, `_read_table()` 직후 최소 필수 컬럼 존재 여부를 검사.
- 누락 시 sheet name, header row, 실제 컬럼 sample을 포함해 명시 error/warning 출력.

**우선순위**: 중간

### REMAIN-3. `report_date` 명시 전달

**상태**

- 현재 `report_date=None`은 코드상 데이터의 마지막 `trend_date`를 사용하므로 즉시 버그는 아님.
- 다만 build/app 호출부에서 명시적으로 기준일을 넘기는 편이 운영 의도를 더 잘 드러냄.

**권장 방향**

- build 단계에서는 `profile.report_date`를 `build_nps_time_intelligence()`에 전달.
- app fallback에서는 priority artifact의 `report_date`를 파싱해 전달.

**우선순위**: 낮음~중간

### REMAIN-4. mapping master store_code 포맷 차이 확인

**상태**

- 이번 패치로 mapping 미매칭률 warning이 노출됨.
- `0624` build 검증 시 다음 warning 확인:
  - negative feedback: 313/407 rows 미매칭, 76.90%
  - response fact: 5,547/6,868 rows 미매칭, 80.77%
- 다만 build 검산 결과 raw vs store aggregate delta는 0이고, 원천 response/store 필드 자체가 존재해 즉시 산출 실패는 아님.

**권장 방향**

- mapping 파일의 `매장코드` 포맷과 원천 Excel의 `D...` prefix 코드 체계를 대조.
- `D` prefix 제거/유지, zero-padding, agency-store code alias 여부를 명세화한 뒤 `_norm_code()`를 보강.
- warning 기준도 “master correction 실패”와 “최종 store_name null”을 분리해 운영 메시지 과잉을 줄일지 검토.

**우선순위**: 중간

---

## 4. 나중에 반영할 것

### LATER-1. `store_code` 정규화 강화

**현재**

- `_norm_code()`는 공백 제거와 `.0` suffix 제거 중심.

**추후 개선**

- 실제 store_code 포맷 명세가 확인되면 zero-padding 차이도 처리.
- 단, 코드 체계에서 앞자리 0이 의미를 가질 가능성이 있으면 임의 제거는 위험하므로 명세 확인 후 반영.

### LATER-2. 원천 `추천지수`와 flag 일관성 검산

**현재**

- flag one-hot 검증은 반영함.

**추후 개선**

- `추천지수` 점수 기준과 `추천/중립/비추천` flag가 일치하는지 검산.
- 단, NPS 점수 분류 기준이 운영 Excel에서 이미 별도 로직으로 산정될 수 있으므로 공식 기준 확인 필요.

### LATER-3. `■팀별` / `일별트렌드` 직접 활용 여부 결정

**현재**

- 두 시트는 workbook profile에서 존재 여부만 확인하고 직접 파싱하지 않음.

**추후 개선 선택지**

1. 실제 운영 검산에 필요하면 parser 추가.
2. 사용하지 않을 시 optional/reference sheet로 내리고 required 의미 제거.

### LATER-4. dashboard/app smoke 자동화

**현재**

- pytest/build 중심 검증.

**추후 개선**

- Streamlit 실행 후 주요 탭/차트 렌더링 smoke check를 자동화하거나 수동 체크리스트화.
- Brian이 요구하는 “보이는 UI 검증” 기준을 release checklist에 포함.

---

## 5. 이번 패치 후 기대 효과

- 최신 raw 파일 선택 오류 가능성 감소.
- 원천 응답 원장 컬럼 drift가 조용히 0 집계로 이어지는 위험 감소.
- 매장 mapping 실패가 무음으로 지나가는 위험 감소.
- export Top N 정책이 코드와 문서에 명시되어 오해 가능성 감소.
- Claude review 지적사항을 blocker/반영/보류/추후 개선으로 구분해 다음 작업 우선순위가 명확해짐.
