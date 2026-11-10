import datetime
import tempfile
import unittest
from pathlib import Path

from pipeline.tracker import (
    COLUMN_HEADERS,
    TrackerRow,
    append_row,
    create_tracker,
    read_rows,
    rows_needing_followup,
    update_status,
)


class TestTracker(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "tracker.xlsx"

    def test_create_tracker_has_expected_headers(self):
        create_tracker(self.path)
        from openpyxl import load_workbook

        workbook = load_workbook(self.path)
        sheet = workbook.active
        headers = [cell.value for cell in next(sheet.iter_rows(min_row=1, max_row=1))]
        self.assertEqual(headers, COLUMN_HEADERS)

    def test_append_and_read_round_trip(self):
        row = TrackerRow(
            company="Example Robotics",
            role="Senior Backend Engineer",
            date="2026-11-01",
            status="applied",
            contact="Jane Recruiter",
            next_action="Follow up in 7 days",
        )
        append_row(row, self.path)
        rows = read_rows(self.path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], row)

    def test_append_creates_file_if_missing(self):
        self.assertFalse(self.path.exists())
        row = TrackerRow("A", "B", "2026-11-01", "applied", "", "")
        append_row(row, self.path)
        self.assertTrue(self.path.exists())

    def test_update_status_updates_matching_row(self):
        append_row(TrackerRow("Example Robotics", "Senior Backend Engineer", "2026-11-01", "applied", "", ""), self.path)
        updated = update_status(
            "Example Robotics", "Senior Backend Engineer", "interviewing", "Prep for onsite", self.path
        )
        self.assertTrue(updated)
        rows = read_rows(self.path)
        self.assertEqual(rows[0].status, "interviewing")
        self.assertEqual(rows[0].next_action, "Prep for onsite")

    def test_update_status_returns_false_when_not_found(self):
        updated = update_status("Nonexistent Co", "Role", "interviewing", path=self.path)
        self.assertFalse(updated)

    def test_rows_needing_followup_after_7_days(self):
        today = datetime.date(2026, 11, 9)
        append_row(TrackerRow("Old Co", "Role A", "2026-11-01", "applied", "", ""), self.path)  # 8 days ago
        append_row(TrackerRow("Recent Co", "Role B", "2026-11-08", "applied", "", ""), self.path)  # 1 day ago
        append_row(TrackerRow("Rejected Co", "Role C", "2026-10-01", "rejected", "", ""), self.path)  # old but not applied

        due = rows_needing_followup(self.path, today=today, days=7)
        self.assertEqual([r.company for r in due], ["Old Co"])


if __name__ == "__main__":
    unittest.main()
