# nps-ops-dashboard 코드 리뷰

**리뷰 일자**: 2026-06-25
**리뷰 대상**: Git tracked 소스 파일 전체 (data/raw, data/processed, data/exports, .venv, .omc, pycache 제외)
**리뷰어**: Claude Sonnet 4.6

---

## 1. 데이터 없이도 확정 가능한 코드 이슈

### [BUG-1] `app.py` — `DataFrame.get()` 방어 코드의 오폭

```python
# 문제 코드
tmp["risk_count"] = tmp.get("passives", 0) + tmp.get("detractors", 0)
```

`DataFrame.get(key, default)` 는 컬럼이 없으면 default(scalar 0)를 반환한다. 두 컬럼이 모두 없으면 `0 + 0 = 0` 이 되어 조용히 틀린 값을 출력한다. `build_store_priority()` 가 항상 `risk_count` 컬럼을 추가하므로 이 방어 코드 자체가 불필요하며, 있어도 오동작하는 구조다.

**권장 수정**: `tmp["risk_count"]` 직접 참조. 없으면 명시적 예외 또는 `KeyError` 그대로 노출.

---

### [BUG-2] `REQUIRED_SHEETS`에 있지만 `HEADER_ROWS`에 없는 시트 2개

```python
# parser.py
REQUIRED_SHEETS = {
    "team": "■팀별",      # ← HEADER_ROWS에 없음
    "trend": "일별트렌드", # ← HEADER_ROWS에 없음
    ...
}
```

`_read_table(path, "■팀별", HEADER_ROWS["■팀별"])` 호출 시 `KeyError` 발생. 현재 이 시트들을 파싱하는 함수가 없다면 `REQUIRED_SHEETS`에서 제거해야 한다. 향후 파싱 예정이라면 `HEADER_ROWS`에 row offset을 추가해야 한다.

---

### [BUG-3] `find_latest_file()` — mtime 기반 파일 선택 불안정

```python
files = sorted(raw_dir.glob("**/*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
```

파일을 열거나 복사하면 mtime이 갱신되어 오래된 파일이 "최신"으로 선택된다. `extract_report_date()` 가 이미 파일명에서 날짜를 파싱하므로 filename date를 1차 정렬 기준으로, mtime은 tie-break로만 사용해야 한다.

---

### [HARDCODE-1] `.head(64)` 매장 수 상한 하드코딩

`build_data.py` Excel 내보내기에서 `store_priority.head(64)`, `non_sales_drilldown.head(64)`, `non_sales_business_type_top.head(30)` 가 하드코딩되어 있다. 매장이 64개를 초과하면 데이터가 조용히 잘린다.

**권장 수정**: config.py에 상수 선언 + 초과 시 경고 로그 출력.

---

### [HARDCODE-2] `MAPPING_FILE` 한글 파일명 고정 경로

```python
MAPPING_FILE = ROOT / "팀소속_대리점명_매장명_매칭.xlsx"
```

프로젝트 루트에 하드코딩된 한글 경로. 파일 이동/이름 변경 시 `FileNotFoundError`. config.py 상수로 이동 권장.

---

### [SILENT-1] `nps_scale_warnings()` 검사 범위 누락

`store_agg["nps_score"]` 만 검사하고 `response_fact` row-level 점수는 검사하지 않는다. 원본 Excel의 flag 컬럼이 잘못 코딩되어도 스케일 경고가 뜨지 않는다.

---

### [SILENT-2] `apply_store_mapping()` join 실패 시 무음 처리

`store_code_norm` 매칭 실패 행은 `store_name` 이 `NaN` 으로 통과한다. join 성공률 로그나 assertion 없음 (임계치 5% 이하 등 기준 필요).

---

## 2. 실제 데이터/요약 없이는 확정 불가한 이슈

### [DATA-1] ⚠️ 최우선 확인 — `promoter_flag` / `passive_flag` / `detractor_flag` 출처 불명

`parser.py` 의 `parse_response_fact()` 가 이 컬럼들을 명시적으로 파생하는 코드가 없다. "AI만족도조사_리스트" 시트에 이 컬럼이 사전 계산된 채 들어오는지, 아니면 `recommend_score` 에서 파생해야 하는지 반드시 확인 필요.

**만약 Excel에 없으면**: 모든 insights 함수가 0을 집계하고 에러도 발생하지 않는다. 대시보드가 정상처럼 보이지만 데이터는 전부 0.

---

### [DATA-2] ⚠️ 최우선 확인 — `NCSI` 컬럼명과 값 셋

```python
df[df["NCSI"].astype(str).str.strip().eq("비판매성")]  # 여러 곳에서 사용
```

실제 Excel 컬럼명이 `NCSI` 인지, 값이 정확히 `"판매성"` / `"비판매성"` 두 가지뿐인지 데이터 확인 필요. 컬럼명이 다르면 필터 결과가 0건으로 조용히 실패한다.

---

### [DATA-3] `HEADER_ROWS` offset 정확성

`매장별` row 10, `대리점별` row 9 등이 실제 Excel 템플릿과 일치하는지 육안 대조 필요. 보고서 양식이 버전업될 때 offset만 바뀌어도 헤더 아래 데이터 행 전체가 밀린다.

---

### [DATA-4] `build_nps_time_intelligence()` `report_date=None` 시 오해

기준일을 `None` 으로 넘기면 `pd.Timestamp.now()` 를 기준으로 Time Intelligence 계산. 과거 데이터 재처리 시 "오늘 기준"으로 전일/주간 비교가 틀어진다. 운영에서 `report_date` 를 항상 명시하는지 확인 필요.

---

### [DATA-5] `store_code` 정규화 범위

`_norm_code()` 가 `.0` suffix 만 제거한다. 앞쪽 0-padding 차이 (예: `"0012"` vs `"12"`) 가 있으면 join 실패. 실제 코드 포맷 확인 필요.

---

## 3. 추가로 필요한 data contract 항목

| 항목 | 필요 이유 |
|------|-----------|
| 각 시트별 컬럼 전체 목록 (한글명 + dtype + nullable 여부) | rename dict 누락 탐지, 헤더 오프셋 검증 |
| `promoter_flag` 파생 규칙 (점수 → 분류 기준) | 파서에 파생 로직 추가 여부 결정 |
| `NCSI` 컬럼 정확한 이름과 값 enum | 필터 신뢰성 보장 |
| 파일명 날짜 포맷 규칙 (정규식) | `extract_report_date()` 실패 시 대응 |
| 대리점/매장 코드 포맷 명세 | join 정규화 완전성 |
| `■팀별` / `일별트렌드` 시트 사용 여부 | dead code vs 미구현 판단 |
| 목표 점수 87.0 공식 KPI 출처 | 하드코딩 근거 문서화 |

---

## 4. 운영 배포 전 최소 검증 체크리스트

```
[ ] 1. python -m pytest tests/ 전체 통과
[ ] 2. python scripts/build_data.py 실행 후 "BUILD_OK" 출력 확인
[ ] 3. profile_workbook() 결과 missing_required_sheets == [] 확인
[ ] 4. response_fact에 promoter_flag / passive_flag / detractor_flag 컬럼 존재 확인
[ ] 5. response_fact["NCSI"].value_counts() 에 "비판매성" 레코드 존재 확인
[ ] 6. apply_store_mapping() 후 store_name null 비율 로그 확인 (5% 이하 권장)
[ ] 7. nps_scale_warnings() 결과 빈 dict 확인 (스케일 이슈 없음)
[ ] 8. find_latest_file() 출력 파일명 수동 확인 (날짜 맞는 파일인지)
[ ] 9. store_priority 총 행수 vs head(64) 비교 — 초과 시 경고 로그 확인
[ ] 10. streamlit run app.py 실행 후 모든 탭 오류 없이 렌더링 확인
[ ] 11. build_nps_time_intelligence() 호출 시 report_date 명시적 전달 여부 확인
```

---

## 우선순위 요약

| 우선순위 | 이슈 | 조치 |
|---------|------|------|
| 즉시 수정 | BUG-2: HEADER_ROWS 누락 시트 | REQUIRED_SHEETS 정리 또는 HEADER_ROWS 추가 |
| 즉시 수정 | BUG-3: mtime 파일 선택 | filename date 우선 정렬 |
| 즉시 수정 | BUG-1: app.py get() | 직접 컬럼 참조로 교체 |
| 배포 전 필수 | DATA-1: flag 컬럼 출처 | Excel 실제 컬럼 확인 |
| 배포 전 필수 | DATA-2: NCSI 컬럼명 | 실제 데이터 확인 |
| 운영 안정성 | HARDCODE-1: head(64) | 상수화 + 초과 경고 |
| 운영 안정성 | SILENT-2: join 성공률 | 로그 추가 |
