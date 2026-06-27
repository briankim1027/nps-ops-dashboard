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
    build_store_action_card,
    build_store_daily_heatmap,
    build_store_daily_lookup,
    build_weekday_time_hotspots,
)
from nps_ops.metrics import build_store_priority, diagnose_store, normalize_nps_series
from scripts.build_data import find_latest_file, validate_response_contract


class BuildDataGuardrailTest(unittest.TestCase):
    def test_find_latest_file_prefers_filename_report_date_over_mtime(self) -> None:
        import os
        import tempfile
        import time

        with tempfile.TemporaryDirectory() as tmpdir:
            raw_dir = Path(tmpdir)
            older_by_name = raw_dir / "●26년06월 NPS평가 통계_0621.xlsx"
            newer_by_name = raw_dir / "●26년06월 NPS평가 통계_0624.xlsx"
            pd.DataFrame({"x": [1]}).to_excel(older_by_name, index=False)
            pd.DataFrame({"x": [1]}).to_excel(newer_by_name, index=False)
            now = time.time()
            os.utime(newer_by_name, (now - 100, now - 100))
            os.utime(older_by_name, (now, now))

            self.assertEqual(find_latest_file(raw_dir).name, newer_by_name.name)

    def test_validate_response_contract_passes_expected_operating_shape(self) -> None:
        response = pd.DataFrame([
            {"promoter_flag": 1, "passive_flag": 0, "detractor_flag": 0, "NCSI": "판매성"},
            {"promoter_flag": 0, "passive_flag": 1, "detractor_flag": 0, "NCSI": "비판매성"},
            {"promoter_flag": 0, "passive_flag": 0, "detractor_flag": 1, "NCSI": "비판매성"},
        ])
        self.assertEqual(validate_response_contract(response), [])

    def test_validate_response_contract_warns_on_silent_failure_shapes(self) -> None:
        response = pd.DataFrame([
            {"promoter_flag": 0, "passive_flag": 0, "detractor_flag": 0, "NCSI": "기타"},
            {"promoter_flag": 1, "passive_flag": 1, "detractor_flag": 0, "NCSI": "판매성"},
        ])
        warnings = validate_response_contract(response)
        self.assertTrue(any("one-hot violation" in w for w in warnings))
        self.assertTrue(any("unexpected values" in w for w in warnings))
        self.assertTrue(any("no 비판매성" in w for w in warnings))


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

    def test_store_daily_heatmap_aggregates_non_sales_by_date_and_store(self) -> None:
        fact = pd.DataFrame([
            {"team_name": "전북", "NCSI": "비판매성", "process_date": "2026-06-22", "agency_name": "A", "store_code": "S1", "store_name": "매장1", "promoter_flag": 1, "passive_flag": 0, "detractor_flag": 0},
            {"team_name": "전북", "NCSI": "비판매성", "process_date": "2026-06-22", "agency_name": "A", "store_code": "S1", "store_name": "매장1", "promoter_flag": 0, "passive_flag": 0, "detractor_flag": 1},
            {"team_name": "전북", "NCSI": "판매성", "process_date": "2026-06-22", "agency_name": "A", "store_code": "S1", "store_name": "매장1", "promoter_flag": 1, "passive_flag": 0, "detractor_flag": 0},
        ])
        heatmap = build_store_daily_heatmap(fact, team="전북", axis="비판매성")
        self.assertEqual(len(heatmap), 1)
        row = heatmap.iloc[0]
        self.assertEqual(row["total_responses"], 2)
        self.assertEqual(row["risk_count"], 1)
        self.assertAlmostEqual(row["nps"], 0.0)

    def test_weekday_time_hotspots_uses_four_time_buckets_when_time_exists(self) -> None:
        fact = pd.DataFrame([
            {"team_name": "전북", "NCSI": "비판매성", "process_date": "2026-06-22 10:15:00", "promoter_flag": 1, "passive_flag": 0, "detractor_flag": 0},
            {"team_name": "전북", "NCSI": "비판매성", "process_date": "2026-06-22 15:20:00", "promoter_flag": 0, "passive_flag": 1, "detractor_flag": 0},
        ])
        hotspots = build_weekday_time_hotspots(fact, team="전북", axis="비판매성")
        self.assertEqual(set(hotspots["time_bucket"]), {"오전(09-12)", "오후(14-17)"})
        self.assertTrue(hotspots["has_time_detail"].all())

    def test_weekday_time_hotspots_marks_missing_time_detail_for_date_only_source(self) -> None:
        fact = pd.DataFrame([
            {"team_name": "전북", "NCSI": "비판매성", "process_date": "2026-06-22", "promoter_flag": 1, "passive_flag": 0, "detractor_flag": 0},
        ])
        hotspots = build_weekday_time_hotspots(fact, team="전북", axis="비판매성")
        self.assertEqual(hotspots.iloc[0]["time_bucket"], "시간정보 없음")
        self.assertFalse(bool(hotspots.iloc[0]["has_time_detail"]))


class StoreActionCardTest(unittest.TestCase):
    def _store_row(self, **over) -> pd.Series:
        base = {
            "store_code": "S1", "store_name": "테스트점", "agency_name": "테스트대리점", "marketer": "홍길동",
            "diagnosis_type": "즉시 개선형", "priority_score": 50.0, "sample_confidence": 0.85,
            "nps_recalc": 70.0, "non_sales_nps_recalc": 60.0, "sales_nps_recalc": 90.0,
            "promoters": 18, "passives": 3, "detractors": 3, "total_responses": 24,
            "required_promoters_to_target": 4,
        }
        base.update(over)
        return pd.Series(base)

    def _negative(self) -> pd.DataFrame:
        return pd.DataFrame([
            {"store_code": "S1", "response_type": "비추천", "business_type": "요금수납", "recommend_score": 2.0,
             "reason_text": "수납하러 갔는데 대기가 너무 길었다", "voc_category": "대기/처리시간", "coaching_hint": "대기 안내"},
            {"store_code": "S1", "response_type": "비추천", "business_type": "요금수납", "recommend_score": 5.0,
             "reason_text": "없음", "voc_category": "무의미/내용없음", "coaching_hint": "반복 여부 확인"},
            {"store_code": "S1", "response_type": "중립", "business_type": "명의변경", "recommend_score": 8.0,
             "reason_text": "처리는 됐는데 설명이 부족", "voc_category": "요금/제도 설명부족", "coaching_hint": "재설명"},
            {"store_code": "S1", "response_type": "중립", "business_type": "기기변경", "recommend_score": 7.0,
             "reason_text": "불편하지 않았습니다", "voc_category": "업무처리 미흡", "coaching_hint": "확인"},
        ])

    def test_daily_lookup_today_and_recent7_windows(self) -> None:
        fact = pd.DataFrame([
            {"team_name": "전북", "store_code": "S1", "process_date": "2026-06-24", "promoter_flag": 1, "passive_flag": 0, "detractor_flag": 0},
            {"team_name": "전북", "store_code": "S1", "process_date": "2026-06-20", "promoter_flag": 0, "passive_flag": 0, "detractor_flag": 1},
            {"team_name": "전북", "store_code": "S1", "process_date": "2026-06-10", "promoter_flag": 1, "passive_flag": 0, "detractor_flag": 0},
        ])
        lookup = build_store_daily_lookup(fact, team="전북")
        self.assertEqual(lookup["S1"]["today"], (1, 0, 1))  # only 06-24
        self.assertEqual(lookup["S1"]["recent7"], (1, 1, 2))  # 06-18..06-24 (excludes 06-10)

    def test_action_card_immediate_type_uses_detractor_scope_and_filters_voc(self) -> None:
        card = build_store_action_card(self._store_row(), self._negative(), {"S1": {"today": (0, 1, 1), "recent7": (1, 1, 3)}}, target_score=87.0)
        # 즉시 개선형 → business top scope is 비추천 only → 요금수납 appears, 명의변경(중립) excluded.
        self.assertEqual(card["top_business_types"][0][0], "요금수납")
        self.assertTrue(all(bt[0] != "명의변경" for bt in card["top_business_types"]))
        # representative VOC drops 무의미/내용없음 and ranks by lowest recommend_score.
        self.assertEqual(card["representative_vocs"][0]["text"], "수납하러 갔는데 대기가 너무 길었다")
        self.assertTrue(all(v["voc_category"] != "무의미/내용없음" for v in card["representative_vocs"]))
        # No-issue passive comment ("불편하지 않았습니다") must never surface as evidence.
        self.assertTrue(all("불편하지 않았" not in v["text"] for v in card["representative_vocs"]))
        self.assertTrue(any("전수 확인" in a for a in card["actions"]))
        self.assertEqual(card["trend_arrow"], "▼")  # today nps 0 < month 70

    def test_action_card_non_sales_type_includes_passives_in_scope(self) -> None:
        card = build_store_action_card(self._store_row(diagnosis_type="비판매성 취약형"), self._negative(), {}, target_score=87.0)
        types = [bt[0] for bt in card["top_business_types"]]
        self.assertIn("명의변경", types)  # 중립 included for non-sales type
        self.assertTrue(any("추천 전환" in a for a in card["actions"]))

    def test_action_card_handles_no_negative_rows(self) -> None:
        card = build_store_action_card(self._store_row(), pd.DataFrame(), {}, target_score=87.0)
        self.assertEqual(card["top_business_types"], [])
        self.assertEqual(card["representative_vocs"], [])
        self.assertEqual(card["today_nps"], None)


if __name__ == "__main__":
    unittest.main()
