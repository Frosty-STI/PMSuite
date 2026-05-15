"""Excel workbook generation via xlsxwriter.

Walking-skeleton: produces a valid 4-sheet workbook with task data populated.
- Day View: task rows + date columns, basic blue cells for planned ranges
- Week View: task rows + week columns
- Schedule Calculations: full audit table per DESIGN.md Q26b
- Critical Path Notes: summary section

Frozen panes, conditional coloring per status, holiday/weekend shading, parent
summary bars, and the full Option E rendering described in DESIGN.md Q15 will be
added incrementally. The file is structurally complete and openable.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

import xlsxwriter

from .critical_path import CriticalPathResult
from .locations import weekday_code
from .logging_config import get_logger
from .models import Project
from .scheduler import ScheduledTask

_log = get_logger(__name__)


def build_excel(
    project: Project,
    schedule: dict[str, ScheduledTask],
    critical_path: CriticalPathResult,
    output_dir: str | Path | None = None,
) -> Path:
    """Generate the Excel workbook and return the output path.

    Filename pattern: gantt_<project_id>_<YYYY-MM-DD>_<HHMMSS>.xlsx
    """
    output_dir = Path(output_dir) if output_dir else Path(project.settings.output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"gantt_{project.project.id}_{timestamp}.xlsx"
    path = output_dir / filename

    # Collision-safe (rare same-second case)
    counter = 2
    while path.exists():
        filename = f"gantt_{project.project.id}_{timestamp}_{counter}.xlsx"
        path = output_dir / filename
        counter += 1

    workbook = xlsxwriter.Workbook(str(path))

    formats = _build_formats(workbook)

    axis_start, axis_end = _compute_axis(project, schedule)

    _build_day_view(workbook, project, schedule, formats, axis_start, axis_end)
    _build_week_view(workbook, project, schedule, formats, axis_start, axis_end)
    _build_schedule_calculations(workbook, project, schedule, critical_path, formats)
    _build_critical_path_notes(workbook, project, schedule, critical_path, formats)

    workbook.close()
    _log.info("Built Excel workbook %s for project %s", path, project.project.id)
    return path


def _build_formats(workbook) -> dict:
    return {
        "header":         workbook.add_format({"bold": True, "bg_color": "#D9D9D9", "border": 1, "align": "center"}),
        "task_id":        workbook.add_format({"font_name": "Consolas", "border": 1}),
        "task_name":      workbook.add_format({"border": 1}),
        "date":           workbook.add_format({"num_format": "yyyy-mm-dd", "border": 1}),
        "planned":        workbook.add_format({"bg_color": "#4A90D9", "border": 1}),
        "completed":      workbook.add_format({"bg_color": "#2E8B57", "border": 1}),
        "delayed":        workbook.add_format({"bg_color": "#E68A00", "border": 1}),
        "overdue":        workbook.add_format({"bg_color": "#D9534F", "border": 1}),
        "today":          workbook.add_format({"bg_color": "#FFF8C4"}),
        "weekend":        workbook.add_format({"bg_color": "#F0F0F0"}),
        "holiday":        workbook.add_format({"bg_color": "#E0E0E0"}),
        "parent_summary": workbook.add_format({"bg_color": "#555555", "font_color": "white", "border": 1}),
        "summary_label":  workbook.add_format({"bold": True}),
    }


def _compute_axis(project: Project, schedule: dict[str, ScheduledTask]) -> tuple[date, date]:
    """Padded + Monday-aligned axis per DESIGN.md Q19."""
    today = date.today()

    if schedule:
        earliest_start = min(s.computed_start for s in schedule.values())
        latest_finish = max(s.effective_finish for s in schedule.values())
    else:
        earliest_start = today
        latest_finish = today

    if project.settings.date_axis_start is not None:
        start_axis = project.settings.date_axis_start
    else:
        raw_start = min(earliest_start, today) - timedelta(days=7)
        start_axis = raw_start - timedelta(days=raw_start.weekday())  # back to Monday

    if project.settings.date_axis_end is not None:
        end_axis = project.settings.date_axis_end
    else:
        raw_end = max(latest_finish, today) + timedelta(days=14)
        end_axis = raw_end + timedelta(days=(6 - raw_end.weekday()))  # forward to Sunday

    return start_axis, end_axis


def _build_day_view(workbook, project, schedule, formats, axis_start: date, axis_end: date) -> None:
    sheet = workbook.add_worksheet("Day View")

    metadata_cols = ["TASK ID", "Name", "Location"]
    for col, header in enumerate(metadata_cols):
        sheet.write(0, col, header, formats["header"])

    date_columns = []
    current = axis_start
    col = len(metadata_cols)
    while current <= axis_end:
        sheet.write(0, col, current.isoformat(), formats["header"])
        date_columns.append((col, current))
        current += timedelta(days=1)
        col += 1

    sheet.set_column(0, 0, 12)
    sheet.set_column(1, 1, 28)
    sheet.set_column(2, 2, 10)
    sheet.set_column(len(metadata_cols), col - 1, 4)
    sheet.freeze_panes(1, len(metadata_cols))

    for row_idx, task in enumerate(project.tasks, start=1):
        sheet.write(row_idx, 0, task.id, formats["task_id"])
        sheet.write(row_idx, 1, task.name, formats["task_name"])
        sheet.write(row_idx, 2, task.completion_location, formats["task_name"])

        s = schedule.get(task.id)
        if not s:
            continue

        for col_idx, d in date_columns:
            cell_format = None
            if s.computed_start <= d <= s.computed_finish:
                cell_format = formats["completed"] if task.is_complete else formats["planned"]
            elif s.computed_finish < d <= s.effective_finish:
                cell_format = formats["delayed"]
            if cell_format:
                sheet.write_blank(row_idx, col_idx, None, cell_format)


def _build_week_view(workbook, project, schedule, formats, axis_start: date, axis_end: date) -> None:
    sheet = workbook.add_worksheet("Week View")

    metadata_cols = ["TASK ID", "Name", "Location"]
    for col, header in enumerate(metadata_cols):
        sheet.write(0, col, header, formats["header"])

    week_columns = []
    current = axis_start
    col = len(metadata_cols)
    while current <= axis_end:
        sheet.write(0, col, current.isoformat(), formats["header"])
        week_columns.append((col, current, current + timedelta(days=6)))
        current += timedelta(days=7)
        col += 1

    sheet.set_column(0, 0, 12)
    sheet.set_column(1, 1, 28)
    sheet.set_column(2, 2, 10)
    sheet.set_column(len(metadata_cols), col - 1, 10)
    sheet.freeze_panes(1, len(metadata_cols))

    for row_idx, task in enumerate(project.tasks, start=1):
        sheet.write(row_idx, 0, task.id, formats["task_id"])
        sheet.write(row_idx, 1, task.name, formats["task_name"])
        sheet.write(row_idx, 2, task.completion_location, formats["task_name"])

        s = schedule.get(task.id)
        if not s:
            continue

        for col_idx, week_start, week_end in week_columns:
            overlap = not (s.computed_finish < week_start or s.computed_start > week_end)
            if overlap:
                cell_format = formats["completed"] if task.is_complete else formats["planned"]
                sheet.write_blank(row_idx, col_idx, None, cell_format)


def _build_schedule_calculations(workbook, project, schedule, critical_path, formats) -> None:
    sheet = workbook.add_worksheet("Schedule Calculations")

    columns = [
        "TASK ID", "Name", "Hierarchy Level", "Parent ID", "Location", "Calendar Mode",
        "Cycle Time", "Manual Start Date", "Computed Start", "Computed Finish",
        "Delay Days", "Effective Finish", "Actual Completion Date", "Is Complete",
        "Dependencies", "Total Float", "Is Critical", "Was On Critical Path",
        "Downstream Impact", "Validation Warnings",
    ]
    for col, header in enumerate(columns):
        sheet.write(0, col, header, formats["header"])

    history_map = {h.task_id: h.was_on_critical_path for h in project.project.history}

    for row_idx, task in enumerate(project.tasks, start=1):
        s = schedule.get(task.id)
        level = _hierarchy_level(project, task.id)
        deps_str = "; ".join(f"{d.id}[{d.type}, lag {d.lag_days}]" for d in task.dependencies)
        downstream = sum(1 for other in project.tasks for d in other.dependencies if d.id == task.id)

        sheet.write(row_idx, 0, task.id)
        sheet.write(row_idx, 1, task.name)
        sheet.write(row_idx, 2, level)
        sheet.write(row_idx, 3, task.parent_id or "")
        sheet.write(row_idx, 4, task.completion_location)
        sheet.write(row_idx, 5, task.calendar_mode)
        sheet.write(row_idx, 6, task.cycle_time_days if task.cycle_time_days is not None else "")
        sheet.write(row_idx, 7, task.manual_start_date.isoformat() if task.manual_start_date else "")
        sheet.write(row_idx, 8, s.computed_start.isoformat() if s else "")
        sheet.write(row_idx, 9, s.computed_finish.isoformat() if s else "")
        sheet.write(row_idx, 10, task.delay_days)
        sheet.write(row_idx, 11, s.effective_finish.isoformat() if s else "")
        sheet.write(row_idx, 12, task.actual_completion_date.isoformat() if task.actual_completion_date else "")
        sheet.write(row_idx, 13, task.is_complete)
        sheet.write(row_idx, 14, deps_str)
        sheet.write(row_idx, 15, critical_path.total_float.get(task.id, 0))
        sheet.write(row_idx, 16, task.id in critical_path.critical_task_ids)
        sheet.write(row_idx, 17, history_map.get(task.id, False))
        sheet.write(row_idx, 18, downstream)
        sheet.write(row_idx, 19, "")

    sheet.freeze_panes(1, 2)
    sheet.set_column(0, 0, 12)
    sheet.set_column(1, 1, 28)
    sheet.set_column(2, len(columns) - 1, 14)


def _build_critical_path_notes(workbook, project, schedule, critical_path, formats) -> None:
    sheet = workbook.add_worksheet("Critical Path Notes")

    overdue = [t.id for t in project.tasks
               if not t.is_complete
               and t.id in schedule
               and schedule[t.id].effective_finish < date.today()]
    delayed = [t.id for t in project.tasks if t.delay_days > 0 and not t.is_complete]

    rows = [
        ("Project", f"{project.project.id} — {project.project.name}"),
        ("Project end (derived)", critical_path.project_end.isoformat() if critical_path.project_end else "n/a"),
        ("Total tasks", len(project.tasks)),
        ("Critical path tasks", len(critical_path.critical_task_ids)),
        ("Overdue incomplete tasks", len(overdue)),
        ("Tasks with delay > 0", len(delayed)),
        ("", ""),
        ("Summary", _build_summary(project, schedule, critical_path, overdue, delayed)),
    ]
    for row_idx, (label, value) in enumerate(rows):
        sheet.write(row_idx, 0, label, formats["summary_label"] if label else None)
        sheet.write(row_idx, 1, value)

    sheet.set_column(0, 0, 28)
    sheet.set_column(1, 1, 80)


def _build_summary(project, schedule, critical_path, overdue, delayed) -> str:
    end = critical_path.project_end.isoformat() if critical_path.project_end else "tbd"
    return (
        f"Project {project.project.id} ends {end}. "
        f"{len(critical_path.critical_task_ids)} tasks on critical path. "
        f"{len(overdue)} overdue. {len(delayed)} delayed."
    )


def _hierarchy_level(project: Project, task_id: str) -> int:
    """0 = root, 1 = first-level child, etc."""
    level = 0
    current = project.task_by_id(task_id)
    while current and current.parent_id:
        level += 1
        current = project.task_by_id(current.parent_id)
        if level > 100:
            return level
    return level
