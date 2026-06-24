from __future__ import annotations

import math

import pandas as pd


def nps_score(promoters: float, detractors: float, total: float) -> float | None:
    if total is None or pd.isna(total) or total == 0:
        return None
    return (promoters - detractors) / total * 100


def normalize_nps_series(s: pd.Series) -> pd.Series:
    """Normalize NPS values to the dashboard standard -100~100 score scale.

    The operating Excel aggregate sheets can store NPS as either a ratio
    (-1~1) or a score (-100~100). Any numeric value with ``abs(value) <= 1``
    is treated as a ratio and multiplied by 100. Missing/non-numeric values are
    preserved as NaN.
    """
    numeric = pd.to_numeric(s, errors="coerce")
    return numeric.where(numeric.abs() > 1, numeric * 100)


def required_promoters_to_target(promoters: int, passives: int, detractors: int, target_score: float = 87.0) -> int:
    """Return additional promoter responses required to reach target NPS.

    Assumes each additional response is a promoter. Target is expressed as 0~100.
    Solve: (P + x - D) / (T + x) * 100 >= target
    """
    total = promoters + passives + detractors
    if total <= 0:
        return 0
    current = nps_score(promoters, detractors, total)
    if current is not None and current >= target_score:
        return 0
    t = target_score / 100
    denom = 1 - t
    if denom <= 0:
        return 0
    x = (t * total - promoters + detractors) / denom
    return max(0, math.ceil(x))


def sample_grade(total: float) -> str:
    if pd.isna(total) or total <= 0:
        return "무응답"
    if total < 5:
        return "샘플부족"
    if total < 10:
        return "주의"
    if total < 20:
        return "보통"
    return "충분"


def diagnose_store(row: pd.Series, target_score: float = 87.0) -> str:
    """Classify stores for field action.

    Rule order matters. We avoid labeling every below-target store as "구조 개선형";
    that category is reserved for enough-sample stores where both sales/non-sales axes
    are weak and there is a meaningful risk count.
    """
    total = row.get("total_responses", 0) or 0
    nps = row.get("nps_recalc", row.get("nps_score"))
    detractors = row.get("detractors", 0) or 0
    passives = row.get("passives", 0) or 0
    req = row.get("required_promoters_to_target", 0) or 0
    sales = row.get("sales_nps_recalc", row.get("sales_nps_score"))
    non_sales = row.get("non_sales_nps_recalc", row.get("non_sales_nps_score"))
    risk_count = passives + detractors

    if total < 5:
        return "샘플 착시형"
    if detractors >= 2:
        return "즉시 개선형"
    if nps is not None and pd.notna(nps) and nps >= target_score and total >= 10:
        return "우수 확산형"
    if pd.notna(non_sales) and non_sales < target_score and (pd.isna(sales) or sales >= target_score):
        return "비판매성 취약형"
    if pd.notna(sales) and sales < target_score and (pd.isna(non_sales) or non_sales >= target_score):
        return "판매성 취약형"
    if total >= 10 and risk_count >= 2 and pd.notna(sales) and pd.notna(non_sales) and sales < target_score and non_sales < target_score:
        return "구조 개선형"
    if nps is not None and pd.notna(nps) and nps < target_score and passives > 0 and req <= 10:
        return "회복 가능형"
    if nps is not None and pd.notna(nps) and nps < target_score and detractors > 0:
        return "즉시 개선형"
    return "관찰/유지형"


def build_store_priority(store_agg: pd.DataFrame, team: str = "전북", target_score: float = 87.0) -> pd.DataFrame:
    df = store_agg.copy()
    if "team_name" in df.columns:
        df = df[df["team_name"].astype(str).str.strip().eq(team)].copy()
    for c in ["promoters", "passives", "detractors", "total_responses"]:
        df[c] = pd.to_numeric(df.get(c, 0), errors="coerce").fillna(0).astype(int)
    for c in ["nps_score", "prev_nps_score", "hq_nps_score", "sales_nps_score", "non_sales_nps_score"]:
        if c in df.columns:
            df[c] = normalize_nps_series(df[c])
    for prefix in ["sales_", "non_sales_"]:
        count_cols = [f"{prefix}promoters", f"{prefix}passives", f"{prefix}detractors", f"{prefix}total_responses"]
        for c in count_cols:
            if c not in df.columns:
                df[c] = 0
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
        df[f"{prefix}nps_recalc"] = df.apply(
            lambda r, p=prefix: nps_score(r[f"{p}promoters"], r[f"{p}detractors"], r[f"{p}total_responses"]),
            axis=1,
        )
    df["nps_recalc"] = df.apply(lambda r: nps_score(r.promoters, r.detractors, r.total_responses), axis=1)
    df["target_gap"] = df["nps_recalc"] - target_score
    df["required_promoters_to_target"] = df.apply(lambda r: required_promoters_to_target(r.promoters, r.passives, r.detractors, target_score), axis=1)
    df["sample_grade"] = df["total_responses"].apply(sample_grade)
    df["risk_count"] = df["passives"] + df["detractors"]
    df["diagnosis_type"] = df.apply(lambda r: diagnose_store(r, target_score), axis=1)
    # Higher priority: enough responses, detractors/risk, target gap, required promoters.
    df["priority_score"] = (
        df["detractors"] * 10
        + df["passives"] * 3
        + df["required_promoters_to_target"] * 2
        + (df["total_responses"].clip(upper=30) / 10)
        + (-df["target_gap"].clip(upper=0) / 10)
    )
    return df.sort_values(["priority_score", "detractors", "total_responses"], ascending=[False, False, False])


def summarize_team_from_response(response_fact: pd.DataFrame, team: str = "전북") -> dict[str, float | int | str]:
    df = response_fact.copy()
    if "team_name" in df.columns:
        df = df[df["team_name"].astype(str).str.strip().eq(team)].copy()
    promoters = int(pd.to_numeric(df.get("promoter_flag", 0), errors="coerce").fillna(0).sum())
    passives = int(pd.to_numeric(df.get("passive_flag", 0), errors="coerce").fillna(0).sum())
    detractors = int(pd.to_numeric(df.get("detractor_flag", 0), errors="coerce").fillna(0).sum())
    total = promoters + passives + detractors
    return {
        "team": team,
        "promoters": promoters,
        "passives": passives,
        "detractors": detractors,
        "total_responses": total,
        "nps_score": nps_score(promoters, detractors, total),
        "store_count": int(df["store_code"].nunique()) if "store_code" in df.columns else 0,
        "agency_count": int(df["agency_name"].nunique()) if "agency_name" in df.columns else 0,
    }
