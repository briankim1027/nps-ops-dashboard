from __future__ import annotations

import re
from typing import Any

import pandas as pd

from nps_ops.metrics import nps_score, normalize_nps_series, required_promoters_to_target, sample_confidence, sample_grade


VOC_RULES: list[tuple[str, list[str], str]] = [
    ("불친절/응대태도", ["불친절", "친절", "태도", "말투", "짜증", "무시", "기분", "성의", "응대"], "응대 톤·설명 태도 재점검, 첫 응대/마무리 멘트 코칭"),
    ("대기/처리시간", ["대기", "기다", "오래", "시간", "느림", "지연", "늦", "처리시간"], "예약/대기 안내, 처리 예상시간 고지, 지연 시 중간 안내"),
    ("요금/제도 설명부족", ["요금", "가격", "비싸", "할인", "약정", "위약", "청구", "결합", "혜택", "제도", "부가", "설명"], "요금·할인·약정 조건을 고객 언어로 재설명하고 핵심 금액 재확인"),
    ("업무처리 미흡", ["처리", "개통", "변경", "해지", "수납", "유심", "USIM", "명의", "번호", "기기", "오류", "실수", "누락"], "업무별 체크리스트 재확인, 처리 완료 전 고객 확인 절차 강화"),
    ("재고/상품/품질", ["재고", "제품", "기기", "폰", "단말", "품질", "고장", "불량", "색상"], "재고/상품 안내 정확도와 대체 제안 스크립트 점검"),
]

NO_CONTENT_PATTERNS = ["없음", "없어요", "없습니다", "없다", "무", "nan", "none", ".", "-", "네", "예", "아", "보통", "그냥 보통이에요"]


def classify_voc(reason: Any, business_type: Any = "") -> tuple[str, str]:
    """Rule-based local VOC categorisation for sensitive internal data.

    Keep this deterministic/local: do not call external AI services for company VOC.
    """
    text = " ".join([str(reason or ""), str(business_type or "")]).strip()
    text_norm = re.sub(r"\s+", " ", text).lower()
    reason_norm = str(reason or "").strip().lower()
    if not reason_norm or reason_norm in NO_CONTENT_PATTERNS:
        return "무의미/내용없음", "원문만으로 코칭 사유 판단 어려움: 동일 업무유형 반복 여부만 확인"
    for category, keywords, hint in VOC_RULES:
        if any(k.lower() in text_norm for k in keywords):
            return category, hint
    return "기타/수기확인", "원문 확인 후 매장 상황에 맞는 개별 코칭 필요"


def add_voc_classification(negative: pd.DataFrame) -> pd.DataFrame:
    if negative.empty:
        return negative.copy()
    out = negative.copy()
    pairs = out.apply(lambda r: classify_voc(r.get("reason_text"), r.get("business_type")), axis=1)
    out["voc_category"] = [p[0] for p in pairs]
    out["coaching_hint"] = [p[1] for p in pairs]
    return out


def _axis_calc(df: pd.DataFrame, prefix: str, target_score: float) -> pd.DataFrame:
    out = df.copy()
    p = f"{prefix}promoters"
    pa = f"{prefix}passives"
    d = f"{prefix}detractors"
    t = f"{prefix}total_responses"
    for c in [p, pa, d, t]:
        out[c] = pd.to_numeric(out.get(c, 0), errors="coerce").fillna(0).astype(int)
    out["axis_promoters"] = out[p]
    out["axis_passives"] = out[pa]
    out["axis_detractors"] = out[d]
    out["axis_total_responses"] = out[t]
    out["axis_nps"] = out.apply(
        lambda r: ((r["axis_promoters"] - r["axis_detractors"]) / r["axis_total_responses"] * 100) if r["axis_total_responses"] else None,
        axis=1,
    )
    out["axis_target_gap"] = out["axis_nps"] - target_score
    out["axis_required_promoters"] = out.apply(
        lambda r: required_promoters_to_target(r["axis_promoters"], r["axis_passives"], r["axis_detractors"], target_score),
        axis=1,
    )
    out["axis_sample_grade"] = out["axis_total_responses"].apply(sample_grade)
    out["axis_risk_count"] = out["axis_passives"] + out["axis_detractors"]
    # Care Priority = Base Risk Score × Sample Confidence (keyed on this axis' response count).
    out["axis_base_priority_score"] = (
        out["axis_detractors"] * 10
        + out["axis_passives"] * 3
        + out["axis_required_promoters"] * 2
        + out["axis_total_responses"].clip(upper=30) / 10
        + (-out["axis_target_gap"].clip(upper=0) / 10)
    )
    out["axis_sample_confidence"] = out["axis_total_responses"].apply(sample_confidence)
    out["axis_priority_score"] = out["axis_base_priority_score"] * out["axis_sample_confidence"]
    return out


def build_non_sales_drilldown(store_priority: pd.DataFrame, target_score: float) -> pd.DataFrame:
    df = _axis_calc(store_priority, "non_sales_", target_score)
    df["focus_reason"] = df.apply(
        lambda r: "비판매성 목표미달" if pd.notna(r["axis_nps"]) and r["axis_nps"] < target_score else ("비판매성 Risk누적" if r["axis_risk_count"] > 0 else "관찰"),
        axis=1,
    )
    cols = [
        "agency_name", "store_code", "store_name", "axis_total_responses", "axis_promoters", "axis_passives", "axis_detractors",
        "axis_nps", "axis_target_gap", "axis_required_promoters", "axis_sample_grade", "axis_risk_count", "focus_reason", "axis_priority_score",
    ]
    return df[df["axis_total_responses"] > 0][[c for c in cols if c in df.columns]].sort_values(
        ["axis_priority_score", "axis_detractors", "axis_risk_count", "axis_total_responses"], ascending=False
    )


def _safe_text(value: Any, fallback: str = "확인 필요") -> str:
    if value is None or pd.isna(value):
        return fallback
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text if text else fallback


def build_weekly_action(row: pd.Series) -> str:
    """Return a field-ready 1~2 line action for a store."""
    nps = row.get("axis_nps")
    gap = row.get("axis_target_gap")
    need = int(row.get("axis_required_promoters", 0) or 0)
    passives = int(row.get("axis_passives", 0) or 0)
    detractors = int(row.get("axis_detractors", 0) or 0)
    biz = _safe_text(row.get("top_business_type"), "비판매성 업무")
    voc = _safe_text(row.get("top_voc_category"), "VOC 사유")
    hint = _safe_text(row.get("coaching_hint"), "중립/비추천 발생 업무유형과 응대 프로세스 확인")
    rep = _safe_text(row.get("representative_voc"), "대표 VOC 없음")

    if detractors >= 2:
        lead = f"이번 주 {biz} 비추천 {detractors}건부터 전수 확인: {voc} 기준으로 고객 안내·처리완료 확인 멘트 재점검."
    elif passives > 0:
        lead = f"이번 주 {biz} 중립 {passives}건을 추천 전환 후보로 관리: 설명 누락/대기 안내/마무리 확인을 점검."
    elif pd.notna(gap) and gap < 0:
        lead = f"비판매성 NPS {float(nps):.1f}로 목표 대비 {float(gap):.1f}p 부족: {biz} 응대 루틴을 우선 점검."
    else:
        lead = f"비판매성 응답 품질 유지: {biz}에서 추천 사유를 확보하고 샘플을 추가 확보."
    close = f"담당자 액션: {hint} 필요추천 {need}건. VOC cue: {rep[:45]}"
    return f"{lead}\n{close}"


def build_non_sales_business_type_top(response_fact: pd.DataFrame, team: str = "전북") -> pd.DataFrame:
    """Aggregate non-sales NPS by business type from the response fact table."""
    if response_fact.empty:
        return pd.DataFrame()
    df = response_fact.copy()
    if "team_name" in df.columns:
        df = df[df["team_name"].astype(str).str.strip().eq(team)].copy()
    if "NCSI" in df.columns:
        df = df[df["NCSI"].astype(str).str.strip().eq("비판매성")].copy()
    if df.empty:
        return pd.DataFrame()
    for c in ["promoter_flag", "passive_flag", "detractor_flag"]:
        df[c] = pd.to_numeric(df.get(c, 0), errors="coerce").fillna(0).astype(int)
    if "business_type" not in df.columns:
        df["business_type"] = "미분류"
    out = (
        df.assign(business_type=df["business_type"].fillna("미분류").astype(str).str.strip().replace("", "미분류"))
        .groupby("business_type", dropna=False)
        .agg(
            promoters=("promoter_flag", "sum"),
            passives=("passive_flag", "sum"),
            detractors=("detractor_flag", "sum"),
            total_responses=("promoter_flag", "size"),
        )
        .reset_index()
    )
    out["nps"] = out.apply(lambda r: nps_score(r.promoters, r.detractors, r.total_responses), axis=1)
    out["risk_count"] = out["passives"] + out["detractors"]
    out["risk_rate"] = out["risk_count"] / out["total_responses"].where(out["total_responses"] != 0, pd.NA)
    return out.sort_values(["risk_count", "detractors", "total_responses"], ascending=False)


def _response_date_col(df: pd.DataFrame) -> str | None:
    """Return the NPS operating date column.

    Time Intelligence is based on the response ledger's 업무처리일자, so process_date
    must win over evaluation_date when both are available.
    """
    for c in ["process_date", "evaluation_date", "report_date"]:
        if c in df.columns:
            return c
    return None


def _prepare_team_response_fact(response_fact: pd.DataFrame, team: str = "전북") -> pd.DataFrame:
    if response_fact.empty:
        return pd.DataFrame()
    df = response_fact.copy()
    if "team_name" in df.columns:
        df = df[df["team_name"].astype(str).str.strip().eq(team)].copy()
    date_col = _response_date_col(df)
    if not date_col:
        return pd.DataFrame()
    df["trend_date"] = pd.to_datetime(df[date_col], errors="coerce").dt.normalize()
    df = df[df["trend_date"].notna()].copy()
    for c in ["promoter_flag", "passive_flag", "detractor_flag"]:
        df[c] = pd.to_numeric(df.get(c, 0), errors="coerce").fillna(0).astype(int)
    if "NCSI" not in df.columns:
        df["NCSI"] = "미분류"
    return df


def build_daily_nps_trend(response_fact: pd.DataFrame, team: str = "전북") -> pd.DataFrame:
    """Daily NPS trend from the response ledger for overall/sales/non-sales axes."""
    df = _prepare_team_response_fact(response_fact, team)
    if df.empty:
        return pd.DataFrame()

    def agg_axis(frame: pd.DataFrame, axis_label: str) -> pd.DataFrame:
        out = (
            frame.groupby("trend_date", dropna=False)
            .agg(
                promoters=("promoter_flag", "sum"),
                passives=("passive_flag", "sum"),
                detractors=("detractor_flag", "sum"),
                total_responses=("promoter_flag", "size"),
            )
            .reset_index()
        )
        out["axis"] = axis_label
        out["nps"] = out.apply(lambda r: nps_score(r.promoters, r.detractors, r.total_responses), axis=1)
        out["risk_count"] = out["passives"] + out["detractors"]
        return out

    parts = [agg_axis(df, "종합")]
    sales = df[df["NCSI"].astype(str).str.strip().eq("판매성")]
    non_sales = df[df["NCSI"].astype(str).str.strip().eq("비판매성")]
    if not sales.empty:
        parts.append(agg_axis(sales, "판매성"))
    if not non_sales.empty:
        parts.append(agg_axis(non_sales, "비판매성"))
    out = pd.concat(parts, ignore_index=True).sort_values(["trend_date", "axis"])
    return out


def build_nps_time_intelligence(response_fact: pd.DataFrame, team: str = "전북", target_score: float = 87.0, report_date: Any = None) -> pd.DataFrame:
    """One-row dynamic interpretation message for weekly flow and today's NPS state.

    Scope is intentionally NPS response-ledger only; it does not join daily-cost or other sales denominators.
    """
    daily_long = build_daily_nps_trend(response_fact, team)
    if daily_long.empty:
        return pd.DataFrame()
    daily = daily_long.pivot_table(
        index="trend_date",
        columns="axis",
        values=["promoters", "passives", "detractors", "total_responses", "nps", "risk_count"],
        aggfunc="first",
    )
    daily.columns = [f"{axis}_{metric}" for metric, axis in daily.columns]
    daily = daily.reset_index().sort_values("trend_date")
    if report_date is not None and not pd.isna(pd.to_datetime(report_date, errors="coerce")):
        today = pd.to_datetime(report_date, errors="coerce").normalize()
    else:
        today = daily["trend_date"].max()
    if today not in set(daily["trend_date"]):
        today = daily[daily["trend_date"].le(today)]["trend_date"].max()
    if pd.isna(today):
        today = daily["trend_date"].max()
    week_start = today - pd.Timedelta(days=int(today.weekday()))
    week_end = week_start + pd.Timedelta(days=6)
    week_long = daily_long[(daily_long["trend_date"] >= week_start) & (daily_long["trend_date"] <= week_end)].copy()
    today_long = daily_long[daily_long["trend_date"].eq(today)].copy()
    prev_candidates = daily[daily["trend_date"].lt(today)]
    prev = prev_candidates.iloc[-1] if not prev_candidates.empty else None

    def axis_row(frame: pd.DataFrame, axis: str) -> pd.Series:
        m = frame[frame["axis"].eq(axis)]
        return m.iloc[0] if not m.empty else pd.Series(dtype=object)

    today_overall = axis_row(today_long, "종합")
    today_sales = axis_row(today_long, "판매성")
    today_non_sales = axis_row(today_long, "비판매성")
    week_overall = axis_row(
        week_long.groupby("axis", as_index=False).agg(
            promoters=("promoters", "sum"), passives=("passives", "sum"), detractors=("detractors", "sum"), total_responses=("total_responses", "sum")
        ).assign(nps=lambda x: x.apply(lambda r: nps_score(r.promoters, r.detractors, r.total_responses), axis=1), risk_count=lambda x: x["passives"] + x["detractors"]),
        "종합",
    )

    today_nps = today_overall.get("nps", pd.NA)
    today_total = int(today_overall.get("total_responses", 0) or 0)
    today_risk = int(today_overall.get("risk_count", 0) or 0)
    today_sales_nps = today_sales.get("nps", pd.NA)
    today_non_sales_nps = today_non_sales.get("nps", pd.NA)
    week_nps = week_overall.get("nps", pd.NA)
    week_total = int(week_overall.get("total_responses", 0) or 0)
    prev_nps = prev.get("종합_nps") if prev is not None and "종합_nps" in prev.index else pd.NA
    day_delta = (float(today_nps) - float(prev_nps)) if pd.notna(today_nps) and pd.notna(prev_nps) else pd.NA

    if pd.isna(today_nps):
        status = "오늘 응답 없음"
    elif today_total < 5:
        status = "샘플 확인"
    elif today_nps >= target_score and today_risk == 0:
        status = "양호 유지"
    elif today_nps >= target_score:
        status = "목표권이나 Risk 확인"
    elif today_risk > 0:
        status = "즉시 확인"
    else:
        status = "회복 관찰"

    weak_axis = "비판매성" if pd.notna(today_non_sales_nps) and (pd.isna(today_sales_nps) or today_non_sales_nps < today_sales_nps) else "판매성"
    weak_nps = today_non_sales_nps if weak_axis == "비판매성" else today_sales_nps
    if pd.notna(day_delta):
        delta_msg = f"전일 대비 {day_delta:+.1f}p"
    else:
        delta_msg = "전일 비교 데이터 부족"
    if pd.notna(weak_nps):
        axis_msg = f"오늘 취약축은 {weak_axis}({float(weak_nps):.1f})입니다."
    else:
        axis_msg = "오늘 축별 응답이 부족해 취약축은 추가 확인이 필요합니다."
    if pd.notna(week_nps):
        if week_nps >= target_score:
            week_status = "목표를 상회"
        elif week_nps >= target_score - 5:
            week_status = "목표에 근접"
        else:
            week_status = "관리가 필요한 수준"
        weekly_situation = f"이번 주 종합 NPS는 {float(week_nps):.1f}점으로 {week_status}하고 있습니다. {axis_msg}"
    else:
        weekly_situation = axis_msg
    if pd.notna(day_delta):
        if day_delta >= 5:
            recent_change = f"{delta_msg} 개선되었습니다. 회복 흐름으로 보입니다."
        elif day_delta <= -5:
            recent_change = f"{delta_msg} 하락했습니다. 중립/비추천 발생 여부를 우선 확인하세요."
        else:
            recent_change = f"{delta_msg}로 큰 변화는 없습니다."
    else:
        recent_change = delta_msg
    if today_total == 0:
        action_msg = "오늘 원장 응답이 없어 주간 누적 흐름만 관찰하세요."
    elif today_total < 5:
        action_msg = f"오늘 응답 {today_total}건으로 표본이 작습니다. 확정 판단보다 추가 응답과 VOC 발생 여부를 관찰하세요."
    elif today_risk > 0:
        action_msg = f"오늘 중립/비추천 {today_risk}건을 먼저 확인하고, 해당 업무유형의 설명·마무리 멘트를 점검하세요."
    elif pd.notna(today_nps) and today_nps < target_score:
        action_msg = "오늘 목표 미달이나 Risk 절대량은 낮습니다. 추가 추천 샘플 확보와 응답 추이를 확인하세요."
    else:
        action_msg = "오늘은 목표권입니다. 추천 사유와 우수 응대 패턴을 이번 주 공유 후보로 남기세요."
    headline = f"{today.strftime('%m/%d')} 현재 {status}: 종합 NPS {float(today_nps):.1f} / 응답 {today_total}건" if pd.notna(today_nps) else f"{today.strftime('%m/%d')} 현재 {status}"
    narrative = f"{weekly_situation} {recent_change} {action_msg}"
    return pd.DataFrame([
        {
            "today_date": today,
            "week_start": week_start,
            "week_end": week_end,
            "target_score": target_score,
            "today_status": status,
            "today_nps": today_nps,
            "today_total_responses": today_total,
            "today_risk_count": today_risk,
            "today_sales_nps": today_sales_nps,
            "today_non_sales_nps": today_non_sales_nps,
            "previous_overall_nps": prev_nps,
            "day_delta_nps": day_delta,
            "week_nps": week_nps,
            "week_total_responses": week_total,
            "weak_axis": weak_axis,
            "headline": headline,
            "weekly_situation": weekly_situation,
            "recent_change": recent_change,
            "action_point": action_msg,
            "narrative": narrative,
            "recommended_action": action_msg,
        }
    ])


def build_store_non_sales_trend(response_fact: pd.DataFrame, team: str = "전북") -> pd.DataFrame:
    """Daily non-sales NPS trend by store from response fact."""
    if response_fact.empty:
        return pd.DataFrame()
    df = response_fact.copy()
    if "team_name" in df.columns:
        df = df[df["team_name"].astype(str).str.strip().eq(team)].copy()
    if "NCSI" in df.columns:
        df = df[df["NCSI"].astype(str).str.strip().eq("비판매성")].copy()
    if df.empty:
        return pd.DataFrame()
    date_col = _response_date_col(df)
    if not date_col:
        return pd.DataFrame()
    df["trend_date"] = pd.to_datetime(df.get(date_col), errors="coerce").dt.normalize()
    df = df[df["trend_date"].notna()].copy()
    for c in ["promoter_flag", "passive_flag", "detractor_flag"]:
        df[c] = pd.to_numeric(df.get(c, 0), errors="coerce").fillna(0).astype(int)
    for c in ["agency_name", "store_code", "store_name"]:
        if c not in df.columns:
            df[c] = ""
    out = (
        df.groupby(["trend_date", "agency_name", "store_code", "store_name"], dropna=False)
        .agg(
            promoters=("promoter_flag", "sum"),
            passives=("passive_flag", "sum"),
            detractors=("detractor_flag", "sum"),
            total_responses=("promoter_flag", "size"),
        )
        .reset_index()
    )
    out["nps"] = out.apply(lambda r: nps_score(r.promoters, r.detractors, r.total_responses), axis=1)
    out["risk_count"] = out["passives"] + out["detractors"]
    return out.sort_values(["trend_date", "agency_name", "store_name"])


def build_sales_good_non_sales_weak(store_priority: pd.DataFrame, target_score: float) -> pd.DataFrame:
    """Stores where sales NPS is healthy but non-sales NPS is below target."""
    if store_priority.empty:
        return pd.DataFrame()
    df = _axis_calc(store_priority, "non_sales_", target_score)
    for c in ["sales_nps_score", "non_sales_nps_score", "sales_nps_recalc", "non_sales_nps_recalc", "sales_total_responses", "non_sales_total_responses"]:
        df[c] = pd.to_numeric(df.get(c, pd.NA), errors="coerce")
    df["sales_source_nps_score"] = normalize_nps_series(df["sales_nps_score"])
    df["non_sales_source_nps_score"] = normalize_nps_series(df["non_sales_nps_score"])
    # Operational decisions use count-recalculated NPS. Source aggregate NPS is kept only as a reference.
    df["sales_nps_score_display"] = df["sales_nps_recalc"]
    df["non_sales_nps_score_display"] = df["axis_nps"]
    df["non_sales_target_gap"] = df["non_sales_nps_score_display"] - target_score
    # Backward-compatible alias for existing dashboard/export column names.
    df["non_sales_source_target_gap"] = df["non_sales_target_gap"]
    mask = (
        df["sales_nps_score_display"].ge(target_score)
        & df["non_sales_nps_score_display"].lt(target_score)
        & df["sales_total_responses"].fillna(0).gt(0)
        & df["axis_total_responses"].fillna(0).gt(0)
    )
    cols = [
        "agency_name", "store_code", "store_name", "sales_total_responses", "sales_nps_score_display",
        "axis_total_responses", "non_sales_nps_score_display", "non_sales_target_gap", "axis_nps", "axis_target_gap", "axis_passives", "axis_detractors",
        "axis_required_promoters", "axis_priority_score",
    ]
    return df[mask][[c for c in cols if c in df.columns]].sort_values(
        ["axis_priority_score", "axis_detractors", "axis_total_responses"], ascending=False
    )


def build_nps_source_recalc_diff(store_priority: pd.DataFrame) -> pd.DataFrame:
    """Compare source Excel NPS columns with count-recalculated operating NPS.

    Operating decisions use *_nps_recalc. This audit table surfaces large gaps so
    field users can explain why the dashboard priority differs from the source
    workbook aggregate columns.
    """
    if store_priority.empty:
        return pd.DataFrame()
    df = store_priority.copy()
    axes = [
        ("종합", "nps_score", "nps_recalc", "total_responses"),
        ("판매성", "sales_nps_score", "sales_nps_recalc", "sales_total_responses"),
        ("비판매성", "non_sales_nps_score", "non_sales_nps_recalc", "non_sales_total_responses"),
    ]
    rows: list[pd.DataFrame] = []
    id_cols = [c for c in ["agency_name", "store_code", "store_name", "diagnosis_type"] if c in df.columns]
    for axis_label, source_col, recalc_col, total_col in axes:
        if source_col not in df.columns or recalc_col not in df.columns:
            continue
        tmp = df[id_cols].copy()
        tmp["axis"] = axis_label
        tmp["source_nps"] = normalize_nps_series(df[source_col])
        tmp["recalc_nps"] = pd.to_numeric(df[recalc_col], errors="coerce")
        tmp["nps_diff"] = tmp["recalc_nps"] - tmp["source_nps"]
        tmp["nps_diff_abs"] = tmp["nps_diff"].abs()
        tmp["axis_total_responses"] = pd.to_numeric(df.get(total_col, pd.NA), errors="coerce")
        rows.append(tmp)
    if not rows:
        return pd.DataFrame()
    out = pd.concat(rows, ignore_index=True)
    out = out[out["source_nps"].notna() & out["recalc_nps"].notna()].copy()
    out = out[out["nps_diff_abs"] > 0.01].copy()
    return out.sort_values(["nps_diff_abs", "axis_total_responses"], ascending=[False, False])


def build_sample_warning(store_priority: pd.DataFrame, target_score: float, min_sample: int = 5) -> pd.DataFrame:
    """Stores/axes where the NPS signal is likely unstable because n is small."""
    if store_priority.empty:
        return pd.DataFrame()
    df = store_priority.copy()
    axes = [
        ("종합", "promoters", "passives", "detractors", "total_responses", "nps_recalc"),
        ("판매성", "sales_promoters", "sales_passives", "sales_detractors", "sales_total_responses", "sales_nps_recalc"),
        ("비판매성", "non_sales_promoters", "non_sales_passives", "non_sales_detractors", "non_sales_total_responses", "non_sales_nps_recalc"),
    ]
    id_cols = [c for c in ["agency_name", "store_code", "store_name", "diagnosis_type"] if c in df.columns]
    rows: list[pd.DataFrame] = []
    for axis_label, pcol, pacol, dcol, tcol, nps_col in axes:
        if tcol not in df.columns or nps_col not in df.columns:
            continue
        tmp = df[id_cols].copy()
        tmp["axis"] = axis_label
        tmp["promoters"] = pd.to_numeric(df.get(pcol, 0), errors="coerce").fillna(0).astype(int)
        tmp["passives"] = pd.to_numeric(df.get(pacol, 0), errors="coerce").fillna(0).astype(int)
        tmp["detractors"] = pd.to_numeric(df.get(dcol, 0), errors="coerce").fillna(0).astype(int)
        tmp["axis_total_responses"] = pd.to_numeric(df[tcol], errors="coerce").fillna(0).astype(int)
        tmp["recalc_nps"] = pd.to_numeric(df[nps_col], errors="coerce")
        tmp["sample_grade"] = tmp["axis_total_responses"].apply(sample_grade)
        tmp["risk_count"] = tmp["passives"] + tmp["detractors"]
        tmp["sample_warning"] = tmp.apply(
            lambda r: (
                f"{axis_label} 응답 {int(r['axis_total_responses'])}건: n<{min_sample}라 점수 확정 판단보다 추가 샘플 확보 우선"
                if int(r["axis_total_responses"]) < min_sample
                else f"{axis_label} 응답 {int(r['axis_total_responses'])}건: 목표 미달/리스크 신호는 있으나 표본이 작아 추세 확인 필요"
            ),
            axis=1,
        )
        rows.append(tmp)
    if not rows:
        return pd.DataFrame()
    out = pd.concat(rows, ignore_index=True)
    mask = (out["axis_total_responses"] > 0) & (
        (out["axis_total_responses"] < min_sample)
        | ((out["axis_total_responses"] < 10) & ((out["recalc_nps"] < target_score) | (out["risk_count"] > 0)))
    )
    out = out[mask].copy()
    return out.sort_values(["axis_total_responses", "risk_count", "recalc_nps"], ascending=[True, False, True])


def build_store_daily_heatmap(response_fact: pd.DataFrame, team: str = "전북", axis: str = "비판매성") -> pd.DataFrame:
    """Build date × store NPS heatmap data.

    The heatmap is response-ledger based. It shows whether risk is concentrated in
    one store, one agency cluster, or one operating date before the user opens the
    detailed table.
    """
    df = _prepare_team_response_fact(response_fact, team)
    if df.empty:
        return pd.DataFrame()
    if axis != "종합" and "NCSI" in df.columns:
        df = df[df["NCSI"].astype(str).str.strip().eq(axis)].copy()
    if df.empty:
        return pd.DataFrame()
    for c in ["agency_name", "store_code", "store_name"]:
        if c not in df.columns:
            df[c] = ""
    out = (
        df.groupby(["trend_date", "agency_name", "store_code", "store_name"], dropna=False)
        .agg(
            promoters=("promoter_flag", "sum"),
            passives=("passive_flag", "sum"),
            detractors=("detractor_flag", "sum"),
            total_responses=("promoter_flag", "size"),
        )
        .reset_index()
    )
    out["axis"] = axis
    out["nps"] = out.apply(lambda r: nps_score(r.promoters, r.detractors, r.total_responses), axis=1)
    out["risk_count"] = out["passives"] + out["detractors"]
    out["risk_rate"] = out["risk_count"] / out["total_responses"].where(out["total_responses"] != 0, pd.NA)
    return out.sort_values(["trend_date", "agency_name", "store_name"])


def _extract_response_datetime(df: pd.DataFrame) -> pd.Series:
    """Return best-effort customer visit/process datetime for time-bucket hotspots.

    Current NPS workbooks often expose only dates. Future files may add a timestamp
    column; this helper accepts common Korean/English names and also preserves hour
    and minute if existing process/evaluation date columns contain them.
    """
    candidate_cols = [
        "visit_datetime", "visit_time", "process_datetime", "process_time", "response_datetime", "response_time",
        "고객방문일시", "고객방문시간", "방문일시", "방문시간", "처리일시", "처리시간", "응답일시", "응답시간",
        "process_date", "evaluation_date", "report_date",
    ]
    for c in candidate_cols:
        if c in df.columns:
            s = pd.to_datetime(df[c], errors="coerce")
            if s.notna().any():
                return s
    return pd.Series(pd.NaT, index=df.index)


def _time_bucket(ts: pd.Timestamp | Any) -> str:
    if pd.isna(ts):
        return "시간정보 없음"
    timestamp = pd.Timestamp(ts)
    if timestamp.time() == pd.Timestamp("00:00:00").time():
        return "시간정보 없음"
    hour = int(timestamp.hour)
    if 9 <= hour < 12:
        return "오전(09-12)"
    if 12 <= hour < 14:
        return "점심(12-14)"
    if 14 <= hour < 17:
        return "오후(14-17)"
    if 17 <= hour < 21:
        return "저녁(17-21)"
    return "기타시간"


def build_weekday_time_hotspots(response_fact: pd.DataFrame, team: str = "전북", axis: str = "비판매성") -> pd.DataFrame:
    """Build weekday × 4 time-bucket workload/risk hotspot data.

    If the source only has dates, rows are returned with `has_time_detail=False` and
    `time_bucket='시간정보 없음'`. The dashboard then shows the data-contract message
    instead of pretending a four-bucket visit pattern exists.
    """
    df = _prepare_team_response_fact(response_fact, team)
    if df.empty:
        return pd.DataFrame()
    if axis != "종합" and "NCSI" in df.columns:
        df = df[df["NCSI"].astype(str).str.strip().eq(axis)].copy()
    if df.empty:
        return pd.DataFrame()
    dt = _extract_response_datetime(df)
    df = df.assign(response_datetime=dt)
    df["weekday_idx"] = df["trend_date"].dt.weekday
    weekday_map = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"}
    df["weekday"] = df["weekday_idx"].map(weekday_map)
    df["time_bucket"] = df["response_datetime"].apply(_time_bucket)
    midnight = pd.Timestamp("00:00:00").time()
    df["has_time_detail"] = df["response_datetime"].notna() & df["response_datetime"].dt.time.ne(midnight)
    out = (
        df.groupby(["weekday_idx", "weekday", "time_bucket", "has_time_detail"], dropna=False)
        .agg(
            promoters=("promoter_flag", "sum"),
            passives=("passive_flag", "sum"),
            detractors=("detractor_flag", "sum"),
            total_responses=("promoter_flag", "size"),
        )
        .reset_index()
    )
    out["axis"] = axis
    out["nps"] = out.apply(lambda r: nps_score(r.promoters, r.detractors, r.total_responses), axis=1)
    out["risk_count"] = out["passives"] + out["detractors"]
    nps_for_score = pd.to_numeric(out["nps"], errors="coerce").fillna(100).clip(upper=87)
    out["hotspot_score"] = out["total_responses"] + out["risk_count"] * 3 + (87 - nps_for_score) / 20
    return out.sort_values(["weekday_idx", "time_bucket"])


def build_store_action_sheet(store_priority: pd.DataFrame, negative: pd.DataFrame, target_score: float) -> pd.DataFrame:
    base = build_non_sales_drilldown(store_priority, target_score).copy()
    neg = add_voc_classification(negative)
    if not neg.empty:
        neg["store_code"] = neg.get("store_code", "").astype(str).str.strip()
        # Store-level risk summary from corrected VOC table.
        risk = (
            neg.groupby(["store_code", "business_type", "voc_category"], dropna=False)
            .size()
            .reset_index(name="risk_count")
            .sort_values(["store_code", "risk_count"], ascending=[True, False])
        )
        top_risk = risk.groupby("store_code", as_index=False).head(1).rename(
            columns={"business_type": "top_business_type", "voc_category": "top_voc_category", "risk_count": "top_risk_count"}
        )[["store_code", "top_business_type", "top_voc_category", "top_risk_count"]]
        rep = (
            neg.sort_values(["store_code", "response_type", "recommend_score"], ascending=[True, True, True])
            .groupby("store_code", as_index=False)
            .first()[["store_code", "reason_text", "coaching_hint"]]
            .rename(columns={"reason_text": "representative_voc", "coaching_hint": "coaching_hint"})
        )
        if "store_code" not in base.columns:
            base = base.merge(store_priority[["store_code", "store_name"]].drop_duplicates(), on="store_name", how="left")
        base["store_code"] = base["store_code"].astype(str).str.strip()
        base = base.merge(top_risk, on="store_code", how="left").merge(rep, on="store_code", how="left")
    else:
        base["top_business_type"] = pd.NA
        base["top_voc_category"] = pd.NA
        base["top_risk_count"] = 0
        base["representative_voc"] = pd.NA
        base["coaching_hint"] = pd.NA
    base["이번주_액션"] = base.apply(build_weekly_action, axis=1)
    # Backward-compatible alias for older exports/dashboard code.
    base["이번주_확인사항"] = base["이번주_액션"]
    out_cols = [
        "agency_name", "store_code", "store_name", "axis_nps", "axis_target_gap", "axis_required_promoters", "axis_total_responses",
        "axis_passives", "axis_detractors", "top_business_type", "top_voc_category", "top_risk_count",
        "representative_voc", "이번주_액션", "이번주_확인사항", "axis_priority_score",
    ]
    return base[[c for c in out_cols if c in base.columns]].sort_values("axis_priority_score", ascending=False)


# Diagnosis types that get a single-store Action Card (priority order).
ACTION_CARD_TYPES = ["즉시 개선형", "비판매성 취약형", "구조 개선형"]

# "No-issue" passive comments ("불편한 점 없었습니다", "불편하지 않았습니다" 류) are not usable
# evidence on a care card. The negated subject (불편/문제/이상) must be matched so genuine
# complaints like "친절하지 않았어요"(=불친절) survive.
NO_ISSUE_RE = re.compile(r"없었|없어요|없습니다|없음|괜찮|만족스러|(?:불편|문제|이상|특별히|딱히).{0,5}(?:없|않)")


def build_store_daily_lookup(response_fact: pd.DataFrame, team: str = "전북") -> dict:
    """Per-store recent-7-day and latest-day NPS inputs from the response ledger.

    Returns {store_code: {"today": (promoters, detractors, total),
                          "recent7": (promoters, detractors, total),
                          "ns_today": (promoters, detractors, total),   # 비판매성 only
                          "ns_recent7": (promoters, detractors, total)}}.
    Latest day = max 업무처리일자 in the ledger; recent7 = trailing 7-day window ending there.
    """
    df = _prepare_team_response_fact(response_fact, team)
    if df.empty or "store_code" not in df.columns:
        return {}
    df = df.copy()
    df["store_code"] = df["store_code"].astype(str).str.strip()
    max_date = df["trend_date"].max()
    recent7_start = max_date - pd.Timedelta(days=6)
    ns_df = df[df["NCSI"].astype(str).str.strip().eq("비판매성")].copy() if "NCSI" in df.columns else pd.DataFrame(columns=df.columns)
    ns_groups: dict[str, pd.DataFrame] = {}
    if not ns_df.empty and "store_code" in ns_df.columns:
        for code, g in ns_df.groupby("store_code"):
            ns_groups[str(code).strip()] = g
    out: dict[str, dict[str, tuple[int, int, int]]] = {}
    for code, g in df.groupby("store_code"):
        today = g[g["trend_date"].eq(max_date)]
        recent = g[g["trend_date"].ge(recent7_start)]
        ns_g = ns_groups.get(str(code), pd.DataFrame())
        ns_today = ns_g[ns_g["trend_date"].eq(max_date)] if not ns_g.empty else pd.DataFrame()
        ns_recent = ns_g[ns_g["trend_date"].ge(recent7_start)] if not ns_g.empty else pd.DataFrame()
        out[code] = {
            "today": (int(today["promoter_flag"].sum()), int(today["detractor_flag"].sum()), int(len(today))),
            "recent7": (int(recent["promoter_flag"].sum()), int(recent["detractor_flag"].sum()), int(len(recent))),
            "ns_today": (int(ns_today["promoter_flag"].sum()), int(ns_today["detractor_flag"].sum()), int(len(ns_today))) if not ns_today.empty else (0, 0, 0),
            "ns_recent7": (int(ns_recent["promoter_flag"].sum()), int(ns_recent["detractor_flag"].sum()), int(len(ns_recent))) if not ns_recent.empty else (0, 0, 0),
        }
    return out


def _nps_from_counts(promoters: int, detractors: int, total: int) -> float | None:
    return nps_score(promoters, detractors, total) if total else None


def _trend_arrow(month: float | None, recent7: float | None, today: float | None) -> str:
    """Direction of the most recent movement vs the month baseline."""
    latest = today if today is not None else recent7
    if latest is None or month is None or pd.isna(latest) or pd.isna(month):
        return "–"
    if latest < month - 1:
        return "▼"
    if latest > month + 1:
        return "▲"
    return "→"


def _card_business_top(scope: pd.DataFrame, limit: int = 3) -> list[tuple[str, int]]:
    if scope.empty or "business_type" not in scope.columns:
        return []
    bt = (
        scope.assign(business_type=scope["business_type"].fillna("미분류").astype(str).str.strip().replace("", "미분류"))
        .groupby("business_type")
        .size()
        .sort_values(ascending=False)
        .head(limit)
    )
    return [(str(k), int(v)) for k, v in bt.items()]


def _card_actions(dtype: str, ctx: dict) -> tuple[list[str], str, str]:
    """Rule-based, type-specific action checklist + quantitative goal + verify metric."""
    top_biz = ctx["top_biz"]
    top_voc = ctx["top_voc"]
    detractors = ctx["detractors"]
    passives = ctx["passives"]
    req = ctx["req"]
    rep_voc = ctx["rep_voc"]
    hint = ctx["coaching_hint"]
    risk_count = ctx["risk_count"]
    non_sales_nps = ctx["non_sales_nps"]
    target = ctx["target"]

    actions: list[str] = []
    if dtype == "즉시 개선형":
        actions.append(f"{top_biz} 비추천 {detractors}건 전수 확인 — {top_voc} 기준 처리완료·안내 멘트 재점검")
        if rep_voc:
            actions.append(f"“{rep_voc[:45]}” 케이스 직접 클로징")
        quant = f"비추천 {detractors} → 0  (필요추천 {req}건이면 목표 도달)"
        verify = "다음주 동일 업무유형 비추천 0건"
    elif dtype == "비판매성 취약형":
        actions.append(f"{top_biz} 중립 {passives}건 추천 전환 — 설명 누락·대기 안내·마무리 확인 점검")
        actions.append(f"비판매 응대 루틴 1개 표준화 (코칭: {hint})")
        ns = f"{float(non_sales_nps):.0f}" if non_sales_nps is not None and pd.notna(non_sales_nps) else "-"
        if passives > 0:
            quant = f"추천 {req}건 확보 시 목표 — 중립 {passives}건 우선 전환 대상"
        else:
            quant = f"추천 {req}건 확보 시 목표 도달"
        verify = f"비판매성 NPS {ns} → {target:.0f}"
    else:  # 구조 개선형
        actions.append("판매성·비판매성 동시 약점 — 대리점 단위 합동 점검 요청")
        actions.append(f"{top_biz} 포함 Risk {risk_count}건 원인 분류 (응대/처리/대기)")
        quant = f"이달 {req}건 + 다음달 분할 — 단월 회복 아님, 2개월 로드맵"
        verify = "양축 목표Gap 동시 축소 여부"
    return actions, quant, verify


def build_store_action_card(store_row: pd.Series, store_negative: pd.DataFrame, daily_lookup: dict, target_score: float) -> dict:
    """Build a single-store Action Card payload (4-zone) for the type-grouped UI."""
    code = str(store_row.get("store_code", "")).strip()
    dtype = str(store_row.get("diagnosis_type", ""))
    neg = store_negative.copy() if store_negative is not None else pd.DataFrame()

    # ② state
    month_nps = store_row.get("nps_recalc")
    month_nps = float(month_nps) if pd.notna(month_nps) else None
    daily = daily_lookup.get(code, {})
    r7p, r7d, r7t = daily.get("recent7", (0, 0, 0))
    tdp, tdd, tdt = daily.get("today", (0, 0, 0))
    recent7_nps = _nps_from_counts(r7p, r7d, r7t)
    today_nps = _nps_from_counts(tdp, tdd, tdt)
    detractors = int(store_row.get("detractors", 0) or 0)
    passives = int(store_row.get("passives", 0) or 0)
    promoters = int(store_row.get("promoters", 0) or 0)
    total = int(store_row.get("total_responses", 0) or 0)
    req = int(store_row.get("required_promoters_to_target", 0) or 0)
    non_sales_nps = store_row.get("non_sales_nps_recalc")
    non_sales_nps = float(non_sales_nps) if pd.notna(non_sales_nps) else None
    sales_nps = store_row.get("sales_nps_recalc")
    sales_nps = float(sales_nps) if pd.notna(sales_nps) else None

    # ② non-sales time-intelligence
    nsr7p, nsr7d, nsr7t = daily.get("ns_recent7", (0, 0, 0))
    nstdp, nstdd, nstdt = daily.get("ns_today", (0, 0, 0))
    ns_recent7_nps = _nps_from_counts(nsr7p, nsr7d, nsr7t)
    ns_today_nps = _nps_from_counts(nstdp, nstdd, nstdt)

    # ③ evidence — business type scope is type-specific
    if dtype == "즉시 개선형" and not neg.empty and "response_type" in neg.columns:
        scope = neg[neg["response_type"].astype(str).str.strip().eq("비추천")]
    else:
        scope = neg
    top_business_types = _card_business_top(scope)
    top_biz = top_business_types[0][0] if top_business_types else "비판매성 업무"

    # representative VOC — drop 무의미/내용없음, lowest recommend_score first
    rep_vocs: list[dict] = []
    top_voc = "VOC 사유"
    coaching_hint = "중립/비추천 발생 업무유형과 응대 프로세스 확인"
    if not neg.empty and "reason_text" in neg.columns:
        meaningful = neg.copy()
        if "voc_category" in meaningful.columns:
            meaningful = meaningful[meaningful["voc_category"].astype(str).ne("무의미/내용없음")]
        txt = meaningful["reason_text"].astype(str).str.strip()
        meaningful = meaningful[txt.ne("") & ~txt.str.contains(NO_ISSUE_RE)]
        if not meaningful.empty:
            # Surface real detractors first, then the lowest recommend_score.
            is_det = meaningful.get("response_type", pd.Series(index=meaningful.index, dtype=object)).astype(str).str.strip().eq("비추천")
            meaningful = meaningful.assign(
                _isdet=is_det.astype(int),
                _score=pd.to_numeric(meaningful.get("recommend_score"), errors="coerce"),
            )
            meaningful = meaningful.sort_values(["_isdet", "_score"], ascending=[False, True], na_position="last")
            top_voc = _safe_text(meaningful.iloc[0].get("voc_category"), top_voc)
            coaching_hint = _safe_text(meaningful.iloc[0].get("coaching_hint"), coaching_hint)
            for _, rr in meaningful.head(2).iterrows():
                rep_vocs.append({
                    "text": _safe_text(rr.get("reason_text")),
                    "business_type": _safe_text(rr.get("business_type"), "업무"),
                    "voc_category": _safe_text(rr.get("voc_category"), "기타"),
                })

    actions, quant_goal, verify_metric = _card_actions(dtype, {
        "top_biz": top_biz, "top_voc": top_voc, "detractors": detractors, "passives": passives,
        "req": req, "rep_voc": rep_vocs[0]["text"] if rep_vocs else "", "coaching_hint": coaching_hint,
        "risk_count": passives + detractors, "non_sales_nps": non_sales_nps, "target": target_score,
    })

    return {
        "store_name": _safe_text(store_row.get("store_name"), "매장"),
        "agency_name": _safe_text(store_row.get("agency_name"), "대리점"),
        "marketer": _safe_text(store_row.get("marketer"), "-"),
        "store_code": code,
        "diagnosis_type": dtype,
        "care_priority": float(store_row.get("priority_score", 0) or 0),
        "sample_confidence": float(store_row.get("sample_confidence", 1) or 1),
        "month_nps": month_nps,
        "recent7_nps": recent7_nps, "recent7_n": int(r7t),
        "today_nps": today_nps, "today_n": int(tdt),
        "ns_recent7_nps": ns_recent7_nps, "ns_recent7_n": int(nsr7t),
        "ns_today_nps": ns_today_nps, "ns_today_n": int(nstdt),
        "trend_arrow": _trend_arrow(month_nps, recent7_nps, today_nps),
        "target_gap": (month_nps - target_score) if month_nps is not None else None,
        "non_sales_gap": (non_sales_nps - target_score) if non_sales_nps is not None else None,
        "sales_gap": (sales_nps - target_score) if sales_nps is not None else None,
        "promoters": promoters, "passives": passives, "detractors": detractors, "total": total,
        "sales_nps": sales_nps, "non_sales_nps": non_sales_nps,
        "top_business_types": top_business_types,
        "representative_vocs": rep_vocs,
        "actions": actions, "quant_goal": quant_goal, "verify_metric": verify_metric,
    }
