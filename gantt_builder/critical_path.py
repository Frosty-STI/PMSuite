"""Critical-path computation (CPM-style).

Forward + backward pass to compute total float for every task. Tasks with
total_float == 0 are on the critical path. Completed tasks are excluded from
the live critical path (their effective_finish is fixed and they can no longer
slip), but a snapshot is captured to project.history at completion time.

Handles all four dependency types (FS / SS / FF / SF) with lag. The backward
pass derives a maximum allowable LF for each predecessor from each successor's
LS or LF depending on the dependency type:

- FS: pred.LF <= succ.LS - 1 - lag
- SS: pred.LS <= succ.LS - lag   (translated to LF via cycle in pred's calendar)
- FF: pred.LF <= succ.LF - lag
- SF: pred.LS <= succ.LF - lag   (translated to LF via cycle in pred's calendar)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from .logging_config import get_logger
from .models import Project, Task
from .scheduler import (
    ScheduledTask,
    _add_days_in_calendar,
    _subtract_days_in_calendar,
    _topological_order,
)

_log = get_logger(__name__)


@dataclass
class CriticalPathResult:
    """Result of CPM analysis for a project."""

    project_end: date | None
    critical_task_ids: set[str]
    total_float: dict[str, int]  # task_id -> total float in days
    latest_start: dict[str, date] = field(default_factory=dict)
    latest_finish: dict[str, date] = field(default_factory=dict)


def compute_critical_path(project: Project, schedule: dict[str, ScheduledTask]) -> CriticalPathResult:
    """Compute project end, latest start/finish, total float, and critical tasks.

    Algorithm:
    1. Project end = max effective_finish across all scheduled tasks.
    2. Backward pass over leaves in REVERSE topological order:
       - For each leaf T, LF = min over successors S of (S's LS - 1 - lag),
         or project_end if T has no successors.
       - LS = LF - (cycle_time - 1) in T's calendar mode.
    3. Total float = LS - computed_start (in calendar days).
    4. Critical = (float == 0) AND (not is_complete).
    5. Parent tasks inherit critical status from any critical descendant.
    """
    if not schedule:
        return CriticalPathResult(
            project_end=None, critical_task_ids=set(), total_float={},
        )

    leaves = [t for t in project.tasks if not project.has_subtasks(t.id)]
    leaf_ids = {t.id for t in leaves}

    project_end = max(s.effective_finish for s in schedule.values())

    # Build successors map: task_id -> list of leaf tasks that depend on it
    successors: dict[str, list[Task]] = {tid: [] for tid in leaf_ids}
    for t in leaves:
        for dep in t.dependencies:
            if dep.id in leaf_ids:
                successors[dep.id].append(t)

    # Backward pass in REVERSE topological order
    topo_order = _topological_order(leaves, project)
    latest_finish: dict[str, date] = {}
    latest_start: dict[str, date] = {}

    for task in reversed(topo_order):
        succ_list = successors.get(task.id, [])
        cycle = task.cycle_time_days or 1
        lf_constraints: list[date] = []

        for succ in succ_list:
            for dep in succ.dependencies:
                if dep.id != task.id:
                    continue
                succ_ls = latest_start.get(succ.id)
                succ_lf = latest_finish.get(succ.id)
                if succ_ls is None or succ_lf is None:
                    continue

                if dep.type == "FS":
                    # pred.LF <= succ.LS - 1 - lag
                    lf_constraints.append(succ_ls - timedelta(days=1 + dep.lag_days))
                elif dep.type == "SS":
                    # pred.LS <= succ.LS - lag  =>  pred.LF <= (that) + (cycle - 1) in pred's calendar
                    pred_ls_max = succ_ls - timedelta(days=dep.lag_days)
                    pred_lf_max = _add_days_in_calendar(
                        pred_ls_max, cycle - 1, task.calendar_mode, task.completion_location, project,
                    )
                    lf_constraints.append(pred_lf_max)
                elif dep.type == "FF":
                    # pred.LF <= succ.LF - lag
                    lf_constraints.append(succ_lf - timedelta(days=dep.lag_days))
                elif dep.type == "SF":
                    # pred.LS <= succ.LF - lag  =>  pred.LF <= (that) + (cycle - 1)
                    pred_ls_max = succ_lf - timedelta(days=dep.lag_days)
                    pred_lf_max = _add_days_in_calendar(
                        pred_ls_max, cycle - 1, task.calendar_mode, task.completion_location, project,
                    )
                    lf_constraints.append(pred_lf_max)
                else:
                    # defensive fallback — FS semantics
                    lf_constraints.append(succ_ls - timedelta(days=1 + dep.lag_days))
                break

        lf = min(lf_constraints) if lf_constraints else project_end
        latest_finish[task.id] = lf

        ls = _subtract_days_in_calendar(
            lf, cycle - 1, task.calendar_mode, task.completion_location, project,
        )
        latest_start[task.id] = ls

    # Total float = LS - computed_start (in calendar days). Critical = float == 0 and not complete.
    total_float: dict[str, int] = {}
    critical: set[str] = set()
    for task in leaves:
        s = schedule.get(task.id)
        ls = latest_start.get(task.id)
        if s is None or ls is None:
            total_float[task.id] = 0
            continue
        tf = (ls - s.computed_start).days
        total_float[task.id] = max(0, tf)
        if tf == 0 and not task.is_complete:
            critical.add(task.id)

    # Parents inherit critical status from any critical descendant
    parents = [t for t in project.tasks if project.has_subtasks(t.id)]
    for parent in parents:
        descendants = _all_descendant_leaf_ids(project, parent.id)
        if not descendants:
            total_float[parent.id] = 0
            continue
        if any(d in critical for d in descendants):
            total_float[parent.id] = 0
            critical.add(parent.id)
        else:
            descendant_floats = [total_float.get(d, 0) for d in descendants]
            total_float[parent.id] = min(descendant_floats) if descendant_floats else 0

    _log.info(
        "CPM for project %s: end=%s, %d critical tasks, %d leaves analyzed",
        project.project.id, project_end, len(critical), len(leaves),
    )

    return CriticalPathResult(
        project_end=project_end,
        critical_task_ids=critical,
        total_float=total_float,
        latest_start=latest_start,
        latest_finish=latest_finish,
    )


def _all_descendant_leaf_ids(project: Project, task_id: str) -> list[str]:
    """Return IDs of all leaf descendants of the given task."""
    result: list[str] = []
    stack = [task_id]
    while stack:
        current = stack.pop()
        children = project.children_of(current)
        if not children:
            if current != task_id:
                result.append(current)
            continue
        for child in children:
            if project.has_subtasks(child.id):
                stack.append(child.id)
            else:
                result.append(child.id)
    return result
