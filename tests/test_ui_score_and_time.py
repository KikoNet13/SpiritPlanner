from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "app"))

from screens.eras.eras_model import compute_era_score_summary  # noqa: E402
from screens.incursion_detail.incursion_detail_model import (  # noqa: E402
    format_duration_hhmmss,
)
from screens.incursions.incursions_model import get_score_label  # noqa: E402
from screens.periods.periods_model import (  # noqa: E402
    build_period_rows,
    compute_score_summary,
)


class DurationFormatTests(unittest.TestCase):
    def test_format_duration_hhmmss(self) -> None:
        self.assertEqual(format_duration_hhmmss(59), "00:00:59")
        self.assertEqual(format_duration_hhmmss(61), "00:01:01")
        self.assertEqual(format_duration_hhmmss(3661), "01:01:01")


class IncursionScoreLabelTests(unittest.TestCase):
    def test_get_score_label(self) -> None:
        self.assertEqual(get_score_label({"score": 42}), "42")
        self.assertEqual(get_score_label({"score": None}), "—")
        self.assertEqual(get_score_label({}), "—")


class PeriodScoreSummaryTests(unittest.TestCase):
    def test_compute_score_summary_partial(self) -> None:
        incursions = [
            {"id": "i01", "score": 15},
            {"id": "i02"},
            {"id": "i03", "score": 25},
            {"id": "i04", "score": None},
        ]
        score_total, completed_incursions, score_average = compute_score_summary(
            incursions
        )
        self.assertEqual(score_total, 40)
        self.assertEqual(completed_incursions, 2)
        self.assertAlmostEqual(score_average or 0.0, 20.0)

    def test_build_period_rows_includes_score_metrics(self) -> None:
        periods = [
            {"id": "p01", "index": 1, "revealed_at": "2026-02-18T00:00:00Z"},
        ]
        incursions_by_period = {
            "p01": [
                {"id": "i01", "index": 1, "spirit_1_id": "s1", "spirit_2_id": "s2", "score": 10},
                {"id": "i02", "index": 2, "spirit_1_id": "s3", "spirit_2_id": "s4"},
                {"id": "i03", "index": 3, "spirit_1_id": "s5", "spirit_2_id": "s6", "score": 20},
            ]
        }
        rows = build_period_rows(periods, incursions_by_period)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.score_total, 30)
        self.assertEqual(row.completed_incursions, 2)
        self.assertAlmostEqual(row.score_average or 0.0, 15.0)


class EraScoreSummaryTests(unittest.TestCase):
    def test_compute_era_score_summary_multi_period(self) -> None:
        incursions_by_period = {
            "p01": [
                {"id": "i01", "score": 10},
                {"id": "i02"},
            ],
            "p02": [
                {"id": "i03", "score": 20},
                {"id": "i04", "score": 30},
            ],
        }
        score_total, completed_incursions, score_average = compute_era_score_summary(
            incursions_by_period
        )
        self.assertEqual(score_total, 60)
        self.assertEqual(completed_incursions, 3)
        self.assertAlmostEqual(score_average or 0.0, 20.0)


if __name__ == "__main__":
    unittest.main()
