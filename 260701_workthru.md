# 260701 Work-through — 0630 새 데이터 반영 및 GitLab 배포 정리

## 결론

오늘 작업의 핵심은 `raw/2026-06` 폴더에 업로드된 `●26년06월 NPS평가 통계_0630.xlsx` 파일을 빌드 프로세스를 통해 성공적으로 처리하고, 생성된 `20260630` 기준일의 processed 데이터를 GitLab 저장소의 `main` 브랜치에 배포(git push) 완료한 것입니다.

최종 상태는 다음과 같습니다.
- **Git Remote**: `gitlab` (`https://gitlab.tde.sktelecom.com/JBTEAM/nps-ops-dashboard.git`)
- **브랜치**: `main`
- **최신 배포 데이터 기준일**: `2026-06-30` (Excel 파일: `●26년06월 NPS평가 통계_0630.xlsx`)
- **검산 결과 (Raw vs Store)**: 추천/중립/비추천/총 응답 수 오차 `0` (완벽히 검산 완료)

---

## 1. 데이터 빌드 및 검산 정보

`scripts/run_build.sh` 스크립트를 사용하여 최신 엑셀 데이터를 정규화 및 파싱 처리하였습니다.

### 1.1 데이터 Profile 요약
- **대상 파일**: `data/raw/2026-06/●26년06월 NPS평가 통계_0630.xlsx`
- **추출된 기준일**: `2026-06-30`
- **전북팀 Summary**:
  - 매장 수: `64개` | 대리점 수: `22개`
  - 추천 / 중립 / 비추천 / 총 응답: `1,551` / `69` / `57` / `1,677` 건
  - **종합 NPS**: `89.09`
  - **판매성 NPS**: `92.53` (총 803건)
  - **비판매성 NPS**: `85.93` (총 874건)
- **오류 및 경고**:
  - `scale_warnings`: 없음 (0개)
  - `response_contract_warnings`: 없음 (0개)
  - `validation` (Raw 원장 대비 매장별 합산 델타): 추천 `0` / 중립 `0` / 비추천 `0` / 총응답 `0` (완벽 일치)

### 1.2 생성된 Processed 파일
아래 18개 데이터 셋이 `data/processed/` 폴더에 정상적으로 생성되었습니다:
- `response_fact_20260630.parquet`
- `store_agg_20260630.parquet`
- `agency_agg_20260630.parquet`
- `negative_feedback_20260630.parquet`
- `crew_agg_20260630.parquet`
- `store_crew_agg_20260630.parquet`
- `store_priority_전북_20260630.parquet`
- `non_sales_drilldown_전북_20260630.parquet`
- `non_sales_business_type_top_전북_20260630.parquet`
- `daily_nps_trend_전북_20260630.parquet`
- `nps_time_intelligence_전북_20260630.parquet`
- `store_non_sales_trend_전북_20260630.parquet`
- `store_daily_heatmap_전북_20260630.parquet`
- `weekday_time_hotspots_전북_20260630.parquet`
- `sales_good_non_sales_weak_전북_20260630.parquet`
- `store_action_sheet_전북_20260630.parquet`
- `nps_source_recalc_diff_전북_20260630.parquet`
- `sample_warning_전북_20260630.parquet`

---

## 2. Git 버전 관리 및 push 내역

배포 용량 최적화 및 Clean 저장소 관리를 위해 아래 규칙에 맞춰 Git을 제어했습니다.

### 2.1 기존 20260629 데이터 캐시 제거
저장소에 누적되어 있던 이전 `20260629` processed 파일 세트를 Git 추적에서 제외하였습니다:
```bash
git rm --cached data/processed/*20260629.parquet
```

### 2.2 최신 20260630 데이터 추가
새로 빌드된 최신 parquet 데이터 셋을 강제 추가(force add)하였습니다:
```bash
git add -f data/processed/*20260630.parquet
```

### 2.3 커밋 및 GitLab push 진행
- **커밋 메시지**: `Update dashboard data 20260630`
- **회사 GitLab 원격지로 push 완료**:
  ```bash
  git push gitlab main
  ```
  성공적으로 push가 마무리되어, GitLab 리포지토리의 `main` 브랜치가 최신 `20260630` 데이터 셋을 바라보도록 설정되었습니다.

---

## 3. 향후 반영 절차 리마인드
다음 번에 새 데이터(예: 0701)가 업로드되면 다음과 같이 수동 처리하시면 됩니다.

1. **엑셀 파일 업로드**: `data/raw/2026-07/`에 새 파일 저장 (예: `●26년07월 NPS평가 통계_0701.xlsx`)
2. **데이터 빌드**:
   ```bash
   bash scripts/run_build.sh
   ```
3. **이전 데이터 캐시 정리 및 신규 데이터 추가**:
   ```bash
   git rm --cached data/processed/*20260630.parquet
   git add -f data/processed/*20260701.parquet
   ```
4. **Git 커밋 및 push**:
   ```bash
   git commit -m "Update dashboard data 20260701"
   git push gitlab main
   ```
5. **Playground 배포 확인**: IDCube Playground 관리페이지에서 Webhook 빌드가 성공했는지 확인(필요시 manual build trigger).
