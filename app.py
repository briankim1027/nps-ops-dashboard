from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    import streamlit as st
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
except ModuleNotFoundError as e:  # Allows py_compile in minimal environments.
    missing = e.name
    print(f"Missing optional dashboard dependency: {missing}. Install with `pip install -r requirements.txt`.")
    raise

from nps_ops.config import DEFAULT_TARGET_SCORE, DEFAULT_TEAM, PROCESSED_DIR
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
    build_store_non_sales_trend,
)
from nps_ops.metrics import required_promoters_to_target, sample_grade


st.set_page_config(page_title="전북팀 NPS 운영 Dashboard", layout="wide", page_icon="📡")

SKT_CSS = """
<style>
:root {
  --skt-purple:#815CF6;
  --skt-orange:#DC6339;
  --skt-magenta:#C045F6;
  --skt-yellow:#E0CD4E;
  --skt-green:#5FCE73;
  --skt-deep-bg:#0D0E1A;
  --skt-deep-bg-2:#141528;
  --skt-card:#FFFFFF;
  --skt-soft:#F5F3FF;
  --skt-line:#E8E8F2;
  --skt-text:#1A1A1A;
  --skt-muted:#666678;
}
html, body, [class*="css"] {font-family:'Noto Sans KR','SKT Sans Text','Apple SD Gothic Neo',sans-serif;}
.stApp {background:linear-gradient(180deg,#F7F5FF 0%,#FFFFFF 36%,#FAFAFC 100%); color:var(--skt-text);}
.block-container {padding-top:1.4rem; padding-bottom:3rem; max-width:1480px;}
.skt-hero {
  padding:28px 32px; border-radius:28px; color:white; margin-bottom:22px;
  background:
    radial-gradient(circle at 12% 10%, rgba(224,205,78,.38), transparent 25%),
    radial-gradient(circle at 84% 0%, rgba(192,69,246,.46), transparent 30%),
    linear-gradient(135deg,#0D0E1A 0%,#231653 47%,#815CF6 100%);
  box-shadow:0 22px 50px rgba(129,92,246,.28);
}
.skt-eyebrow {font-size:12px; font-weight:800; letter-spacing:.12em; color:#E0CD4E; margin-bottom:8px;}
.skt-title {font-size:34px; font-weight:900; letter-spacing:-.035em; margin:0 0 8px 0;}
.skt-subtitle {font-size:15px; color:rgba(255,255,255,.82); margin:0;}
.skt-card-grid {display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:14px; margin:8px 0 22px 0;}
.skt-metric-card {
  background:rgba(255,255,255,.94); border:1px solid rgba(129,92,246,.14); border-radius:22px;
  padding:18px 18px 16px 18px; box-shadow:0 10px 28px rgba(13,14,26,.08);
  position:relative; overflow:hidden; min-height:112px;
}
.skt-metric-card:before {content:""; position:absolute; inset:0 0 auto 0; height:5px; background:linear-gradient(90deg,#815CF6,#C045F6,#DC6339);}
.skt-metric-card.focus:before {background:linear-gradient(90deg,#DC6339,#E0CD4E);}
.skt-label {font-size:12px; font-weight:800; color:var(--skt-muted); letter-spacing:.03em; margin-bottom:8px;}
.skt-value {font-size:30px; line-height:1; font-weight:900; letter-spacing:-.04em; color:var(--skt-text);}
.skt-note {font-size:12px; color:var(--skt-muted); margin-top:8px;}
.skt-section-title {font-size:22px; font-weight:900; letter-spacing:-.03em; margin-top:20px; margin-bottom:4px;}
.skt-section-caption {font-size:13px; color:var(--skt-muted); margin-bottom:12px;}
div[data-testid="stMetric"] {background:white; border:1px solid var(--skt-line); border-radius:18px; padding:14px 16px; box-shadow:0 6px 18px rgba(13,14,26,.06);}
.stTabs [data-baseweb="tab-list"] {gap:8px; background:#F0EDFF; padding:6px; border-radius:16px;}
.stTabs [data-baseweb="tab"] {border-radius:12px; padding:9px 16px; font-weight:800; color:#4F46A5;}
.stTabs [aria-selected="true"] {background:#815CF6 !important; color:white !important;}
[data-testid="stDataFrame"] {border-radius:18px; overflow:hidden; border:1px solid var(--skt-line); box-shadow:0 8px 24px rgba(13,14,26,.05);}
.skt-help-box {background:#FFFFFF; border:1px solid var(--skt-line); border-radius:20px; padding:16px 18px; box-shadow:0 8px 24px rgba(13,14,26,.06); margin:8px 0 16px 0;}
.skt-help-title {font-size:16px; font-weight:900; margin:0 0 10px 0; color:#1A1A1A;}
.skt-help-grid {display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px 16px;}
.skt-help-item {display:flex; align-items:flex-start; gap:10px; margin-top:10px; font-size:13px; line-height:1.55; color:#333344;}
.skt-help-text {flex:1; padding-top:2px;}
.skt-chip {display:inline-block; flex:0 0 88px; min-width:88px; text-align:center; border-radius:999px; padding:4px 10px; margin-right:0; font-size:12px; font-weight:900; color:white; background:#815CF6;}
.skt-chip.orange {background:#DC6339;}.skt-chip.yellow {background:#B89B00;}.skt-chip.green {background:#249A45;}.skt-chip.gray {background:#6B7280;}.skt-chip.magenta {background:#C045F6;}
.skt-formula {font-family:'JetBrains Mono','Courier New',monospace; background:#F5F3FF; border-radius:12px; padding:10px 12px; font-size:13px; color:#231653; margin-top:8px;}
.skt-priority-note {font-size:12.5px; color:#4B4B5F; margin:8px 0 18px 0; line-height:1.55;}
.skt-priority-note .skt-formula {display:inline-block; margin:0 0 6px 0;}
@media (max-width:1100px) {.skt-help-grid {grid-template-columns:repeat(2,minmax(0,1fr));}}
@media (max-width:720px) {.skt-help-grid {grid-template-columns:1fr;}}
</style>
"""
st.markdown(SKT_CSS, unsafe_allow_html=True)


def fmt_score(v: float | int | None) -> str:
    if v is None or pd.isna(v):
        return "-"
    return f"{float(v):.2f}"


def axis_summary(df: pd.DataFrame, prefix: str = "") -> dict[str, float | int | None]:
    pcol = f"{prefix}promoters"
    pacol = f"{prefix}passives"
    dcol = f"{prefix}detractors"
    tcol = f"{prefix}total_responses"
    promoters = int(pd.to_numeric(df.get(pcol, 0), errors="coerce").fillna(0).sum())
    passives = int(pd.to_numeric(df.get(pacol, 0), errors="coerce").fillna(0).sum())
    detractors = int(pd.to_numeric(df.get(dcol, 0), errors="coerce").fillna(0).sum())
    total = int(pd.to_numeric(df.get(tcol, promoters + passives + detractors), errors="coerce").fillna(0).sum())
    nps = ((promoters - detractors) / total * 100) if total else None
    return {"promoters": promoters, "passives": passives, "detractors": detractors, "total": total, "nps": nps}


def prepare_axis_table(priority: pd.DataFrame, axis: str, target_score: float) -> pd.DataFrame:
    axis_map = {
        "종합 NPS": ("", "종합 NPS"),
        "판매성 NPS": ("sales_", "판매성 NPS"),
        "비판매성 NPS": ("non_sales_", "비판매성 NPS"),
    }
    prefix, label = axis_map[axis]
    df = priority.copy()
    pcol = f"{prefix}promoters"
    pacol = f"{prefix}passives"
    dcol = f"{prefix}detractors"
    tcol = f"{prefix}total_responses"
    for c in [pcol, pacol, dcol, tcol]:
        df[c] = pd.to_numeric(df.get(c, 0), errors="coerce").fillna(0).astype(int)
    df["선택축"] = label
    df["선택축_추천"] = df[pcol]
    df["선택축_중립"] = df[pacol]
    df["선택축_비추천"] = df[dcol]
    df["선택축_총응답자"] = df[tcol]
    df["선택축_NPS"] = df.apply(lambda r: ((r["선택축_추천"] - r["선택축_비추천"]) / r["선택축_총응답자"] * 100) if r["선택축_총응답자"] else None, axis=1)
    df["선택축_목표Gap"] = df["선택축_NPS"] - target_score
    df["선택축_필요추천수"] = df.apply(lambda r: required_promoters_to_target(r["선택축_추천"], r["선택축_중립"], r["선택축_비추천"], target_score), axis=1)
    df["선택축_샘플"] = df["선택축_총응답자"].apply(sample_grade)
    df["선택축_Risk"] = df["선택축_중립"] + df["선택축_비추천"]
    df["선택축_priority_score"] = (
        df["선택축_비추천"] * 10
        + df["선택축_중립"] * 3
        + df["선택축_필요추천수"] * 2
        + (df["선택축_총응답자"].clip(upper=30) / 10)
        + (-df["선택축_목표Gap"].clip(upper=0) / 10)
    )
    sort_cols = ["선택축_priority_score", "선택축_비추천", "선택축_총응답자"]
    return df.sort_values(sort_cols, ascending=[False, False, False])


team = st.sidebar.text_input("팀명", DEFAULT_TEAM)
target_score = st.sidebar.number_input("목표 NPS", min_value=0.0, max_value=100.0, value=float(DEFAULT_TARGET_SCORE), step=1.0)
priority_files = sorted(PROCESSED_DIR.glob(f"store_priority_{team}_*.parquet"), reverse=True)
response_files = sorted(PROCESSED_DIR.glob("response_fact_*.parquet"), reverse=True)
negative_files = sorted(PROCESSED_DIR.glob("negative_feedback_*.parquet"), reverse=True)
store_files = sorted(PROCESSED_DIR.glob("store_agg_*.parquet"), reverse=True)
crew_files = sorted(PROCESSED_DIR.glob("crew_agg_*.parquet"), reverse=True)
non_sales_files = sorted(PROCESSED_DIR.glob(f"non_sales_drilldown_{team}_*.parquet"), reverse=True)
action_sheet_files = sorted(PROCESSED_DIR.glob(f"store_action_sheet_{team}_*.parquet"), reverse=True)
non_sales_type_files = sorted(PROCESSED_DIR.glob(f"non_sales_business_type_top_{team}_*.parquet"), reverse=True)
non_sales_trend_files = sorted(PROCESSED_DIR.glob(f"store_non_sales_trend_{team}_*.parquet"), reverse=True)
sales_good_ns_weak_files = sorted(PROCESSED_DIR.glob(f"sales_good_non_sales_weak_{team}_*.parquet"), reverse=True)
nps_diff_files = sorted(PROCESSED_DIR.glob(f"nps_source_recalc_diff_{team}_*.parquet"), reverse=True)
sample_warning_files = sorted(PROCESSED_DIR.glob(f"sample_warning_{team}_*.parquet"), reverse=True)
daily_nps_trend_files = sorted(PROCESSED_DIR.glob(f"daily_nps_trend_{team}_*.parquet"), reverse=True)
nps_time_intelligence_files = sorted(PROCESSED_DIR.glob(f"nps_time_intelligence_{team}_*.parquet"), reverse=True)

if not priority_files:
    st.warning("처리된 데이터가 없습니다. 먼저 `bash scripts/run_build.sh`를 실행하세요.")
    st.stop()

priority = pd.read_parquet(priority_files[0])
response = pd.read_parquet(response_files[0]) if response_files else pd.DataFrame()
negative = pd.read_parquet(negative_files[0]) if negative_files else pd.DataFrame()
crew = pd.read_parquet(crew_files[0]) if crew_files else pd.DataFrame()
negative = add_voc_classification(negative) if not negative.empty and "voc_category" not in negative.columns else negative
non_sales_drilldown = pd.read_parquet(non_sales_files[0]) if non_sales_files else build_non_sales_drilldown(priority, target_score)
non_sales_business_type_top = pd.read_parquet(non_sales_type_files[0]) if non_sales_type_files else build_non_sales_business_type_top(response, team)
store_non_sales_trend = pd.read_parquet(non_sales_trend_files[0]) if non_sales_trend_files else build_store_non_sales_trend(response, team)
sales_good_non_sales_weak = pd.read_parquet(sales_good_ns_weak_files[0]) if sales_good_ns_weak_files else build_sales_good_non_sales_weak(priority, target_score)
nps_source_recalc_diff = pd.read_parquet(nps_diff_files[0]) if nps_diff_files else build_nps_source_recalc_diff(priority)
sample_warning = pd.read_parquet(sample_warning_files[0]) if sample_warning_files else build_sample_warning(priority, target_score)
daily_nps_trend = pd.read_parquet(daily_nps_trend_files[0]) if daily_nps_trend_files else build_daily_nps_trend(response, team)
nps_time_intelligence = build_nps_time_intelligence(response, team, target_score, report_date=None) if not response.empty else (pd.read_parquet(nps_time_intelligence_files[0]) if nps_time_intelligence_files else pd.DataFrame())
action_sheet = pd.read_parquet(action_sheet_files[0]) if action_sheet_files else build_store_action_sheet(
    priority,
    negative[negative["team_name"].astype(str).str.strip().eq(team)] if not negative.empty and "team_name" in negative.columns else negative,
    target_score,
)
report_date = priority["report_date"].dropna().astype(str).iloc[0][:10] if "report_date" in priority.columns and priority["report_date"].notna().any() else priority_files[0].stem[-8:]

agency_options = sorted([str(x) for x in priority.get("agency_name", pd.Series(dtype=object)).dropna().unique()])
selected_agencies = st.sidebar.multiselect("대리점 필터", agency_options, default=[])
top10_only = st.sidebar.checkbox("Action Sheet TOP 10만 보기", value=False)


def apply_agency_filter(df: pd.DataFrame) -> pd.DataFrame:
    if not selected_agencies or df.empty or "agency_name" not in df.columns:
        return df
    return df[df["agency_name"].astype(str).isin(selected_agencies)].copy()

priority_view_base = apply_agency_filter(priority)
non_sales_drilldown_view_base = apply_agency_filter(non_sales_drilldown)
action_sheet_view_base = apply_agency_filter(action_sheet)
store_non_sales_trend_view_base = apply_agency_filter(store_non_sales_trend)
sales_good_non_sales_weak_view_base = apply_agency_filter(sales_good_non_sales_weak)
nps_source_recalc_diff_view_base = apply_agency_filter(nps_source_recalc_diff)
sample_warning_view_base = apply_agency_filter(sample_warning)

st.markdown(
    f"""
    <div class="skt-hero">
      <div class="skt-eyebrow">SK TELECOM · JEONBUK NPS OPS</div>
      <div class="skt-title">전북팀 NPS 운영 Dashboard</div>
      <p class="skt-subtitle">{report_date} 기준 · 종합/판매성/비판매성 NPS를 분리해 현장 코칭 우선순위로 전환</p>
    </div>
    """,
    unsafe_allow_html=True,
)

overall = axis_summary(priority, "")
sales = axis_summary(priority, "sales_")
non_sales = axis_summary(priority, "non_sales_")

st.markdown(
    f"""
    <div class="skt-card-grid">
      <div class="skt-metric-card"><div class="skt-label">NPS 종합</div><div class="skt-value">{fmt_score(overall['nps'])}</div><div class="skt-note">추천 {overall['promoters']:,} · 중립 {overall['passives']:,} · 비추천 {overall['detractors']:,}</div></div>
      <div class="skt-metric-card"><div class="skt-label">판매성 NPS</div><div class="skt-value">{fmt_score(sales['nps'])}</div><div class="skt-note">판매 상담/가입·기변 축</div></div>
      <div class="skt-metric-card focus"><div class="skt-label">비판매성 NPS</div><div class="skt-value">{fmt_score(non_sales['nps'])}</div><div class="skt-note">팀 평가 집중관리 축</div></div>
      <div class="skt-metric-card"><div class="skt-label">총응답자</div><div class="skt-value">{overall['total']:,}</div><div class="skt-note">판매성 {sales['total']:,} · 비판매성 {non_sales['total']:,}</div></div>
      <div class="skt-metric-card"><div class="skt-label">중립/비추천</div><div class="skt-value">{overall['passives'] + overall['detractors']:,}</div><div class="skt-note">중립 {overall['passives']:,} · 비추천 {overall['detractors']:,}</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)

trend_title_col, date_from_col, date_to_col = st.columns([0.58, 0.21, 0.21])
with trend_title_col:
    st.markdown('<div class="skt-section-title">6월 NPS Trend</div>', unsafe_allow_html=True)
    st.markdown('<div class="skt-section-caption">기본값은 6월 전체 기간입니다. 날짜를 조정해 주간/특정 기간 흐름도 함께 확인합니다.</div>', unsafe_allow_html=True)

if nps_time_intelligence.empty or daily_nps_trend.empty:
    st.info("NPS Trend 산출 데이터가 없습니다. `python scripts/build_data.py`를 다시 실행하세요.")
else:
    ti = nps_time_intelligence.iloc[0]
    week_start = pd.to_datetime(ti.get("week_start"), errors="coerce")
    week_end = pd.to_datetime(ti.get("week_end"), errors="coerce")
    trend = daily_nps_trend.copy()
    trend["trend_date"] = pd.to_datetime(trend["trend_date"], errors="coerce")
    trend = trend[trend["trend_date"].notna()].copy()

    min_trend_date = trend["trend_date"].min()
    max_trend_date = trend["trend_date"].max()
    default_start = min_trend_date
    default_end = max_trend_date
    default_start = max(default_start, min_trend_date)
    default_end = min(default_end, max_trend_date)

    with date_from_col:
        date_from = st.date_input(
            "Date from",
            value=default_start.date(),
            min_value=min_trend_date.date(),
            max_value=max_trend_date.date(),
            key="weekly_nps_date_from",
        )
    with date_to_col:
        date_to = st.date_input(
            "Date to",
            value=default_end.date(),
            min_value=min_trend_date.date(),
            max_value=max_trend_date.date(),
            key="weekly_nps_date_to",
        )

    if date_from > date_to:
        st.warning("Date from이 Date to보다 늦습니다. 날짜 범위를 다시 선택하세요.")
        weekly_trend = pd.DataFrame()
    else:
        start_ts = pd.Timestamp(date_from)
        end_ts = pd.Timestamp(date_to)
        weekly_trend = trend[(trend["trend_date"] >= start_ts) & (trend["trend_date"] <= end_ts)].copy()

    if weekly_trend.empty:
        st.info("선택 기간의 NPS 흐름 데이터가 없습니다.")
    else:
        weekly_trend["trend_label"] = weekly_trend["trend_date"].dt.strftime("%m/%d")
        x_order = weekly_trend.sort_values("trend_date")["trend_label"].drop_duplicates().tolist()
        fig = go.Figure()
        colors = {"종합": "#815CF6", "판매성": "#249A45", "비판매성": "#DC6339"}
        for axis in ["판매성", "비판매성"]:
            sub = weekly_trend[weekly_trend["axis"].eq(axis)].sort_values("trend_date")
            if not sub.empty:
                fig.add_trace(go.Bar(
                    x=sub["trend_label"], y=sub["total_responses"], name=f"{axis} 응답건수",
                    marker_color=colors[axis], opacity=0.30, yaxis="y2", width=0.24,
                    customdata=sub["trend_date"].dt.strftime("%Y-%m-%d"),
                    hovertemplate="%{customdata}<br>응답건수=%{y:,}<extra>%{fullData.name}</extra>",
                ))
        for axis in ["종합", "판매성", "비판매성"]:
            sub = weekly_trend[weekly_trend["axis"].eq(axis)].sort_values("trend_date")
            if not sub.empty:
                fig.add_trace(go.Scatter(
                    x=sub["trend_label"], y=sub["nps"], name=f"{axis} NPS",
                    mode="lines+markers",
                    line=dict(color=colors[axis], width=4 if axis in {"종합", "비판매성"} else 2.4, dash="solid" if axis == "종합" else "dot"),
                    marker=dict(size=8 if axis == "종합" else 6),
                    customdata=sub["trend_date"].dt.strftime("%Y-%m-%d"),
                    hovertemplate="%{customdata}<br>NPS=%{y:.1f}<extra>%{fullData.name}</extra>",
                ))
        fig.add_trace(go.Scatter(
            x=x_order, y=[target_score] * len(x_order), name=f"목표 {target_score:.0f}",
            mode="lines", line=dict(color="#111111", width=3, dash="solid"),
            hovertemplate=f"목표 NPS={target_score:.0f}<extra></extra>",
        ))
        min_nps = pd.to_numeric(weekly_trend["nps"], errors="coerce").min()
        y_min = 0 if pd.isna(min_nps) or min_nps >= 0 else max(-100, float(min_nps) - 5)
        nps_axis_top = 115 if y_min >= 0 else 105
        fig.update_layout(
            barmode="group", bargap=0.42, bargroupgap=0.18,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title="업무처리일자", yaxis_title="NPS", legend_title_text=None,
            yaxis=dict(range=[y_min, nps_axis_top], gridcolor="rgba(148,163,184,0.20)"),
            yaxis2=dict(title="응답건수", overlaying="y", side="right", showgrid=False, rangemode="tozero"),
            xaxis=dict(type="category", categoryorder="array", categoryarray=x_order),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=48, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        f"""
        <div class="skt-help-box">
          <div class="skt-help-title">{ti.get('headline', '동적 해석메시지')}</div>
          <div class="skt-help-item"><span class="skt-chip">이번 주 판세</span><span class="skt-help-text">{ti.get('weekly_situation', ti.get('narrative', '-'))}</span></div>
          <div class="skt-help-item"><span class="skt-chip magenta">최근 변화</span><span class="skt-help-text">{ti.get('recent_change', '-')}</span></div>
          <div class="skt-help-item"><span class="skt-chip orange">오늘 실행</span><span class="skt-help-text">{ti.get('action_point', ti.get('recommended_action', '-'))}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    today_nps = ti.get("today_nps")
    today_gap = float(today_nps) - float(target_score) if pd.notna(today_nps) else None
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("오늘 종합 NPS", fmt_score(today_nps), None if today_gap is None else f"{today_gap:+.1f}p vs 목표")
    c2.metric("오늘 판매성 NPS", fmt_score(ti.get("today_sales_nps")))
    c3.metric("오늘 비판매성 NPS", fmt_score(ti.get("today_non_sales_nps")))
    c4.metric("오늘 응답건수", f"{int(ti.get('today_total_responses', 0) or 0):,}")
    c5.metric("오늘 중립/비추천", f"{int(ti.get('today_risk_count', 0) or 0):,}")

legend_html = """
<div class="skt-help-box">
  <div class="skt-help-title">종합진단 유형구분</div>
  <div class="skt-help-grid">
    <div class="skt-help-item"><span class="skt-chip orange">즉시 개선형</span>비추천 2건 이상 또는 목표 미달 상태에서 비추천이 발생한 매장. 현장 VOC 확인과 즉시 코칭 우선.</div>
    <div class="skt-help-item"><span class="skt-chip magenta">구조 개선형</span>응답 샘플이 충분하고 중립/비추천 risk가 누적되며 판매성·비판매성 축이 함께 취약한 매장.</div>
    <div class="skt-help-item"><span class="skt-chip yellow">회복 가능형</span>목표 미달이나 비추천보다는 중립 영향이 크고, 추가 추천 확보로 목표 회복 가능성이 높은 매장.</div>
    <div class="skt-help-item"><span class="skt-chip">비판매성 취약형</span>판매성은 목표 이상이나 비판매성 NPS가 목표 미달인 매장. 팀 평가 대응 관점에서 별도 관리.</div>
    <div class="skt-help-item"><span class="skt-chip gray">판매성 취약형</span>비판매성은 목표 이상이나 판매성 NPS가 목표 미달인 매장. 판매 상담/가입·기변 과정 점검 대상.</div>
    <div class="skt-help-item"><span class="skt-chip green">우수 확산형</span>목표 이상이며 응답 샘플이 일정 수준 이상인 매장. 우수 응대 패턴 확산 후보.</div>
    <div class="skt-help-item"><span class="skt-chip gray">샘플 착시형</span>총응답 5건 미만. 점수보다 추가 샘플 확보 후 판단.</div>
    <div class="skt-help-item"><span class="skt-chip gray">관찰/유지형</span>즉시 개입 신호는 약하나 추세 관찰이 필요한 매장.</div>
  </div>
</div>
"""

priority_formula_html = f"""
<div class="skt-priority-note">
  <div class="skt-formula">우선순위점수 = 비추천×10 + 중립×3 + 목표까지 필요추천수×2 + min(총응답자,30)/10 + 목표미달Gap절대값/10</div>
  <div>해석: 비추천과 중립의 절대량을 가장 크게 보고, 목표 87점까지 회복에 필요한 추천수와 샘플 충분성을 함께 반영합니다. 점수가 높을수록 먼저 확인해야 할 매장입니다.</div>
</div>
"""

st.markdown('<div class="skt-section-title">매장 개입 우선순위</div>', unsafe_allow_html=True)
st.markdown('<div class="skt-section-caption">기본 판세는 종합 NPS로 보고, 우측 탭에서 판매성/비판매성 축으로 같은 매장을 재정렬합니다.</div>', unsafe_allow_html=True)

tabs = st.tabs(["종합 NPS", "판매성 NPS", "비판매성 NPS"])
for tab, axis in zip(tabs, ["종합 NPS", "판매성 NPS", "비판매성 NPS"]):
    with tab:
        axis_df = prepare_axis_table(priority_view_base, axis, target_score)
        show_cols = [
            "agency_name", "store_name", "선택축_총응답자", "선택축_추천", "선택축_중립", "선택축_비추천",
            "선택축_NPS", "선택축_목표Gap", "선택축_필요추천수", "선택축_샘플", "diagnosis_type", "선택축_priority_score",
        ]
        view = axis_df[[c for c in show_cols if c in axis_df.columns]].copy()
        rename = {
            "agency_name": "대리점", "store_name": "매장", "선택축_총응답자": "총응답자", "선택축_추천": "추천",
            "선택축_중립": "중립", "선택축_비추천": "비추천", "선택축_NPS": "NPS", "선택축_목표Gap": "목표Gap",
            "선택축_필요추천수": "필요추천수", "선택축_샘플": "샘플", "diagnosis_type": "종합진단", "선택축_priority_score": "우선순위점수",
        }
        view = view.rename(columns=rename)
        st.dataframe(
            view,
            use_container_width=True,
            hide_index=True,
            column_config={
                "NPS": st.column_config.NumberColumn("NPS", format="%.2f"),
                "목표Gap": st.column_config.NumberColumn("목표Gap", format="%.2f"),
                "우선순위점수": st.column_config.NumberColumn("우선순위점수", format="%.1f"),
            },
        )

st.markdown(priority_formula_html, unsafe_allow_html=True)

st.markdown('<div class="skt-section-title">비판매성 NPS 전용 상세</div>', unsafe_allow_html=True)
st.markdown('<div class="skt-section-caption">비판매성 업무유형 Top, 매장별 추이, 판매성은 양호하지만 비판매성만 낮은 매장을 별도로 봅니다.</div>', unsafe_allow_html=True)
ns_tab1, ns_tab2, ns_tab3, ns_tab4 = st.tabs(["집중관리 매장", "업무유형 Top", "매장별 추이", "판매성 양호·비판매성 취약"])
with ns_tab1:
    if non_sales_drilldown_view_base.empty:
        st.info("비판매성 Drill-down 데이터가 없습니다.")
    else:
        ns_focus = non_sales_drilldown_view_base.copy()
        ns_focus = ns_focus[(ns_focus["axis_target_gap"] < 0) | (ns_focus["axis_risk_count"] > 0)].head(30)
        ns_view = ns_focus.rename(columns={
            "agency_name": "대리점", "store_name": "매장", "axis_total_responses": "비판매성 응답", "axis_promoters": "추천",
            "axis_passives": "중립", "axis_detractors": "비추천", "axis_nps": "비판매성 NPS", "axis_target_gap": "목표Gap",
            "axis_required_promoters": "필요추천수", "axis_sample_grade": "샘플", "axis_risk_count": "Risk건수",
            "focus_reason": "집중관리 사유", "axis_priority_score": "우선순위점수",
        })
        st.dataframe(ns_view, use_container_width=True, hide_index=True, column_config={
            "비판매성 NPS": st.column_config.NumberColumn("비판매성 NPS", format="%.2f"),
            "목표Gap": st.column_config.NumberColumn("목표Gap", format="%.2f"),
            "우선순위점수": st.column_config.NumberColumn("우선순위점수", format="%.1f"),
        })
with ns_tab2:
    if non_sales_business_type_top.empty:
        st.info("비판매성 업무유형 Top 데이터가 없습니다.")
    else:
        type_view = non_sales_business_type_top.head(15).rename(columns={
            "business_type": "업무유형", "total_responses": "비판매성 응답", "promoters": "추천",
            "passives": "중립", "detractors": "비추천", "nps": "NPS", "risk_count": "Risk건수", "risk_rate": "Risk비중",
        })
        type_view["Risk비중(%)"] = pd.to_numeric(type_view["Risk비중"], errors="coerce") * 100
        type_view = type_view.drop(columns=["Risk비중"])
        fig = px.bar(type_view, x="업무유형", y=["중립", "비추천"], barmode="stack", color_discrete_sequence=["#E0CD4E", "#DC6339"])
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", xaxis_title="비판매성 업무유형", yaxis_title="Risk건수")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(type_view, use_container_width=True, hide_index=True, column_config={
            "NPS": st.column_config.NumberColumn("NPS", format="%.2f"),
            "Risk비중(%)": st.column_config.NumberColumn("Risk비중(%)", format="%.1f"),
        })
with ns_tab3:
    if store_non_sales_trend_view_base.empty:
        st.info("매장별 비판매성 추이 데이터가 없습니다.")
    else:
        trend = store_non_sales_trend_view_base.copy()
        trend_store_options = trend.sort_values(["risk_count", "total_responses"], ascending=False)["store_name"].dropna().astype(str).unique().tolist()
        default_stores = trend_store_options[:5]
        selected_trend_stores = st.multiselect("추이 확인 매장", trend_store_options, default=default_stores)
        trend_plot = trend[trend["store_name"].astype(str).isin(selected_trend_stores)].copy() if selected_trend_stores else trend.head(0)
        if trend_plot.empty:
            st.info("선택된 매장이 없습니다.")
        else:
            trend_plot = trend_plot.assign(trend_date=pd.to_datetime(trend_plot["trend_date"], errors="coerce"))
            trend_plot = trend_plot[trend_plot["trend_date"].notna()].copy()
            trend_plot["trend_label"] = trend_plot["trend_date"].map(lambda d: d.strftime("%m/%d"))
            trend_plot["hover_date"] = trend_plot["trend_date"].map(lambda d: d.strftime("%Y-%m-%d"))
            trend_plot["nps_display"] = pd.to_numeric(trend_plot["nps"], errors="coerce").map(
                lambda v: v if pd.isna(v) or v >= 0 else v * 0.2
            )
            x_order = trend_plot.sort_values("trend_date")["trend_label"].drop_duplicates().tolist()

            fig = px.line(
                trend_plot,
                x="trend_label",
                y="nps_display",
                color="store_name",
                markers=True,
                custom_data=["hover_date", "nps"],
            )
            fig.update_traces(hovertemplate="%{customdata[0]}<br>비판매성 NPS=%{customdata[1]:.1f}<extra>%{fullData.name}</extra>")

            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis_title="평가일",
                yaxis_title="비판매성 NPS · 음수구간 압축",
                yaxis=dict(
                    range=[-22, 105],
                    tickmode="array",
                    tickvals=[-20, -10, 0, 20, 40, 60, 80, 100],
                    ticktext=["-100", "-50", "0", "20", "40", "60", "80", "100"],
                    gridcolor="rgba(148,163,184,0.20)",
                ),
                xaxis=dict(type="category", categoryorder="array", categoryarray=x_order),
            )
            st.plotly_chart(fig, use_container_width=True)
            trend_view = trend_plot.drop(columns=["trend_label", "hover_date", "nps_display"]).rename(columns={"trend_date": "일자", "agency_name": "대리점", "store_name": "매장", "total_responses": "응답", "promoters": "추천", "passives": "중립", "detractors": "비추천", "nps": "비판매성 NPS", "risk_count": "Risk건수"})
            st.dataframe(trend_view, use_container_width=True, hide_index=True, column_config={"비판매성 NPS": st.column_config.NumberColumn("비판매성 NPS", format="%.2f")})
with ns_tab4:
    if sales_good_non_sales_weak_view_base.empty:
        st.success("현재 기준 판매성은 양호하지만 비판매성만 낮은 별도 분리 대상이 없습니다.")
    else:
        weak_view = sales_good_non_sales_weak_view_base.rename(columns={
            "agency_name": "대리점", "store_name": "매장", "sales_total_responses": "판매성 응답", "sales_nps_score_display": "판매성 NPS",
            "sales_source_nps_score": "판매성 NPS(엑셀원천)", "axis_total_responses": "비판매성 응답", "non_sales_nps_score_display": "비판매성 NPS",
            "non_sales_source_nps_score": "비판매성 NPS(엑셀원천)", "non_sales_target_gap": "비판매성 목표Gap", "non_sales_source_target_gap": "비판매성 목표Gap", "axis_nps": "비판매성 NPS(응답재계산)",
            "axis_passives": "비판매성 중립", "axis_detractors": "비판매성 비추천", "axis_required_promoters": "필요추천수", "axis_priority_score": "우선순위점수",
        })
        st.dataframe(weak_view, use_container_width=True, hide_index=True, column_config={
            "판매성 NPS": st.column_config.NumberColumn("판매성 NPS", format="%.2f"),
            "비판매성 NPS": st.column_config.NumberColumn("비판매성 NPS", format="%.2f"),
            "비판매성 NPS(응답재계산)": st.column_config.NumberColumn("비판매성 NPS(응답재계산)", format="%.2f"),
            "비판매성 목표Gap": st.column_config.NumberColumn("비판매성 목표Gap", format="%.2f"),
            "우선순위점수": st.column_config.NumberColumn("우선순위점수", format="%.1f"),
        })

st.markdown('<div class="skt-section-title">매장별 Action Sheet</div>', unsafe_allow_html=True)
st.markdown('<div class="skt-section-caption">대리점 필터/다운로드와 TOP 10 별도 출력이 가능한 현장 실행표입니다. 이번 주 액션은 1~2줄로 바로 전달 가능하게 정리했습니다.</div>', unsafe_allow_html=True)
if action_sheet_view_base.empty:
    st.info("Action Sheet 데이터가 없습니다.")
else:
    action_source = action_sheet_view_base.head(10 if top10_only else 40)
    action_rename = {
        "agency_name": "대리점", "store_code": "매장코드", "store_name": "매장", "axis_nps": "비판매성 NPS", "axis_target_gap": "목표Gap",
        "axis_required_promoters": "필요추천수", "axis_total_responses": "비판매성 응답", "axis_passives": "중립",
        "axis_detractors": "비추천", "top_business_type": "주요 Risk 업무", "top_voc_category": "VOC 분류",
        "top_risk_count": "Risk건수", "representative_voc": "대표 VOC", "이번주_액션": "이번 주 액션", "axis_priority_score": "우선순위점수",
    }
    action_view = action_source.rename(columns=action_rename)
    st.dataframe(action_view, use_container_width=True, hide_index=True, column_config={
        "비판매성 NPS": st.column_config.NumberColumn("비판매성 NPS", format="%.2f"),
        "목표Gap": st.column_config.NumberColumn("목표Gap", format="%.2f"),
        "우선순위점수": st.column_config.NumberColumn("우선순위점수", format="%.1f"),
    })
    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        st.download_button(
            "현재 보기 CSV 다운로드",
            data=action_view.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"nps_action_sheet_{team}_{str(report_date).replace('-', '')}.csv",
            mime="text/csv",
        )
    with dl_col2:
        top10_view = action_sheet_view_base.head(10).rename(columns=action_rename)
        st.download_button(
            "TOP 10 CSV 다운로드",
            data=top10_view.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"nps_action_sheet_top10_{team}_{str(report_date).replace('-', '')}.csv",
            mime="text/csv",
        )

st.markdown('<div class="skt-section-title">검산 / 샘플 경고</div>', unsafe_allow_html=True)
st.markdown('<div class="skt-section-caption">운영 판단은 재계산 NPS로 고정하되, 원천 Excel NPS와 차이가 큰 매장과 표본이 작은 축은 별도로 확인합니다.</div>', unsafe_allow_html=True)
audit_tab1, audit_tab2 = st.tabs(["원천 vs 재계산 차이 Top", "샘플소수 경고"])
with audit_tab1:
    if nps_source_recalc_diff_view_base.empty:
        st.success("원천 NPS와 재계산 NPS 비교 데이터가 없습니다.")
    else:
        diff_view = nps_source_recalc_diff_view_base.head(40).rename(columns={
            "agency_name": "대리점", "store_name": "매장", "axis": "축", "axis_total_responses": "응답",
            "source_nps": "원천 NPS", "recalc_nps": "재계산 NPS", "nps_diff": "차이", "nps_diff_abs": "차이절대값",
            "diagnosis_type": "종합진단",
        })
        st.dataframe(diff_view, use_container_width=True, hide_index=True, column_config={
            "원천 NPS": st.column_config.NumberColumn("원천 NPS", format="%.2f"),
            "재계산 NPS": st.column_config.NumberColumn("재계산 NPS", format="%.2f"),
            "차이": st.column_config.NumberColumn("차이", format="%.2f"),
            "차이절대값": st.column_config.NumberColumn("차이절대값", format="%.2f"),
        })
with audit_tab2:
    if sample_warning_view_base.empty:
        st.success("샘플소수 경고 대상이 없습니다.")
    else:
        sample_view = sample_warning_view_base.head(60).rename(columns={
            "agency_name": "대리점", "store_name": "매장", "axis": "축", "axis_total_responses": "응답",
            "promoters": "추천", "passives": "중립", "detractors": "비추천", "recalc_nps": "재계산 NPS",
            "sample_grade": "샘플등급", "risk_count": "Risk건수", "sample_warning": "확인 메시지",
            "diagnosis_type": "종합진단",
        })
        st.dataframe(sample_view, use_container_width=True, hide_index=True, column_config={
            "재계산 NPS": st.column_config.NumberColumn("재계산 NPS", format="%.2f"),
        })

left, right = st.columns(2)
with left:
    st.markdown('<div class="skt-section-title">진단 유형 분포</div>', unsafe_allow_html=True)
    diag = priority_view_base["diagnosis_type"].value_counts().reset_index()
    diag.columns = ["diagnosis_type", "count"]
    fig = px.bar(diag, x="diagnosis_type", y="count", color="diagnosis_type", color_discrete_sequence=["#815CF6", "#DC6339", "#C045F6", "#E0CD4E", "#5FCE73", "#6B7280"])
    fig.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", xaxis_title=None, yaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.markdown('<div class="skt-section-title">비추천/중립 Risk Top</div>', unsafe_allow_html=True)
    tmp = priority_view_base.copy()
    missing_risk_cols = [c for c in ["passives", "detractors"] if c not in tmp.columns]
    if missing_risk_cols:
        st.error(f"Risk 차트 필수 컬럼 누락: {missing_risk_cols}. 데이터 빌드를 다시 확인하세요.")
        st.stop()
    tmp["risk_count"] = pd.to_numeric(tmp["passives"], errors="coerce").fillna(0) + pd.to_numeric(tmp["detractors"], errors="coerce").fillna(0)
    top = tmp.sort_values("risk_count", ascending=False).head(15).rename(columns={"passives": "중립", "detractors": "비추천"})
    fig = px.bar(top, x="store_name", y=["중립", "비추천"], barmode="stack", color_discrete_sequence=["#E0CD4E", "#DC6339"])
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", xaxis_title=None, yaxis_title="건수", legend_title_text=None)
    st.plotly_chart(fig, use_container_width=True)

st.markdown(legend_html, unsafe_allow_html=True)

st.markdown('<div class="skt-section-title">VOC / 중립·비추천</div>', unsafe_allow_html=True)
if negative.empty:
    st.info("negative_feedback 데이터가 없습니다.")
else:
    neg_team = negative[negative["team_name"].astype(str).str.strip().eq(team)] if "team_name" in negative.columns else negative
    voc_tab1, voc_tab2 = st.tabs(["업무유형 Risk 요약", "VOC 원문 Table"])
    with voc_tab1:
        type_counts = neg_team["business_type"].value_counts(dropna=False).head(20).reset_index()
        type_counts.columns = ["business_type", "count"]
        fig = px.bar(type_counts, x="business_type", y="count", color_discrete_sequence=["#815CF6"])
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

        risk_summary = (
            neg_team.assign(response_type=neg_team.get("response_type", "").fillna("미분류"))
            .groupby(["agency_name", "store_name", "business_type", "response_type"], dropna=False)
            .size()
            .reset_index(name="건수")
            .pivot_table(index=["agency_name", "store_name", "business_type"], columns="response_type", values="건수", fill_value=0, aggfunc="sum")
            .reset_index()
        )
        for col in ["중립", "비추천"]:
            if col not in risk_summary.columns:
                risk_summary[col] = 0
        risk_summary["Risk건수"] = risk_summary["중립"] + risk_summary["비추천"]
        risk_summary = risk_summary.sort_values(["Risk건수", "비추천", "중립"], ascending=False).head(50)
        risk_view = risk_summary.rename(columns={"agency_name": "대리점", "store_name": "매장", "business_type": "업무유형"})
        st.dataframe(risk_view, use_container_width=True, hide_index=True)
    with voc_tab2:
        display_cols = [c for c in ["response_date", "process_date", "response_type", "agency_name", "store_name", "business_type", "voc_category", "recommend_score", "reason_text", "coaching_hint"] if c in neg_team.columns]
        voc_view = neg_team[display_cols].head(300).rename(columns={
            "response_date": "응답일자", "process_date": "처리일자", "response_type": "구분", "agency_name": "대리점",
            "store_name": "매장", "business_type": "업무유형", "voc_category": "VOC 분류", "recommend_score": "추천지수", "reason_text": "VOC 원문",
            "coaching_hint": "코칭 힌트",
        })
        st.dataframe(voc_view, use_container_width=True, hide_index=True)

st.markdown('<div class="skt-section-title">T크루 코칭 후보</div>', unsafe_allow_html=True)
st.markdown('<div class="skt-section-caption">개인 줄세우기보다 n≥5 기준의 코칭 후보를 먼저 보도록 구성했습니다. 비추천/중립 건수와 목표 Gap을 함께 봅니다.</div>', unsafe_allow_html=True)
if crew.empty:
    st.info("T크루 데이터가 없습니다.")
else:
    crew_team = crew[crew["team_name"].astype(str).str.strip().eq(team)].copy() if "team_name" in crew.columns else crew.copy()
    for c in ["promoters", "passives", "detractors", "total_responses"]:
        crew_team[c] = pd.to_numeric(crew_team.get(c, 0), errors="coerce").fillna(0)
    crew_team["NPS"] = crew_team.apply(lambda r: ((r["promoters"] - r["detractors"]) / r["total_responses"] * 100) if r["total_responses"] else None, axis=1)
    crew_team["목표Gap"] = crew_team["NPS"] - target_score
    crew_team["Risk건수"] = crew_team["passives"] + crew_team["detractors"]
    crew_team["코칭우선점수"] = crew_team["detractors"] * 10 + crew_team["passives"] * 3 + (-crew_team["목표Gap"].clip(upper=0) / 10) + crew_team["total_responses"].clip(upper=20) / 10
    coach = crew_team[crew_team["total_responses"] >= 5].sort_values(["코칭우선점수", "detractors", "total_responses"], ascending=False).head(50)
    coach_cols = [c for c in ["agency_name", "crew_name", "total_responses", "promoters", "passives", "detractors", "NPS", "목표Gap", "Risk건수", "코칭우선점수"] if c in coach.columns]
    coach_view = coach[coach_cols].rename(columns={
        "agency_name": "대리점", "crew_name": "T크루", "total_responses": "총응답자", "promoters": "추천", "passives": "중립", "detractors": "비추천",
    })
    st.dataframe(
        coach_view,
        use_container_width=True,
        hide_index=True,
        column_config={
            "NPS": st.column_config.NumberColumn("NPS", format="%.2f"),
            "목표Gap": st.column_config.NumberColumn("목표Gap", format="%.2f"),
            "코칭우선점수": st.column_config.NumberColumn("코칭우선점수", format="%.1f"),
        },
    )

