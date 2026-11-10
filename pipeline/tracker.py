"""Local application tracker spreadsheet.

A single .xlsx file openable directly in Excel or Google Sheets, at a
gitignored path under data/. Columns match the captain's intent exactly:
company, role, date, status, contact, next action.
"""

from __future__ import annotations

import dataclasses
import datetime
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.worksheet.worksheet import Worksheet

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TRACKER_PATH = REPO_ROOT / "data" / "tracker.xlsx"

COLUMNS = ["company", "role", "date", "status", "contact", "next_action"]
COLUMN_HEADERS = ["Company", "Role", "Date", "Status", "Contact", "Next Action"]

STATUSES = ["applied", "screening", "interviewing", "offer", "rejected", "withdrawn"]


@dataclasses.dataclass
class TrackerRow:
    company: str
    role: str
    date: str  # ISO 8601 date, e.g. "2026-11-09"
    status: str
    contact: str
    next_action: str

    def as_list(self) -> list[str]:
        return [self.company, self.role, self.date, self.status, self.contact, self.next_action]


def create_tracker(path: Path | None = None) -> Path:
    tracker_path = path or DEFAULT_TRACKER_PATH
    tracker_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Applications"
    sheet.append(COLUMN_HEADERS)
    workbook.save(tracker_path)
    return tracker_path


def _open_or_create(path: Path) -> Workbook:
    if path.exists():
        return load_workbook(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Applications"
    sheet.append(COLUMN_HEADERS)
    return workbook


def _sheet(workbook: Workbook) -> Worksheet:
    return workbook["Applications"] if "Applications" in workbook.sheetnames else workbook.active


def append_row(row: TrackerRow, path: Path | None = None) -> None:
    tracker_path = path or DEFAULT_TRACKER_PATH
    workbook = _open_or_create(tracker_path)
    _sheet(workbook).append(row.as_list())
    workbook.save(tracker_path)


def read_rows(path: Path | None = None) -> list[TrackerRow]:
    tracker_path = path or DEFAULT_TRACKER_PATH
    if not tracker_path.exists():
        return []
    workbook = load_workbook(tracker_path)
    sheet = _sheet(workbook)
    rows = []
    for row_cells in sheet.iter_rows(min_row=2, values_only=True):
        if row_cells[0] is None:
            continue
        rows.append(TrackerRow(*[("" if c is None else str(c)) for c in row_cells[:6]]))
    return rows


def find_row_index_by_company_role(
    company: str, role: str, path: Path | None = None
) -> int | None:
    """Return the 1-indexed sheet row number (header is row 1) or None."""
    tracker_path = path or DEFAULT_TRACKER_PATH
    if not tracker_path.exists():
        return None
    workbook = load_workbook(tracker_path)
    sheet = _sheet(workbook)
    for i, row_cells in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
        if row_cells[0] == company and row_cells[1] == role:
            return i
    return None


def update_status(
    company: str, role: str, new_status: str, next_action: str = "", path: Path | None = None
) -> bool:
    """Update status (and optionally next_action) for a matching row. Returns False if not found."""
    tracker_path = path or DEFAULT_TRACKER_PATH
    row_index = find_row_index_by_company_role(company, role, tracker_path)
    if row_index is None:
        return False
    workbook = load_workbook(tracker_path)
    sheet = _sheet(workbook)
    sheet.cell(row=row_index, column=4, value=new_status)  # Status
    if next_action:
        sheet.cell(row=row_index, column=6, value=next_action)  # Next Action
    workbook.save(tracker_path)
    return True


def rows_needing_followup(path: Path | None = None, today: datetime.date | None = None, days: int = 7) -> list[TrackerRow]:
    """Rows still in 'applied' status whose date is >= `days` days ago."""
    today = today or datetime.date.today()
    rows = read_rows(path)
    due = []
    for row in rows:
        if row.status != "applied":
            continue
        try:
            applied_date = datetime.date.fromisoformat(row.date)
        except ValueError:
            continue
        if (today - applied_date).days >= days:
            due.append(row)
    return due
