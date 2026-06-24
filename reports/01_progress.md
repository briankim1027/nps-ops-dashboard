# NPS 운영 Dashboard — 작업 로그

## 2026-06-24

- 신규 프로젝트 `/home/mysktelecom/workplace/nps-ops-dashboard` 생성
- 6월 실운영 Excel 구조 기준 parser 방향 확정
- raw 파일 위치: `data/raw/2026-06/`
- `AI만족도조사_리스트`를 Raw Fact 원장으로 사용
- `매장별`, `대리점별`, `응답_비추천`, `T크루별`, `T매장크루별` 파서 초안 작성
- `scripts/build_data.py`로 parquet/Excel/Markdown 산출물 생성 예정
