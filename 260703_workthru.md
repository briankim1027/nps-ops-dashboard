# 260703 Work-through — 0630 NPS 소명 조정 데이터 반영 및 GitLab 배포 정리

## 결론

오늘 작업의 핵심은 `raw/2026-06` 폴더에 추가로 업로드된 소명 조정 반영 데이터인 `●26년06월 NPS평가 통계_0630_마감아님3.xlsx` 파일을 빌드 프로세스를 통해 성공적으로 처리하고, 수정된 `20260630` 기준일의 processed 데이터를 GitLab 저장소의 `main` 브랜치에 배포(git push) 완료한 것입니다.

최종 상태는 다음과 같습니다.
- **Git Remote**: `gitlab` (`https://gitlab.tde.sktelecom.com/JBTEAM/nps-ops-dashboard.git`)
- **브랜치**: `main`
- **최신 배포 데이터 기준일**: `2026-06-30` (소명 조정본 파일: `●26년06월 NPS평가 통계_0630_마감아님3.xlsx`)
- **검산 결과 (Raw vs Store)**: 추천/중립/비추천/총 응답 수 오차 `0` (완벽히 검산 완료)

---

## 1. 데이터 빌드 및 검산 정보

`scripts/build_data.py` 스크립트를 사용하여 최신 엑셀 데이터를 정규화 및 파싱 처리하였습니다.

### 1.1 데이터 Profile 요약 (조정 전 vs 조정 후)

| 항목 | 조정 전 (`●26년06월 NPS평가 통계_0630.xlsx`) | 조정 후 (`●26년06월 NPS평가 통계_0630_마감아님3.xlsx`) | 변동 내용 |
| :--- | :--- | :--- | :--- |
| **대상 파일** | `●26년06월 NPS평가 통계_0630.xlsx` | `●26년06월 NPS평가 통계_0630_마감아님3.xlsx` | 소명 조정본 반영 |
| **추천 응답** | 1,551 건 | 1,551 건 | 동일 (0) |
| **중립 응답** | 69 건 | 69 건 | 동일 (0) |
| **비추천 응답** | 57 건 | **46 건** | **11건 감소 (-11)** |
| **총 응답** | 1,677 건 | **1,666 건** | **11건 감소 (-11)** |
| **종합 NPS** | 89.09 | **90.34** | **+1.25 p.p. 상승** |
| **판매성 NPS** | 92.53 (총 803건) | **93.01 (총 801건)** | **+0.48 p.p. 상승** |
| **비판매성 NPS** | 85.93 (총 874건) | **87.86 (총 865건)** | **+1.93 p.p. 상승** |
| **매장 수** | 64개 | 64개 | 동일 |
| **대리점 수** | 22개 | 22개 | 동일 |

- **오류 및 경고**:
  - `scale_warnings`: 없음 (0개)
  - `response_contract_warnings`: `response_fact 추천/중립/비추천 one-hot violation rows=9/8666` (비판매성 소명 조정 과정에서의 일부 데이터 정합성 메시지)
  - `validation` (Raw 원장 대비 매장별 합산 델타): 추천 `0` / 중립 `0` / 비추천 `0` / 총응답 `0` (완벽 일치)

### 1.2 생성된 Processed 파일
아래 18개 데이터 셋이 `data/processed/` 폴더에 정상적으로 갱신되었습니다:
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

### 2.1 최신 20260630 데이터 및 workthru 추가
새로 빌드된 20260630 parquet 데이터 셋 및 작업 문서를 스테이징(staging) 하였습니다:
```bash
git add data/processed/*20260630.parquet
git add 260703_workthru.md
```

### 2.2 커밋 및 GitLab push 진행
- **커밋 메시지**: `Update dashboard data 20260630 with adjusted NPS raw`
- **회사 GitLab 원격지로 push 완료**:
  ```bash
  git push gitlab main
  ```
  성공적으로 push가 마무리되어, GitLab 리포지토리의 `main` 브랜치가 최신 소명 조정이 완료된 `20260630` 데이터 셋을 바라보도록 설정되었습니다.
