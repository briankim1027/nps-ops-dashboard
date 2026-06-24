from __future__ import annotations

from pathlib import Path
import sys
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nps_ops.insights import (
    _response_date_col,
    build_daily_nps_trend,
    build_nps_source_recalc_diff,
    build_nps_time_intelligence,
    build_sample_warning,
)
from nps_ops.metrics import build_store_priority, diagnose_store, normalize_nps_series


class MetricsScaleTest(unittest.TestCase):
    def test_normalize_nps_series_ratio_scale(self) -> None:
        s = pd.Series([0.333, 1.0, -1.0, 0.857, None])
        result = normalize_nps_series(s)
        self.assertAlmostEqual(result.iloc[0], 33.3, places=1)
        self.assertAlmostEqual(result.iloc[1], 100.0, places=1)
        self.assertAlmostEqual(result.iloc[2], -100.0, places=1)
        self.assertAlmostEqual(result.iloc[3], 85.7, places=1)
        self.assertTrue(pd.isna(result.iloc[4]))

    def test_normalize_nps_series_score_scale(self) -> None:
        s = pd.Series([87.0, -50.0, 33.3, 100.0])
        result = normalize_nps_series(s)
        self.assertEqual(result.round(1).tolist(), [87.0, -50.0, 33.3, 100.0])

    def test_diagnose_store_non_sales_weak_after_normalization(self) -> None:
        row = pd.Series({
            "total_responses": 15,
            "nps_recalc": 70.0,
            "detractors": 1,
            "passives": 2,
            "required_promoters_to_target": 20,
            "sales_nps_score": 95.0,
            "non_sales_nps_score": 45.0,
        })
        self.assertEqual(diagnose_store(row), "비판매성 취약형")

    def test_diagnose_store_axis_weak_before_recoverable(self) -> None:
        row = pd.Series({
            "total_responses": 15,
            "nps_recalc": 70.0,
            "detractors": 0,
            "passives": 2,
            "required_promoters_to_target": 8,
            "sales_nps_score": 90.0,
            "non_sales_nps_score": 40.0,
        })
        self.assertEqual(diagnose_store(row), "비판매성 취약형")

    def test_diagnose_store_prefers_count_recalc_axis_scores(self) -> None:
        row = pd.Series({
            "total_responses": 20,
            "nps_recalc": 80.0,
            "detractors": 0,
            "passives": 4,
            "required_promoters_to_target": 4,
            # Source aggregate says sales is healthy and non-sales is weak...
            "sales_nps_score": 95.0,
            "non_sales_nps_score": 40.0,
            # ...but count-recalculated operational 기준 says the opposite.
            "sales_nps_recalc": 40.0,
            "non_sales_nps_recalc": 95.0,
        })
        self.assertEqual(diagnose_store(row), "판매성 취약형")

    def test_build_store_priority_adds_axis_recalc_and_uses_it_for_diagnosis(self) -> None:
        store_agg = pd.DataFrame([
            {
                "team_name": "전북",
                "store_name": "테스트매장",
                "promoters": 16,
                "passives": 4,
                "detractors": 0,
                "total_responses": 20,
                "sales_promoters": 2,
                "sales_passives": 1,
                "sales_detractors": 2,
                "sales_total_responses": 5,
                "non_sales_promoters": 10,
                "non_sales_passives": 0,
                "non_sales_detractors": 0,
                "non_sales_total_responses": 10,
                # Source values intentionally conflict with count-recalc values.
                "sales_nps_score": 1.0,
                "non_sales_nps_score": 0.4,
            }
        ])
        out = build_store_priority(store_agg)
        row = out.iloc[0]
        self.assertAlmostEqual(row["sales_nps_recalc"], 0.0)
        self.assertAlmostEqual(row["non_sales_nps_recalc"], 100.0)
        self.assertEqual(row["diagnosis_type"], "판매성 취약형")

    def test_nps_source_recalc_diff_surfaces_large_axis_gap(self) -> None:
        priority = pd.DataFrame([
            {
                "agency_name": "A",
                "store_name": "S",
                "diagnosis_type": "판매성 취약형",
                "nps_score": 80.0,
                "nps_recalc": 80.0,
                "total_responses": 10,
                "sales_nps_score": 1.0,
                "sales_nps_recalc": 0.0,
                "sales_total_responses": 5,
                "non_sales_nps_score": 0.4,
                "non_sales_nps_recalc": 100.0,
                "non_sales_total_responses": 10,
            }
        ])
        audit = build_nps_source_recalc_diff(priority)
        self.assertEqual(audit.iloc[0]["axis"], "판매성")
        self.assertAlmostEqual(audit.iloc[0]["nps_diff_abs"], 100.0)

    def test_sample_warning_flags_low_n_axis(self) -> None:
        priority = pd.DataFrame([
            {
                "agency_name": "A",
                "store_name": "S",
                "diagnosis_type": "샘플 착시형",
                "promoters": 3,
                "passives": 0,
                "detractors": 1,
                "total_responses": 4,
                "nps_recalc": 50.0,
                "sales_promoters": 2,
                "sales_passives": 0,
                "sales_detractors": 0,
                "sales_total_responses": 2,
                "sales_nps_recalc": 100.0,
                "non_sales_promoters": 1,
                "non_sales_passives": 0,
                "non_sales_detractors": 1,
                "non_sales_total_responses": 2,
                "non_sales_nps_recalc": 0.0,
            }
        ])
        warning = build_sample_warning(priority, target_score=87.0)
        self.assertGreaterEqual(len(warning), 3)
        self.assertTrue(warning["sample_warning"].str.contains("추가 샘플 확보").any())

    def test_response_date_col_prefers_process_date(self) -> None:
        df = pd.DataFrame({"process_date": ["2026-06-22"], "evaluation_date": ["2026-06-23"]})
        self.assertEqual(_response_date_col(df), "process_date")

    def test_response_date_col_falls_back_to_evaluation_date(self) -> None:
        df = pd.DataFrame({"evaluation_date": ["2026-06-23"]})
        self.assertEqual(_response_date_col(df), "evaluation_date")

    def test_build_daily_nps_trend_axes_from_process_date(self) -> None:
        fact = pd.DataFrame([
            {"team_name": "전북", "NCSI": "판매성", "process_date": "2026-06-22", "evaluation_date": "2026-06-23", "promoter_flag": 1, "passive_flag": 0, "detractor_flag": 0},
            {"team_name": "전북", "NCSI": "비판매성", "process_date": "2026-06-22", "evaluation_date": "2026-06-23", "promoter_flag": 0, "passive_flag": 0, "detractor_flag": 1},
            {"team_name": "전북", "NCSI": "비판매성", "process_date": "2026-06-22", "evaluation_date": "2026-06-23", "promoter_flag": 0, "passive_flag": 1, "detractor_flag": 0},
        ])
        trend = build_daily_nps_trend(fact, team="전북")
        self.assertEqual(set(trend["axis"]), {"종합", "판매성", "비판매성"})
        self.assertTrue((trend["trend_date"] == pd.Timestamp("2026-06-22")).all())
        overall = trend[trend["axis"].eq("종합")].iloc[0]
        self.assertAlmostEqual(overall["nps"], 0.0)
        non_sales = trend[trend["axis"].eq("비판매성")].iloc[0]
        self.assertEqual(non_sales["risk_count"], 2)

    def test_time_intelligence_empty_input(self) -> None:
        self.assertTrue(build_nps_time_intelligence(pd.DataFrame(), team="전북").empty)

    def test_time_intelligence_emits_dynamic_message_fields(self) -> None:
        fact = pd.DataFrame([
            {"team_name": "전북", "NCSI": "판매성", "process_date": "2026-06-21", "promoter_flag": 1, "passive_flag": 0, "detractor_flag": 0},
            {"team_name": "전북", "NCSI": "판매성", "process_date": "2026-06-22", "promoter_flag": 0, "passive_flag": 1, "detractor_flag": 0},
            {"team_name": "전북", "NCSI": "비판매성", "process_date": "2026-06-22", "promoter_flag": 0, "passive_flag": 0, "detractor_flag": 1},
        ])
        ti = build_nps_time_intelligence(fact, team="전북", target_score=87.0, report_date=None)
        self.assertFalse(ti.empty)
        row = ti.iloc[0]
        self.assertEqual(row["today_status"], "샘플 확인")
        self.assertIn("이번 주 종합 NPS", row["weekly_situation"])
        self.assertIn("전일 대비", row["recent_change"])
        self.assertIn("표본", row["action_point"])


if __name__ == "__main__":
    unittest.main()
