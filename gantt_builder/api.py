"""Public API surface for PMSuite Gantt Builder.

This is the module Streamlit (and any other consumer) imports. It wraps the
internal modules and applies validation + scheduling at the right boundaries.

API operations raise GanttError subclasses on failure; callers can serialize
errors to the structured envelope via `.to_envelope()` for UI display.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .critical_path import compute_critical_path
from .excel_builder import build_excel as _build_excel
from .logging_config import get_logger
from .models import LastExport, Project
from .project_io import load_project as _load, save_project as _save
from .scheduler import run_schedule
from .validation import validate_project as _validate

_log = get_logger(__name__)


def load_project(path: str | Path) -> Project:
    """Load a project from JSON. Raises StructuralError on parse failure."""
    return _load(path)


def save_project(project: Project, path: str | Path) -> None:
    """Atomically save the project JSON. Updates `project.updated_at`."""
    _save(project, path)


def validate_project(project: Project) -> list[str]:
    """Run logical-tier validation. Raises ValidationFailure if errors exist.

    Returns a list of warning strings (non-fatal). Save / Build operations call
    this internally at appropriate boundaries.
    """
    return _validate(project)


def schedule_project(project: Project):
    """Run the forward pass scheduler. Returns a dict of task_id -> ScheduledTask."""
    return run_schedule(project)


def build_excel(project: Project, output_dir: str | Path | None = None) -> Path:
    """Validate, schedule, and write the Excel workbook. Returns the output path.

    Raises ValidationFailure if logical validation fails (Excel build is gated on
    clean validation per DESIGN.md Q13).
    """
    _validate(project)
    schedule = run_schedule(project)
    critical = compute_critical_path(project, schedule)
    output_path = _build_excel(project, schedule, critical, output_dir=output_dir)

    project.project.last_export = LastExport(
        path=str(output_path),
        at=datetime.now().astimezone(),
    )
    return output_path
