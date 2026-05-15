"""Forward-pass scheduling.

Computes earliest start and earliest finish for every task, respecting:
- Per-task calendar mode (working_days vs e_days)
- Manual start date as floor
- Full FS / SS / FF / SF dependency types with lag (positive or negative)
- Parent rollup (parent.start = earliest child start; parent.end = latest child end)
- Cumulative delay_days applied to compute effective_finish
- Completion freeze (actual_completion_date overrides computed_finish)

Dependency type semantics (all lag values are in calendar days):
- FS: successor.start >= predecessor.effective_finish + 1 + lag
- SS: successor.start >= predecessor.computed_start + lag
- FF: successor.finish >= predecessor.effective_finish + lag
       => successor.start >= (that finish) - (cycle - 1) in successor's calendar
- SF: successor.finish >= predecessor.computed_start + lag
       => successor.start >= (that finish) - (cycle - 1) in successor's calendar

Backward pass for critical path / float lives in critical_path.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from .errors import StructuralError
from .locations import weekday_code
from .logging_config import get_logger
from .models import Project, Task

_log = get_logger(__name__)


@dataclass
class ScheduledTask:
    """Computed schedule data for one task."""

    task_id: str
    computed_start: date
    computed_finish: date
    effective_finish: date  # computed_finish + delay_days, or actual_completion_date if complete


def run_schedule(project: Project) -> dict[str, ScheduledTask]:
    """Compute start / finish / effective_finish for every task.

    Returns a dict keyed by task ID. Includes both leaf tasks and parent rollups.
    """
    schedule: dict[str, ScheduledTask] = {}

    # Compute leaves first in topological order
    leaves = [t for t in project.tasks if not project.has_subtasks(t.id)]
    ordered_leaves = _topological_order(leaves, project)

    for task in ordered_leaves:
        scheduled = _schedule_leaf(task, project, schedule)
        schedule[task.id] = scheduled

    # Roll up parents (any task that has children)
    parents = [t for t in project.tasks if project.has_subtasks(t.id)]
    # Parents may have parents themselves; iterate until stable
    while True:
        progress = False
        for parent in parents:
            if parent.id in schedule:
                continue
            children = project.children_of(parent.id)
            if all(c.id in schedule for c in children):
                child_schedules = [schedule[c.id] for c in children]
                start = min(s.computed_start for s in child_schedules)
                finish = max(s.computed_finish for s in child_schedules)
                effective = max(s.effective_finish for s in child_schedules)
                schedule[parent.id] = ScheduledTask(
                    task_id=parent.id,
                    computed_start=start,
                    computed_finish=finish,
                    effective_finish=effective,
                )
                progress = True
        if not progress:
            break

    _log.info("Scheduled %d tasks for project %s", len(schedule), project.project.id)
    return schedule


def _schedule_leaf(task: Task, project: Project, scheduled: dict[str, ScheduledTask]) -> ScheduledTask:
    """Compute start/finish for a leaf task."""
    if task.cycle_time_days is None or task.cycle_time_days < 1:
        raise StructuralError(f"Leaf task {task.id} has invalid cycle_time_days")

    # Determine floors (max of manual_start_date and dependency-driven starts)
    floors: list[date] = []
    if task.manual_start_date is not None:
        floors.append(task.manual_start_date)

    for dep in task.dependencies:
        pred = scheduled.get(dep.id)
        if pred is None:
            continue  # validation should catch this
        floor = _dependency_start_floor(task, dep, pred, project)
        floors.append(floor)

    if not floors:
        raise StructuralError(f"Task {task.id} has no anchor (unanchored)")

    raw_start = max(floors)
    computed_start = _snap_to_working_day(raw_start, task, project)
    computed_finish = _compute_finish(task, computed_start, project)

    # Effective finish: completion freezes; otherwise computed + delay_days
    if task.is_complete and task.actual_completion_date is not None:
        effective_finish = task.actual_completion_date
    else:
        effective_finish = _add_days_in_calendar(
            computed_finish, task.delay_days, task.calendar_mode, task.completion_location, project,
        )

    return ScheduledTask(
        task_id=task.id,
        computed_start=computed_start,
        computed_finish=computed_finish,
        effective_finish=effective_finish,
    )


def _compute_finish(task: Task, start: date, project: Project) -> date:
    """Compute finish date for a leaf task starting on `start`. Inclusive cycle time."""
    return _add_days_in_calendar(
        start, task.cycle_time_days - 1, task.calendar_mode, task.completion_location, project,
    )


def _dependency_start_floor(
    task: Task, dep, pred: ScheduledTask, project: Project,
) -> date:
    """Compute the earliest start for `task` implied by one dependency on `pred`.

    Each dependency type produces a floor on the successor's start; the caller
    takes max() across all dependency floors (and manual_start_date / parent floors).
    """
    cycle = task.cycle_time_days or 1
    lag = dep.lag_days
    dep_type = dep.type

    if dep_type == "FS":
        # Successor starts the day after predecessor's effective finish + lag.
        return pred.effective_finish + timedelta(days=1 + lag)

    if dep_type == "SS":
        # Successor starts when predecessor starts (+ lag).
        return pred.computed_start + timedelta(days=lag)

    if dep_type == "FF":
        # Successor finishes when predecessor finishes (+ lag).
        # => successor.start = implied_finish - (cycle - 1) in successor's calendar
        implied_finish = pred.effective_finish + timedelta(days=lag)
        return _subtract_days_in_calendar(
            implied_finish, cycle - 1, task.calendar_mode, task.completion_location, project,
        )

    if dep_type == "SF":
        # Successor finishes when predecessor starts (+ lag). Rare.
        implied_finish = pred.computed_start + timedelta(days=lag)
        return _subtract_days_in_calendar(
            implied_finish, cycle - 1, task.calendar_mode, task.completion_location, project,
        )

    # Unknown type — defensive fallback to FS
    return pred.effective_finish + timedelta(days=1 + lag)


def _snap_to_working_day(d: date, task: Task, project: Project) -> date:
    """Snap a date forward to the next valid working day if the task is working-mode.

    Per DESIGN.md Q3 ("successor calendar mode governs at boundaries"): if the
    successor is a working-day task, its start must land on a working day of its
    own location's calendar. E-day tasks ignore this — they run every calendar day.
    """
    if task.calendar_mode != "working_days":
        return d
    work_week = set(project.settings.work_weeks.get(task.completion_location, []))
    holiday_dates = {h.date for h in project.settings.holidays.get(task.completion_location, [])}
    current = d
    safety = 0
    while (weekday_code(current) not in work_week or current in holiday_dates) and safety < 366:
        current += timedelta(days=1)
        safety += 1
    return current


def _add_days_in_calendar(
    start: date, days_to_add: int, calendar_mode: str, location: str, project: Project,
) -> date:
    """Add `days_to_add` days to `start` according to calendar mode and location."""
    if days_to_add <= 0:
        return start

    if calendar_mode == "e_days":
        return start + timedelta(days=days_to_add)

    # working_days: count forward, skipping non-working days and holidays
    work_week = set(project.settings.work_weeks.get(location, []))
    holiday_dates = {h.date for h in project.settings.holidays.get(location, [])}

    current = start
    remaining = days_to_add
    while remaining > 0:
        current += timedelta(days=1)
        if weekday_code(current) in work_week and current not in holiday_dates:
            remaining -= 1
    return current


def _subtract_days_in_calendar(
    end: date, days_to_subtract: int, calendar_mode: str, location: str, project: Project,
) -> date:
    """Symmetric inverse of _add_days_in_calendar: walk backward from `end`."""
    if days_to_subtract <= 0:
        return end

    if calendar_mode == "e_days":
        return end - timedelta(days=days_to_subtract)

    work_week = set(project.settings.work_weeks.get(location, []))
    holiday_dates = {h.date for h in project.settings.holidays.get(location, [])}

    current = end
    remaining = days_to_subtract
    while remaining > 0:
        current -= timedelta(days=1)
        if weekday_code(current) in work_week and current not in holiday_dates:
            remaining -= 1
    return current


def _topological_order(leaves: list[Task], project: Project) -> list[Task]:
    """Return leaves in topological order so each task's dependencies are scheduled first."""
    leaf_ids = {t.id for t in leaves}
    in_degree: dict[str, int] = {t.id: 0 for t in leaves}
    for t in leaves:
        for dep in t.dependencies:
            if dep.id in leaf_ids:
                in_degree[t.id] += 1

    queue = [t for t in leaves if in_degree[t.id] == 0]
    ordered: list[Task] = []
    while queue:
        task = queue.pop(0)
        ordered.append(task)
        for other in leaves:
            if any(d.id == task.id for d in other.dependencies):
                in_degree[other.id] -= 1
                if in_degree[other.id] == 0:
                    queue.append(other)

    if len(ordered) < len(leaves):
        # Cycle detected; return whatever we have. Validation catches this separately.
        ordered.extend(t for t in leaves if t not in ordered)
    return ordered
