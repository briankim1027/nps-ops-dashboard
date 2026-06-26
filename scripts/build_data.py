from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nps_ops.config import (
    DEFAULT_TARGET_SCORE,
    DEFAULT_TEAM,
    EXPORT_DIR,
    EXPORT_TOP_N_AUDIT,
    EXPORT_TOP_N_STORES,
    EXPORT_TOP_N_TYPES,
    MAPPING_FILE,
    MAPPING_UNMATCHED_WARN_RATE,
    PROCESSED_DIR,
    RAW_DIR,
)
from nps_ops.insights import (
    add_voc_classification,
    build_daily_nps_trend,
    build_non_sales_business_type_top,
    build_non_sales_drilldown,
    build_nps_source_recalc_diff,
    build_nps_time_intelligence,
    build_sample_warning,
    build_sales_good_non_sales_weak,
    build_store_action_sheet,
    build_store_daily_heatmap,
    build_store_non_sales_trend,
    build_weekday_time_hotspots,
)
from nps_ops.metrics import build_store_priority, summarize_team_from_response
from nps_ops.parser import extract_report_date, parse_workbook, profile_workbook


def find_latest_file(raw_dir: Path = RAW_DIR) -> Path:
    files = [p for p in raw_dir.glob("**/*.xlsx") if not p.name.startswith("~$")]
    if not files:
        raise FileNotFoundError(f"No .xlsx files found under {raw_dir}")
    return sorted(files, key=lambda p: (extract_report_date(p) or pd.Timestamp.min.date(), p.stat().st_mtime), reverse=True)[0]


def _norm_code(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True)


def load_store_mapping(path: Path = MAPPING_FILE) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    mapping = pd.read_excel(path)
    required = ["팀명", "대리점코드", "대리점명", "매장코드", "매장명"]
    missing = [c for c in required if c not in mapping.columns]
    if missing:
        raise ValueError(f"Mapping file missing columns: {missing}")
    mapping = mapping[required].copy()
    mapping.columns = ["map_team_name", "map_agency_code", "map_agency_name", "map_store_code", "map_store_name"]
    mapping["store_code_norm"] = _norm_code(mapping["map_store_code"])
    mapping = mapping.drop_duplicates("store_code_norm", keep="first")
    return mapping


def apply_store_mapping(df: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    """Correct team/agency/store labels using Brian's store master mapping.

    The live `응답_비추천` sheet contains a lookup block whose rows do not align with
    the VOC rows, so agency/store fields from that block must not be trusted. The
    store code is reliable; use it to rehydrate team-agency-store labels.
    """
    if df.empty or mapping.empty or "store_code" not in df.columns:
        return df
    out = df.copy()
    out["store_code_norm"] = _norm_code(out["store_code"])
    out = out.merge(mapping, on="store_code_norm", how="left")
    unmatched = out["map_store_name"].isna() & out["store_code"].notna()
    unmatched_rate = float(unmatched.mean()) if len(out) else 0.0
    if unmatched_rate > MAPPING_UNMATCHED_WARN_RATE:
        sample_codes = out.loc[unmatched, "store_code"].astype(str).drop_duplicates().head(10).tolist()
        print(
            f"WARNING mapping_unmatched_rate={unmatched_rate:.2%} "
            f"rows={int(unmatched.sum())}/{len(out)} sample_store_codes={sample_codes}"
        )
    for src, dst in [
        ("map_team_name", "team_name"),
        ("map_agency_code", "agency_code"),
        ("map_agency_name", "agency_name"),
        ("map_store_name", "store_name"),
    ]:
        if src in out.columns:
            if dst not in out.columns:
                out[dst] = pd.NA
            out[dst] = out[src].combine_first(out[dst])
    drop_cols = [c for c in ["store_code_norm", "map_team_name", "map_agency_code", "map_agency_name", "map_store_code", "map_store_name"] if c in out.columns]
    return out.drop(columns=drop_cols)


def fmt_optional_score(value: object) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{float(value):.2f}"


def parquet_safe(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce mixed object columns to nullable strings before pyarrow export."""
    out = df.copy()
    for col in [c for c in out.columns if out[c].dtype == "object"]:
        out[col] = out[col].map(lambda v: pd.NA if pd.isna(v) else str(v))
    return out


def write_parquet(df: pd.DataFrame, path: Path) -> None:
    parquet_safe(df).to_parquet(path, index=False)


def nps_scale_warnings(df: pd.DataFrame, cols: list[str]) -> list[str]:
    warnings: list[str] = []
    for col in cols:
        if col not in df.columns:
            continue
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        if s.empty:
            continue
        max_abs = s.abs().max()
        nonzero = s[s.abs() > 0]
        if max_abs <= 1 and not nonzero.empty:
            warnings.append(f"{col} still appears to be entirely 0~1 scale after normalization")
        if (~s.between(-100, 100)).any():
            warnings.append(f"{col} has values outside -100~100 after normalization")
    return warnings


def validate_response_contract(response_fact: pd.DataFrame) -> list[str]:
    """Return warnings for response-level fields that can silently break insights."""
    warnings: list[str] = []
    required = ["promoter_flag", "passive_flag", "detractor_flag", "NCSI"]
    missing = [c for c in required if c not in response_fact.columns]
    if missing:
        return [f"response_fact missing required columns: {missing}"]

    flags = response_fact[["promoter_flag", "passive_flag", "detractor_flag"]].apply(pd.to_numeric, errors="coerce").fillna(0)
    invalid_flag_values = flags[~flags.isin([0, 1]).all(axis=1)]
    if not invalid_flag_values.empty:
        warnings.append(f"response_fact flag columns contain non-binary values: rows={len(invalid_flag_values)}")

    one_hot = flags.sum(axis=1)
    invalid_one_hot = one_hot.ne(1)
    if invalid_one_hot.any():
        warnings.append(f"response_fact 추천/중립/비추천 one-hot violation rows={int(invalid_one_hot.sum())}/{len(response_fact)}")

    ncsi = response_fact["NCSI"].astype(str).str.strip()
    allowed_ncsi = {"판매성", "비판매성"}
    unexpected_ncsi = sorted([v for v in ncsi.dropna().unique().tolist() if v not in allowed_ncsi])
    if unexpected_ncsi:
        warnings.append(f"response_fact NCSI unexpected values: {unexpected_ncsi[:20]}")
    if not ncsi.eq("비판매성").any():
        warnings.append("response_fact NCSI has no 비판매성 rows")
    return warnings


def build(path: Path, team: str = DEFAULT_TEAM, target_score: float = DEFAULT_TARGET_SCORE) -> dict[str, object]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    profile = profile_workbook(path)
    parsed = parse_workbook(path)
    mapping = load_store_mapping()
    if not mapping.empty:
        # Apply to VOC and response-level tables where a reliable store code exists.
        parsed["negative_feedback"] = apply_store_mapping(parsed["negative_feedback"], mapping)
        parsed["response_fact"] = apply_store_mapping(parsed["response_fact"], mapping)

    # Main derived tables
    team_summary = summarize_team_from_response(parsed["response_fact"], team=team)
    store_priority = build_store_priority(parsed["store_agg"], team=team, target_score=target_score)
    scale_warnings = nps_scale_warnings(store_priority, ["nps_score", "sales_nps_score", "non_sales_nps_score", "prev_nps_score", "hq_nps_score"])
    response_contract_warnings = validate_response_contract(parsed["response_fact"])
    parsed["negative_feedback"] = add_voc_classification(parsed["negative_feedback"])
    non_sales_drilldown = build_non_sales_drilldown(store_priority, target_score=target_score)
    non_sales_business_type_top = build_non_sales_business_type_top(parsed["response_fact"], team=team)
    daily_nps_trend = build_daily_nps_trend(parsed["response_fact"], team=team)
    nps_time_intelligence = build_nps_time_intelligence(parsed["response_fact"], team=team, target_score=target_score, report_date=None)
    store_non_sales_trend = build_store_non_sales_trend(parsed["response_fact"], team=team)
    store_daily_heatmap = build_store_daily_heatmap(parsed["response_fact"], team=team, axis="비판매성")
    weekday_time_hotspots = build_weekday_time_hotspots(parsed["response_fact"], team=team, axis="비판매성")
    sales_good_non_sales_weak = build_sales_good_non_sales_weak(store_priority, target_score=target_score)
    nps_source_recalc_diff = build_nps_source_recalc_diff(store_priority)
    sample_warning = build_sample_warning(store_priority, target_score=target_score)
    action_sheet = build_store_action_sheet(
        store_priority,
        parsed["negative_feedback"][parsed["negative_feedback"].get("team_name", "").astype(str).str.strip().eq(team)],
        target_score=target_score,
    )

    # Validation between response raw and store aggregate for team.
    store_team = parsed["store_agg"][parsed["store_agg"].get("team_name", "").astype(str).str.strip().eq(team)].copy()
    store_totals = {
        "promoters": int(pd.to_numeric(store_team.get("promoters", 0), errors="coerce").fillna(0).sum()),
        "passives": int(pd.to_numeric(store_team.get("passives", 0), errors="coerce").fillna(0).sum()),
        "detractors": int(pd.to_numeric(store_team.get("detractors", 0), errors="coerce").fillna(0).sum()),
        "total_responses": int(pd.to_numeric(store_team.get("total_responses", 0), errors="coerce").fillna(0).sum()),
        "store_count": int(store_team.get("store_code", pd.Series(dtype=object)).nunique()),
        "agency_count": int(store_team.get("agency_name", pd.Series(dtype=object)).nunique()),
        "sales_promoters": int(pd.to_numeric(store_team.get("sales_promoters", 0), errors="coerce").fillna(0).sum()),
        "sales_passives": int(pd.to_numeric(store_team.get("sales_passives", 0), errors="coerce").fillna(0).sum()),
        "sales_detractors": int(pd.to_numeric(store_team.get("sales_detractors", 0), errors="coerce").fillna(0).sum()),
        "sales_total_responses": int(pd.to_numeric(store_team.get("sales_total_responses", 0), errors="coerce").fillna(0).sum()),
        "non_sales_promoters": int(pd.to_numeric(store_team.get("non_sales_promoters", 0), errors="coerce").fillna(0).sum()),
        "non_sales_passives": int(pd.to_numeric(store_team.get("non_sales_passives", 0), errors="coerce").fillna(0).sum()),
        "non_sales_detractors": int(pd.to_numeric(store_team.get("non_sales_detractors", 0), errors="coerce").fillna(0).sum()),
        "non_sales_total_responses": int(pd.to_numeric(store_team.get("non_sales_total_responses", 0), errors="coerce").fillna(0).sum()),
    }
    if store_totals["sales_total_responses"]:
        store_totals["sales_nps_score"] = (store_totals["sales_promoters"] - store_totals["sales_detractors"]) / store_totals["sales_total_responses"] * 100
    else:
        store_totals["sales_nps_score"] = None
    if store_totals["non_sales_total_responses"]:
        store_totals["non_sales_nps_score"] = (store_totals["non_sales_promoters"] - store_totals["non_sales_detractors"]) / store_totals["non_sales_total_responses"] * 100
    else:
        store_totals["non_sales_nps_score"] = None
    validation = {
        "raw_vs_store_promoters_delta": team_summary["promoters"] - store_totals["promoters"],
        "raw_vs_store_passives_delta": team_summary["passives"] - store_totals["passives"],
        "raw_vs_store_detractors_delta": team_summary["detractors"] - store_totals["detractors"],
        "raw_vs_store_total_delta": team_summary["total_responses"] - store_totals["total_responses"],
    }

    # Persist artifacts.
    ymd = profile.report_date.strftime("%Y%m%d") if profile.report_date else "unknown"
    outputs = {}
    for name, df in parsed.items():
        out = PROCESSED_DIR / f"{name}_{ymd}.parquet"
        write_parquet(df, out)
        outputs[name] = str(out)
    priority_path = PROCESSED_DIR / f"store_priority_{team}_{ymd}.parquet"
    write_parquet(store_priority, priority_path)
    outputs["store_priority"] = str(priority_path)
    non_sales_path = PROCESSED_DIR / f"non_sales_drilldown_{team}_{ymd}.parquet"
    write_parquet(non_sales_drilldown, non_sales_path)
    outputs["non_sales_drilldown"] = str(non_sales_path)
    non_sales_type_path = PROCESSED_DIR / f"non_sales_business_type_top_{team}_{ymd}.parquet"
    write_parquet(non_sales_business_type_top, non_sales_type_path)
    outputs["non_sales_business_type_top"] = str(non_sales_type_path)
    daily_nps_trend_path = PROCESSED_DIR / f"daily_nps_trend_{team}_{ymd}.parquet"
    write_parquet(daily_nps_trend, daily_nps_trend_path)
    outputs["daily_nps_trend"] = str(daily_nps_trend_path)
    nps_time_intelligence_path = PROCESSED_DIR / f"nps_time_intelligence_{team}_{ymd}.parquet"
    write_parquet(nps_time_intelligence, nps_time_intelligence_path)
    outputs["nps_time_intelligence"] = str(nps_time_intelligence_path)
    non_sales_trend_path = PROCESSED_DIR / f"store_non_sales_trend_{team}_{ymd}.parquet"
    write_parquet(store_non_sales_trend, non_sales_trend_path)
    outputs["store_non_sales_trend"] = str(non_sales_trend_path)
    store_daily_heatmap_path = PROCESSED_DIR / f"store_daily_heatmap_{team}_{ymd}.parquet"
    write_parquet(store_daily_heatmap, store_daily_heatmap_path)
    outputs["store_daily_heatmap"] = str(store_daily_heatmap_path)
    weekday_time_hotspots_path = PROCESSED_DIR / f"weekday_time_hotspots_{team}_{ymd}.parquet"
    write_parquet(weekday_time_hotspots, weekday_time_hotspots_path)
    outputs["weekday_time_hotspots"] = str(weekday_time_hotspots_path)
    sales_good_ns_weak_path = PROCESSED_DIR / f"sales_good_non_sales_weak_{team}_{ymd}.parquet"
    write_parquet(sales_good_non_sales_weak, sales_good_ns_weak_path)
    outputs["sales_good_non_sales_weak"] = str(sales_good_ns_weak_path)
    action_path = PROCESSED_DIR / f"store_action_sheet_{team}_{ymd}.parquet"
    write_parquet(action_sheet, action_path)
    outputs["store_action_sheet"] = str(action_path)
    diff_path = PROCESSED_DIR / f"nps_source_recalc_diff_{team}_{ymd}.parquet"
    write_parquet(nps_source_recalc_diff, diff_path)
    outputs["nps_source_recalc_diff"] = str(diff_path)
    sample_warning_path = PROCESSED_DIR / f"sample_warning_{team}_{ymd}.parquet"
    write_parquet(sample_warning, sample_warning_path)
    outputs["sample_warning"] = str(sample_warning_path)

    # Human-readable export for quick review.
    excel_path = EXPORT_DIR / f"nps_ops_summary_{team}_{ymd}.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        pd.DataFrame([team_summary]).to_excel(writer, sheet_name="team_summary", index=False)
        pd.DataFrame([store_totals]).to_excel(writer, sheet_name="store_sheet_totals", index=False)
        pd.DataFrame([validation]).to_excel(writer, sheet_name="validation", index=False)
        store_priority.head(EXPORT_TOP_N_STORES).to_excel(writer, sheet_name="store_priority", index=False)
        non_sales_drilldown.head(EXPORT_TOP_N_STORES).to_excel(writer, sheet_name="non_sales_drilldown", index=False)
        non_sales_business_type_top.head(EXPORT_TOP_N_TYPES).to_excel(writer, sheet_name="non_sales_type_top", index=False)
        daily_nps_trend.to_excel(writer, sheet_name="daily_nps_trend", index=False)
        nps_time_intelligence.to_excel(writer, sheet_name="time_intelligence", index=False)
        store_non_sales_trend.to_excel(writer, sheet_name="store_non_sales_trend", index=False)
        store_daily_heatmap.to_excel(writer, sheet_name="store_daily_heatmap", index=False)
        weekday_time_hotspots.to_excel(writer, sheet_name="weekday_time_hotspots", index=False)
        sales_good_non_sales_weak.head(EXPORT_TOP_N_STORES).to_excel(writer, sheet_name="sales_good_ns_weak", index=False)
        nps_source_recalc_diff.head(EXPORT_TOP_N_AUDIT).to_excel(writer, sheet_name="nps_recalc_audit", index=False)
        sample_warning.head(EXPORT_TOP_N_AUDIT).to_excel(writer, sheet_name="sample_warning", index=False)
        action_sheet.head(EXPORT_TOP_N_STORES).to_excel(writer, sheet_name="store_action_sheet", index=False)
        parsed["negative_feedback"][parsed["negative_feedback"].get("team_name", "").astype(str).str.strip().eq(team)].to_excel(writer, sheet_name="negative_feedback", index=False)
    outputs["excel_summary"] = str(excel_path)

    md_path = EXPORT_DIR / f"nps_ops_summary_{team}_{ymd}.md"
    top = store_priority.head(10)[[c for c in ["agency_name", "store_name", "total_responses", "promoters", "passives", "detractors", "nps_recalc", "required_promoters_to_target", "sample_grade", "diagnosis_type", "priority_score"] if c in store_priority.columns]]
    ns_top = non_sales_drilldown.head(10)[[c for c in ["agency_name", "store_name", "axis_total_responses", "axis_passives", "axis_detractors", "axis_nps", "axis_target_gap", "axis_required_promoters", "focus_reason", "axis_priority_score"] if c in non_sales_drilldown.columns]]
    ns_type_top = non_sales_business_type_top.head(10)[[c for c in ["business_type", "total_responses", "promoters", "passives", "detractors", "nps", "risk_count", "risk_rate"] if c in non_sales_business_type_top.columns]]
    sales_good_ns_weak_top = sales_good_non_sales_weak.head(10)[[c for c in ["agency_name", "store_name", "sales_total_responses", "sales_nps_score_display", "axis_total_responses", "non_sales_nps_score_display", "non_sales_target_gap", "axis_nps", "axis_required_promoters"] if c in sales_good_non_sales_weak.columns]]
    nps_diff_top = nps_source_recalc_diff.head(15)[[c for c in ["agency_name", "store_name", "axis", "axis_total_responses", "source_nps", "recalc_nps", "nps_diff", "nps_diff_abs", "diagnosis_type"] if c in nps_source_recalc_diff.columns]]
    sample_warning_top = sample_warning.head(15)[[c for c in ["agency_name", "store_name", "axis", "axis_total_responses", "promoters", "passives", "detractors", "recalc_nps", "sample_grade", "risk_count", "sample_warning"] if c in sample_warning.columns]]
    action_top = action_sheet.head(10)[[c for c in ["agency_name", "store_name", "axis_nps", "axis_target_gap", "top_business_type", "top_voc_category", "representative_voc", "이번주_액션"] if c in action_sheet.columns]]
    md = [
        f"# NPS 운영 Summary — {team} {ymd}",
        "",
        "## 1. 파일 Profile",
        f"- source: `{path.name}`",
        f"- report_date: `{profile.report_date}`",
        f"- missing_required_sheets: `{profile.missing_required_sheets}`",
        "",
        "## 2. Raw 응답 원장 기준 팀 Summary",
        f"- 매장 수: {team_summary['store_count']}",
        f"- 대리점 수: {team_summary['agency_count']}",
        f"- 추천/중립/비추천/총응답자: {team_summary['promoters']} / {team_summary['passives']} / {team_summary['detractors']} / {team_summary['total_responses']}",
        f"- NPS: {fmt_optional_score(team_summary['nps_score'])}",
        f"- 판매성 NPS: {fmt_optional_score(store_totals['sales_nps_score'])} ({store_totals['sales_total_responses']}건)",
        f"- 비판매성 NPS: {fmt_optional_score(store_totals['non_sales_nps_score'])} ({store_totals['non_sales_total_responses']}건)",
        "",
        "## 3. 매장별 시트 검산",
        f"- 매장별 시트 매장 수: {store_totals['store_count']}",
        f"- 매장별 시트 대리점 수: {store_totals['agency_count']}",
        f"- 매장별 시트 추천/중립/비추천/총응답자: {store_totals['promoters']} / {store_totals['passives']} / {store_totals['detractors']} / {store_totals['total_responses']}",
        f"- Raw 원장 대비 delta: {validation}",
        "",
        "## 4. 개입 우선순위 Top 10",
        top.to_markdown(index=False),
        "",
        "## 5. 비판매성 NPS 집중관리 Top 10",
        ns_top.to_markdown(index=False),
        "",
        "## 6. 비판매성 업무유형별 Risk Top 10",
        ns_type_top.to_markdown(index=False),
        "",
        "## 7. 판매성 양호·비판매성 취약 매장 Top 10",
        sales_good_ns_weak_top.to_markdown(index=False),
        "",
        "## 8. NPS 재계산 검산 Top 15",
        nps_diff_top.to_markdown(index=False),
        "",
        "## 9. 샘플소수 경고 Top 15",
        sample_warning_top.to_markdown(index=False),
        "",
        "## 10. 매장별 Action Sheet Top 10",
        action_top.to_markdown(index=False),
        "",
        "## 11. 해석 메모",
        "- 우선순위는 NPS 점수만이 아니라 비추천/중립 절대량, 목표까지 필요 추천수, 응답자 수를 함께 반영합니다.",
        f"- Excel 요약 시트는 운영 검토용 Top N입니다: 매장/Action 계열 Top {EXPORT_TOP_N_STORES}, 업무유형 Top {EXPORT_TOP_N_TYPES}, 검산/경고 Top {EXPORT_TOP_N_AUDIT}.",
        "- 응답자 수가 작은 매장은 `샘플 착시형`으로 분리하여 과잉해석을 방지합니다.",
        "- VOC 분류는 내부 데이터 외부 전송 없이 로컬 rule 기반으로 산정합니다.",
        "- 운영 판단 기준은 추천/중립/비추천 count 기반 재계산 NPS이며, 원천 Excel NPS 컬럼은 -100~100 점수로 표준화해 검산/참조용으로 유지합니다.",
    ]
    if scale_warnings:
        md.extend(["", "## 12. NPS 스케일 경고", *[f"- {w}" for w in scale_warnings]])
    if response_contract_warnings:
        md.extend(["", "## 13. Response Fact 계약 경고", *[f"- {w}" for w in response_contract_warnings]])
    md_path.write_text("\n".join(md), encoding="utf-8")
    outputs["markdown_summary"] = str(md_path)

    return {
        "source": str(path),
        "report_date": str(profile.report_date),
        "team_summary": team_summary,
        "store_totals": store_totals,
        "validation": validation,
        "scale_warnings": scale_warnings,
        "response_contract_warnings": response_contract_warnings,
        "outputs": outputs,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", type=Path, default=None)
    ap.add_argument("--team", default=DEFAULT_TEAM)
    ap.add_argument("--target-score", type=float, default=DEFAULT_TARGET_SCORE)
    args = ap.parse_args()
    path = args.file or find_latest_file()
    result = build(path, team=args.team, target_score=args.target_score)
    print("BUILD_OK")
    print("source=", result["source"])
    print("report_date=", result["report_date"])
    print("team_summary=", result["team_summary"])
    print("store_totals=", result["store_totals"])
    print("validation=", result["validation"])
    print("scale_warnings=", result["scale_warnings"])
    print("response_contract_warnings=", result["response_contract_warnings"])
    print("outputs=")
    for k, v in result["outputs"].items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
