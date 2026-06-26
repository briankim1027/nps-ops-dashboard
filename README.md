# 전북팀 NPS 운영 Dashboard

6월 이후 업로드되는 `●26년06월 NPS평가 통계_*.xlsx` 형태의 파일을 기준 데이터 구조로 사용하는 신규 NPS 운영 Dashboard 프로젝트입니다.

## 기본 원칙

- 기존 `NPS_v1.xlsx` 샘플 구조는 legacy/reference로만 취급합니다.
- 6월 실운영 Excel 구조를 기준으로 parser, 적재, dashboard를 새로 설계합니다.
- `AI만족도조사_리스트`를 설문 응답 원장 Fact로 보고, `매장별`, `대리점별`, `팀별`, `T크루별`, `응답_비추천`, `일별트렌드`는 집계/검산/운영 View로 사용합니다.
- 회사/매장/직원/고객 관련 데이터는 민감정보로 취급하고 로컬에서 처리합니다.

## 폴더 구조

```text
data/
  raw/
    2026-06/        # Brian이 6월 NPS Excel 파일을 넣는 위치
  processed/        # 파싱/정규화 결과 parquet/sqlite 등
  exports/          # 분석 결과/리포트/엑셀 산출물
src/
  nps_ops/          # parser, model, metrics, dashboard logic
notebooks/          # 임시 탐색/검산용
reports/            # 설계/분석 메모
scripts/            # 실행 스크립트
```

## 파일 업로드 위치

6월 파일은 우선 아래 경로에 넣으면 됩니다.

```text
/home/brian/workplace/nps-ops-dashboard/data/raw/2026-06/
```

예시:

```text
/home/brian/workplace/nps-ops-dashboard/data/raw/2026-06/●26년06월 NPS평가 통계_0622.xlsx
```

## 실행 방법

Brian의 WSL 기본 shell에는 `python` 명령이 없을 수 있으므로, 프로젝트 전용 `.venv`를 사용합니다.

최초 1회:

```bash
cd /home/brian/workplace/nps-ops-dashboard
bash scripts/setup_env.sh
```

데이터 재생성:

```bash
bash scripts/run_build.sh
```

Dashboard 실행:

```bash
bash scripts/run_dashboard.sh
```

직접 실행하려면 아래처럼 `.venv`의 Python을 사용합니다.

```bash
cd /home/brian/workplace/nps-ops-dashboard
. .venv/bin/activate
python scripts/build_data.py
python -m streamlit run app.py --server.headless true --server.port 8502
```

브라우저 주소:

```text
http://localhost:8502
```

## MVP 개발 순서

1. 6월 Excel 구조 profile 생성
2. 신규 parser 작성
3. Raw Fact 적재 구조 정의
4. 전북팀 64개 매장 기준 KPI 검산
5. Streamlit 운영 Dashboard MVP 구현
6. VOC/중립·비추천 코칭 View 확장
7. 일비용/TAC+/MSC3/성장매트릭스 통합 View 확장
