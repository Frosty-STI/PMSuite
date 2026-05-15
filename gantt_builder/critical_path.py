"""Critical-path computation (CPM-style).

Walking-skeleton: stubbed. Returns no critical tasks and zero float for all tasks.
Full implementation will perform a backward pass from project_end (derived from
the latest leaf's effective_finish) and mark tasks with total_float == 0 as critical.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import Project
from .scheduler import ScheduledTask


@dataclass
class CriticalPathResult:
    """Result of CPM analysis."""

    project_end: object  # date or None
    critical_task_ids: set[str]
    total_float: dict[str, int]  # task_id -> total float in days


def compute_critical_path(project: Project, schedule: dict[str, ScheduledTask]) -> CriticalPathResult:
    """Compute project end date and total float for every task. Mark critical tasks.

    Walking-skeleton: returns project_end derived from latest effective_finish but
    leaves the critical set empty and float values at 0. Full backward pass to be
    implemented per DESIGN.md.
    """
    if not schedule:
        return CriticalPathResult(project_end=None, critical_task_ids=set(), total_float={})

    project_end = max(s.effective_finish for s in schedule.values())

    # TODO: implement backward pass for total float (DESIGN.md Q17)
    total_float = {tid: 0 for tid in schedule}
    critical_ids: set[str] = set()

    return CriticalPathResult(
        project_end=project_end,
        critical_task_ids=critical_ids,
        total_float=total_float,
    )
