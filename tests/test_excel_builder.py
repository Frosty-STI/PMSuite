"""Structural Excel rendering assertions."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from gantt_builder import api
from gantt_builder.models import HolidayEntry, Project, ProjectMeta, Settings, Task


def test_working_day_holiday_gap_uses_holiday_fill(tmp_path: Path):
    project = Project(
        project=ProjectMeta(
            id="EXCEL-TEST",
            name="Excel test",
            timezone="America/Chicago",
            created_at=datetime(2026, 5, 13, 12, 0, 0),
            updated_at=datetime(2026, 5, 13, 12, 0, 0),
        ),
        settings=Settings(
            holidays={
                "DAL": [
                    HolidayEntry(date=date(2026, 5, 19), name="Test Holiday", source="user-added"),
                ],
            },
            work_weeks={"DAL": ["MON", "TUE", "WED", "THU", "FRI"]},
            next_task_id=2,
        ),
        tasks=[
            Task(
                id="TASK-001",
                name="Working task over holiday",
                completion_location="DAL",
                calendar_mode="working_days",
                cycle_time_days=3,
                manual_start_date=date(2026, 5, 18),
            ),
        ],
    )

    output = api.build_excel(project, output_dir=tmp_path)

    openpyxl = __import__("openpyxl")
    wb = openpyxl.load_workbook(str(output))
    sheet = wb["Day View"]

    holiday_col = None
    for cell in sheet[1]:
        if isinstance(cell.value, str) and "2026-05-19" in cell.value:
            holiday_col = cell.column
            break

    assert holiday_col is not None
    holiday_cell = sheet.cell(row=2, column=holiday_col)
    assert holiday_cell.fill.fgColor.rgb == "FFB0B0B0"
