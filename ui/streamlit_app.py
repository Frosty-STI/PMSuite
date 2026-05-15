"""Streamlit UI for PMSuite Gantt Builder.

Walking-skeleton: dropdown to pick a project from projects/, table preview of
tasks, Save and Build Excel buttons. Full editing surface (add/edit/delete
tasks, dependency editor, holiday editor, dirty-state badge, undo of auto-catchup)
to be added incrementally per DESIGN.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from gantt_builder import api  # noqa: E402
from gantt_builder.errors import GanttError, ValidationFailure  # noqa: E402


PROJECTS_DIR = ROOT / "projects"
EXAMPLES_DIR = ROOT / "examples"


def main() -> None:
    st.set_page_config(page_title="PMSuite Gantt Builder", layout="wide")
    st.title("PMSuite — Gantt Builder")

    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

    with st.sidebar:
        st.header("Project")
        project_files = sorted(PROJECTS_DIR.glob("*.json"))
        example_files = sorted(EXAMPLES_DIR.glob("*.json"))

        options = ["— select —"] + [f"projects/{p.name}" for p in project_files] + \
                  [f"examples/{p.name}" for p in example_files]
        selection = st.selectbox("Open a project", options)

    if selection == "— select —":
        st.info("Pick a project from the sidebar, or load an example to explore.")
        return

    if selection.startswith("projects/"):
        path = PROJECTS_DIR / selection.split("/", 1)[1]
    else:
        path = EXAMPLES_DIR / selection.split("/", 1)[1]

    try:
        with st.spinner(f"Loading {path.name}..."):
            project = api.load_project(path)
    except GanttError as exc:
        st.error(f"Failed to load: {exc.message}")
        return

    st.subheader(f"{project.project.id} — {project.project.name}")
    st.caption(f"{len(project.tasks)} tasks · timezone {project.project.timezone}")

    tasks_data = [{
        "TASK ID": t.id,
        "Name": t.name,
        "Location": t.completion_location,
        "Calendar": t.calendar_mode,
        "Cycle": t.cycle_time_days if t.cycle_time_days is not None else "(parent)",
        "Manual Start": t.manual_start_date.isoformat() if t.manual_start_date else "",
        "Parent": t.parent_id or "",
        "Dependencies": ", ".join(d.id for d in t.dependencies),
        "Complete": "✓" if t.is_complete else "",
        "Delay Days": t.delay_days,
    } for t in project.tasks]

    st.dataframe(tasks_data, use_container_width=True, hide_index=True)

    col_save, col_build, col_validate = st.columns(3)

    with col_validate:
        if st.button("Validate"):
            try:
                with st.spinner("Validating..."):
                    warnings = api.validate_project(project)
                if warnings:
                    for w in warnings:
                        st.warning(w)
                else:
                    st.success("Project is valid.")
            except ValidationFailure as exc:
                for err in exc.errors:
                    st.error(f"{err.error_code}: {err.message}")

    with col_save:
        if st.button("Save"):
            try:
                api.save_project(project, path)
                st.success(f"Saved to {path}")
            except GanttError as exc:
                st.error(f"Save failed: {exc.message}")

    with col_build:
        if st.button("Build Excel"):
            try:
                with st.spinner("Building Excel..."):
                    output_path = api.build_excel(project)
                st.success(f"Built: {output_path}")
            except ValidationFailure as exc:
                st.error("Cannot build — validation errors:")
                for err in exc.errors:
                    st.error(f"  {err.error_code}: {err.message}")
            except GanttError as exc:
                st.error(f"Build failed: {exc.message}")


if __name__ == "__main__":
    main()
