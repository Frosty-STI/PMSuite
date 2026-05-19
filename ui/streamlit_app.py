"""Streamlit UI for PMSuite Gantt Builder.

Step 6: full editing surface - task add/edit/delete, dependency picker,
mark-complete wired to cascade, auto-catchup on load, dirty-state badge
with beforeunload warning, New Project form.

The JSON file remains the source of truth. This UI is a thin client over
the documented Python API (gantt_builder.api).
"""

from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from gantt_builder import api  # noqa: E402
from gantt_builder.errors import GanttError, ValidationFailure  # noqa: E402
from gantt_builder.locations import LOCATIONS, LOCATION_DISPLAY, DEFAULT_WORK_WEEKS  # noqa: E402
from gantt_builder.models import Project, ProjectMeta, Settings, Task  # noqa: E402


PROJECTS_DIR = ROOT / "projects"
EXAMPLES_DIR = ROOT / "examples"


# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------

def _init_session_state() -> None:
    defaults = {
        "project": None,
        "project_path": None,
        "dirty": False,
        "last_auto_catchup_result": None,
        "last_completion_result": None,
        "pending_switch_to": None,
        "show_new_project_form": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _mark_dirty() -> None:
    st.session_state.dirty = True


def _mark_clean() -> None:
    st.session_state.dirty = False
    st.session_state.last_auto_catchup_result = None
    st.session_state.last_completion_result = None


# ---------------------------------------------------------------------------
# beforeunload warning (injected when dirty)
# ---------------------------------------------------------------------------

def _inject_beforeunload(dirty: bool) -> None:
    if dirty:
        st.components.v1.html(
            """<script>
            window.parent._pmsuiteAllowReload = window.parent._pmsuiteAllowReload || false;
            window.parent.onbeforeunload = function() {
                if (window.parent._pmsuiteAllowReload) {
                    window.parent._pmsuiteAllowReload = false;
                    return undefined;
                }
                return "You have unsaved changes that will be lost.";
            };
            </script>""",
            height=0,
        )
    else:
        st.components.v1.html(
            "<script>window.parent.onbeforeunload = null;</script>",
            height=0,
        )


def _allow_rerun() -> None:
    st.components.v1.html(
        "<script>window.parent._pmsuiteAllowReload = true;</script>",
        height=0,
    )




# ---------------------------------------------------------------------------
# Project loading and switching
# ---------------------------------------------------------------------------

def _load_project(path: Path) -> bool:
    """Load a project into session state. Returns True on success."""
    try:
        project = api.load_project(path)
    except GanttError as exc:
        st.error(f"Failed to load: {exc.message}")
        return False
    st.session_state.project = project
    st.session_state.project_path = path
    _mark_clean()
    return True


def _list_project_files() -> list[str]:
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    project_files = sorted(PROJECTS_DIR.glob("*.json"))
    example_files = sorted(EXAMPLES_DIR.glob("*.json"))
    options = ["-- select --"]
    options += [f"projects/{p.name}" for p in project_files]
    options += [f"examples/{p.name}" for p in example_files]
    return options


def _resolve_path(selection: str) -> Path:
    if selection.startswith("projects/"):
        return PROJECTS_DIR / selection.split("/", 1)[1]
    return EXAMPLES_DIR / selection.split("/", 1)[1]


# ---------------------------------------------------------------------------
# New Project form
# ---------------------------------------------------------------------------

def _render_new_project_form() -> None:
    st.sidebar.subheader("New Project")
    with st.sidebar.form("new_project_form"):
        name = st.text_input("Project name", value="My Project")
        slug = st.text_input(
            "Project ID (auto-slugged)",
            value=name.upper().replace(" ", "-")[:20] if name else "MY-PROJECT",
        )
        timezone = st.text_input("Timezone", value="America/Chicago")
        default_loc = st.selectbox("Default location", LOCATIONS, index=0)
        submitted = st.form_submit_button("Create")

    if submitted and slug:
        slug_clean = slug.upper().strip()
        dest = PROJECTS_DIR / f"{slug_clean.lower()}.json"
        if dest.exists():
            st.sidebar.error(f"File already exists: {dest.name}")
            return

        now = datetime.now().astimezone()
        holidays_block = {}
        work_weeks_block = {}
        for loc in [default_loc]:
            holidays_block[loc] = []
            work_weeks_block[loc] = DEFAULT_WORK_WEEKS.get(loc, ["MON", "TUE", "WED", "THU", "FRI"])

        project = Project(
            project=ProjectMeta(
                id=slug_clean,
                name=name,
                timezone=timezone,
                created_at=now,
                updated_at=now,
            ),
            settings=Settings(
                holidays=holidays_block,
                work_weeks=work_weeks_block,
                next_task_id=1,
            ),
            tasks=[],
        )
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        api.save_project(project, dest)
        st.session_state.show_new_project_form = False
        _load_project(dest)
        st.rerun()


# ---------------------------------------------------------------------------
# Auto-catchup prompt
# ---------------------------------------------------------------------------

def _render_auto_catchup_prompt(project: Project) -> None:
    if not project.settings.auto_delay_on_load:
        return
    if not api.is_auto_catchup_pending(project):
        return
    if st.session_state.last_auto_catchup_result is not None:
        return

    preview = api.preview_auto_catchup(project)
    if not preview.was_applied:
        return

    st.warning(
        f"**Auto-catchup pending:** {len(preview.entries)} task(s) are overdue "
        f"(total +{preview.total_days_added} delay days). "
        f"Last check: {project.settings.last_auto_delay_run}"
    )
    col_apply, col_skip = st.columns(2)
    with col_apply:
        if st.button("Apply auto-catchup", type="primary"):
            result = api.apply_auto_catchup(project)
            st.session_state.last_auto_catchup_result = result
            _mark_dirty()
            st.rerun()
    with col_skip:
        if st.button("Skip for now"):
            st.session_state.last_auto_catchup_result = "skipped"
            st.rerun()


def _render_auto_catchup_banner() -> None:
    result = st.session_state.last_auto_catchup_result
    if result is None or result == "skipped":
        return

    st.success(
        f"Auto-catchup applied: {len(result.entries)} task(s), "
        f"+{result.total_days_added} total delay days."
    )
    with st.expander("View details"):
        for entry in result.entries:
            st.text(f"  {entry.task_id}: +{entry.days_added} day(s)")

    if st.button("Undo auto-catchup batch"):
        project = st.session_state.project
        reverted = api.undo_delay_batch(project, result)
        st.session_state.last_auto_catchup_result = None
        if len(reverted) < len(result.entries):
            st.warning(
                f"Reverted {len(reverted)} of {len(result.entries)} tasks. "
                "Some tasks were manually edited and could not be undone."
            )
        else:
            st.info(f"Reverted all {len(reverted)} tasks.")
        _mark_dirty()
        st.rerun()


# ---------------------------------------------------------------------------
# "New Here?" walkthrough
# ---------------------------------------------------------------------------

_WALKTHROUGH_CSS = """
<style>
div[data-testid="stExpander"] details[open] summary ~ div[data-testid="stExpanderDetails"] {
    background-color: #f0faf0;
}
</style>
"""

def _render_new_here() -> None:
    st.components.v1.html(
        '<div style="background:#e8f5e9;padding:2px 10px;border-radius:6px;'
        'display:inline-block;margin-bottom:4px">'
        '<span style="font-size:15px;font-weight:600;color:#2e7d32">'
        'New Here?  Click below for a walkthrough</span></div>',
        height=34,
    )
    with st.expander("Getting Started with PMSuite", expanded=False):
        st.markdown("""
**PMSuite builds Excel Gantt workbooks from structured JSON project files.**
Your JSON file is the single source of truth. The Excel workbook is a
read-only output artifact. This UI is a thin editing surface over the
JSON data.

---

**1. Load or create a project**
Pick an existing project from the sidebar dropdown, or click **New Project**
to create one. Your project files live locally in `projects/` and are never
pushed to GitHub. Rotating local snapshots provide crash recovery.
*(Design: Q12 pure-Python module, Q23 local data safety)*

**2. Add tasks**
Each task gets a system-generated `TASK-NNN` ID (you only provide the name).
IDs are sequential, never reused, and gaps are allowed. Choose a **calendar
mode** for each task: `e_days` for continuous processes like oven cycles, or
`working_days` for human-bound work like reports.
*(Design: Q1/Q2 per-task calendar mode, Q10 system-generated IDs)*

**3. Assign locations**
Every task requires a completion location from the 8-site enum (DAL,
FR-BIP, MLA, TIEMA, CLARK, TIPI, TAI, AIZU). Sites at UTC+8 or later
use a Sun-Thu work-week from the USA perspective. Holidays are tracked
per-location.
*(Design: Q19/Q20 USA-perspective work-week rule)*

**4. Set dependencies**
Link tasks with FS (Finish-to-Start), SS, FF, or SF dependency types.
Add positive lag to delay a successor or negative lag (lead) to let it
start early. Lag is counted in the predecessor's calendar; the successor
then snaps to its own calendar.
*(Design: Q3 successor's calendar governs, Q8 dependency types)*

**5. Build hierarchy**
Group tasks under a parent by setting the Parent field. Parent tasks
derive their duration from children -- do not set a cycle time on parents.
Parents can have their own dependencies and manual start dates, which act
as a floor for all descendants.
*(Design: Q7 multi-level tree, unlimited depth)*

**6. Validate**
Click **Validate** to run a two-tier check. Structural errors (malformed
data) fail fast; logical errors (circular deps, missing references,
unanchored tasks) are collected and shown together. Save always works
even with logical errors; Build Excel requires a clean validation.
*(Design: Q13 two-tier collect validation)*

**7. Set a baseline**
Click **Set Baseline** to snapshot each task's current computed start/finish
as the planned reference. The baseline never moves when delays or completions
shift the live schedule -- it represents the original plan for variance
reporting in the Excel output.
*(Design: Q27 baseline fields)*

**8. Track delays**
Delays accumulate in `delay_days` with a full audit trail. When you open
a project after missed days, the auto-catchup prompt computes how many days
each overdue task slipped and offers to apply the catch-up. You can undo the
batch within the session. Upstream delays do not inflate downstream
delay_days -- downstream tasks shift only via the dependency cascade.
*(Design: Q9 delay mechanics, Q11 per-task accurate catch-up, Q24 prompted
before applying)*

**9. Mark complete**
Check the Is Complete box to freeze a task's effective dates. Dependents
will then key off the actual completion date rather than the computed finish.
Completing a parent cascades to all descendants -- children with their own
earlier completion date keep their earlier date (real history is preserved).
*(Design: Q8 completion semantics, Q8d preserve-earlier-children)*

**10. Build Excel**
Click **Build Excel** to validate, schedule, and generate a timestamped
`.xlsx` workbook. The output contains 5 sheets: Chart Key & Info, Day View,
Week View, Schedule Calculations, and Critical Path Notes. Bars use
segmented cell coloring (blue=planned, green=complete, orange=delayed,
red=overdue). Rows sort chronologically by scheduled dates, not by task ID.
*(Design: Q14/Q15 Option E rendering, Q35 chronological row order)*
        """)


# ---------------------------------------------------------------------------
# Dependency explanation expander
# ---------------------------------------------------------------------------

def _render_dependency_explanation() -> None:
    with st.expander("Understanding Dependencies (FS / SS / FF / SF)"):
        st.markdown("""
**FS** (Finish-to-Start, default): The successor starts after the predecessor
finishes. Use this for sequential work.

**SS** (Start-to-Start): The successor starts when the predecessor starts.
Use this for parallel work that must begin together.

**FF** (Finish-to-Finish): The successor finishes when the predecessor
finishes. Use this for work that must complete in sync.

**SF** (Start-to-Finish): The successor finishes when the predecessor starts.
Rare but useful for shift-handoff patterns.

**Lag:** Positive lag delays the successor by N days. Negative lag (lead) lets
the successor begin before the predecessor's anchor event. Lag is counted in
the **predecessor's** calendar mode.
        """)


# ---------------------------------------------------------------------------
# Task table (editable via individual task expanders)
# ---------------------------------------------------------------------------

def _render_task_table(project: Project) -> None:
    task_ids = [t.id for t in project.tasks]
    task_labels = {t.id: f"{t.id} - {t.name}" for t in project.tasks}

    for i, task in enumerate(project.tasks):
        is_parent = project.has_subtasks(task.id)
        prefix = "[P] " if is_parent else "    "
        complete_mark = " [done]" if task.is_complete else ""
        label = f"{prefix}{task.id} -- {task.name}{complete_mark}"
        if task.parent_id:
            label += f"  (child of {task.parent_id})"

        with st.expander(label, expanded=False):
            _render_task_editor(project, task, i, task_ids, task_labels, is_parent)


def _render_task_editor(
    project: Project,
    task: Task,
    idx: int,
    task_ids: list[str],
    task_labels: dict[str, str],
    is_parent: bool,
) -> None:
    col1, col2 = st.columns(2)

    with col1:
        new_name = st.text_input("Name", value=task.name, key=f"name_{task.id}")
        loc_options = LOCATIONS
        loc_idx = loc_options.index(task.completion_location) if task.completion_location in loc_options else 0
        new_location = st.selectbox(
            "Location",
            loc_options,
            index=loc_idx,
            format_func=lambda x: f"{x} - {LOCATION_DISPLAY.get(x, x)}",
            key=f"loc_{task.id}",
        )
        new_calendar = st.selectbox(
            "Calendar Mode",
            ["working_days", "e_days"],
            index=0 if task.calendar_mode == "working_days" else 1,
            key=f"cal_{task.id}",
        )

    with col2:
        if not is_parent:
            new_cycle = st.number_input(
                "Cycle Time (Days)",
                min_value=1,
                value=task.cycle_time_days or 1,
                key=f"cycle_{task.id}",
            )
        else:
            st.text("Cycle Time: (derived from children)")
            new_cycle = None

        has_manual_start = st.checkbox(
            "Has manual start date",
            value=task.manual_start_date is not None,
            key=f"has_mstart_{task.id}",
        )
        if has_manual_start:
            new_manual_start = st.date_input(
                "Manual Start Date",
                value=task.manual_start_date or date.today(),
                key=f"mstart_{task.id}",
            )
        else:
            new_manual_start = None

        new_delay = st.number_input(
            "Delay Days",
            min_value=0,
            value=task.delay_days,
            key=f"delay_{task.id}",
        )

    # Parent picker
    potential_parents = ["(none)"] + [
        tid for tid in task_ids
        if tid != task.id and tid not in project.all_descendant_ids(task.id)
    ]
    current_parent_idx = 0
    if task.parent_id and task.parent_id in potential_parents:
        current_parent_idx = potential_parents.index(task.parent_id)
    new_parent = st.selectbox(
        "Parent",
        potential_parents,
        index=current_parent_idx,
        key=f"parent_{task.id}",
    )
    new_parent_id = None if new_parent == "(none)" else new_parent

    # Completion
    st.divider()
    comp_col1, comp_col2 = st.columns(2)
    with comp_col1:
        new_complete = st.checkbox(
            "Is Complete",
            value=task.is_complete,
            key=f"complete_{task.id}",
        )
    with comp_col2:
        if new_complete:
            default_comp_date = task.actual_completion_date or date.today()
            new_comp_date = st.date_input(
                "Actual Completion Date",
                value=default_comp_date,
                key=f"compdate_{task.id}",
            )
        else:
            new_comp_date = None
            if task.actual_completion_date:
                st.caption("Completion date will be cleared.")

    # Dependencies
    st.divider()
    st.markdown("**Dependencies (predecessors)**")
    existing_deps = list(task.dependencies)

    for dep_idx, dep in enumerate(existing_deps):
        dcol1, dcol2, dcol3, dcol4 = st.columns([3, 2, 2, 1])
        with dcol1:
            dep_label = task_labels.get(dep.id, dep.id)
            st.text(dep_label)
        with dcol2:
            st.text(f"Type: {dep.type}")
        with dcol3:
            st.text(f"Lag: {dep.lag_days}")
        with dcol4:
            if st.button("X", key=f"remdep_{task.id}_{dep.id}"):
                api.remove_dependency(project, task.id, dep.id)
                _mark_dirty()
                st.rerun()

    # Add dependency
    available_deps = [
        tid for tid in task_ids
        if tid != task.id and not any(d.id == tid for d in task.dependencies)
    ]
    if available_deps:
        with st.form(f"add_dep_form_{task.id}"):
            adcol1, adcol2, adcol3 = st.columns([3, 2, 2])
            with adcol1:
                new_dep_id = st.selectbox(
                    "Add predecessor",
                    available_deps,
                    format_func=lambda x: task_labels.get(x, x),
                    key=f"newdep_{task.id}",
                )
            with adcol2:
                new_dep_type = st.selectbox(
                    "Type",
                    ["FS", "SS", "FF", "SF"],
                    key=f"newdeptype_{task.id}",
                )
            with adcol3:
                new_dep_lag = st.number_input(
                    "Lag (days)",
                    value=0,
                    key=f"newdeplag_{task.id}",
                )
            if st.form_submit_button("Add dependency"):
                try:
                    api.add_dependency(
                        project, task.id, new_dep_id,
                        type=new_dep_type, lag_days=int(new_dep_lag),
                    )
                    _mark_dirty()
                    st.rerun()
                except GanttError as exc:
                    st.error(f"{exc.error_code}: {exc.message}")

    # Apply task field changes
    st.divider()
    if st.button(f"Apply changes to {task.id}", key=f"apply_{task.id}", type="primary"):
        try:
            kwargs = {
                "name": new_name,
                "completion_location": new_location,
                "calendar_mode": new_calendar,
                "delay_days": new_delay,
                "parent_id": new_parent_id,
            }
            if not is_parent:
                kwargs["cycle_time_days"] = new_cycle

            # Handle manual_start_date: Streamlit date_input returns a date
            # even when we want None, so we need the user to explicitly clear it.
            if new_manual_start is not None:
                kwargs["manual_start_date"] = new_manual_start

            # Handle completion toggle
            if new_complete and not task.is_complete:
                api.mark_task_complete(project, task.id, completion_date=new_comp_date)
                st.session_state.last_completion_result = task.id
            elif not new_complete and task.is_complete:
                api.unmark_task_complete(project, task.id)
            elif new_complete and task.is_complete and new_comp_date != task.actual_completion_date:
                kwargs["actual_completion_date"] = new_comp_date
                kwargs["is_complete"] = True

            api.update_task(project, task.id, **kwargs)
            _mark_dirty()
            st.success(f"Updated {task.id}")
            st.rerun()
        except GanttError as exc:
            st.error(f"{exc.error_code}: {exc.message}")
        except Exception as exc:
            st.error(f"Error: {exc}")

    # Delete button
    if st.button(f"Delete {task.id}", key=f"delete_{task.id}", type="secondary"):
        try:
            api.delete_task(project, task.id)
            _mark_dirty()
            st.rerun()
        except GanttError as exc:
            st.error(f"{exc.error_code}: {exc.message}")


# ---------------------------------------------------------------------------
# Add Task button
# ---------------------------------------------------------------------------

def _render_add_task(project: Project) -> None:
    with st.expander("Add new task"):
        with st.form("add_task_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Task name", value="New task")
                location = st.selectbox(
                    "Location", LOCATIONS,
                    format_func=lambda x: f"{x} - {LOCATION_DISPLAY.get(x, x)}",
                )
                calendar = st.selectbox("Calendar mode", ["working_days", "e_days"])
            with col2:
                cycle = st.number_input("Cycle time (days)", min_value=1, value=1)
                manual_start = st.date_input("Manual start date", value=date.today())

            if st.form_submit_button("Add task", type="primary"):
                try:
                    task = api.add_task(
                        project,
                        name=name,
                        completion_location=location,
                        calendar_mode=calendar,
                        cycle_time_days=cycle,
                        manual_start_date=manual_start,
                    )
                    _mark_dirty()
                    st.success(f"Added {task.id} - {task.name}")
                    st.rerun()
                except GanttError as exc:
                    st.error(f"{exc.error_code}: {exc.message}")
                except Exception as exc:
                    st.error(f"Error: {exc}")


# ---------------------------------------------------------------------------
# Action buttons: Validate, Save, Build Excel
# ---------------------------------------------------------------------------

def _render_action_buttons(project: Project, path: Path) -> None:
    # --- Button row (all level) ---
    col_validate, col_save, col_build, col_baseline = st.columns(4)

    with col_validate:
        if st.button("Validate", use_container_width=True):
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
                    if err.affected_tasks:
                        st.caption(f"Affected: {', '.join(err.affected_tasks)}")

    with col_save:
        if st.button("Save", use_container_width=True, key="save_btn"):
            try:
                api.save_project(project, path)
                _mark_clean()
                st.success(f"Saved to {path.name}")
                _allow_rerun()
                st.rerun()
            except GanttError as exc:
                st.error(f"Save failed: {exc.message}")
            except Exception as exc:
                st.error(f"Save failed: {exc}")

    with col_build:
        if st.button("Build Excel", use_container_width=True):
            try:
                with st.spinner("Building Excel..."):
                    output_path = api.build_excel(project)
                _mark_dirty()
                st.success(f"Built: {output_path}")
            except ValidationFailure as exc:
                st.error("Cannot build - validation errors:")
                for err in exc.errors:
                    st.error(f"  {err.error_code}: {err.message}")
                    if err.affected_tasks:
                        st.caption(f"  Affected: {', '.join(err.affected_tasks)}")
            except GanttError as exc:
                st.error(f"Build failed: {exc.message}")

    with col_baseline:
        if st.button("Set Baseline", use_container_width=True):
            try:
                with st.spinner("Setting baseline..."):
                    result = api.set_project_baseline(project)
                _mark_dirty()
                st.session_state["_baseline_just_set"] = True
                st.success(f"Baseline set for {result.count_baselined} task(s), {len(result.tasks_skipped)} skipped.")
            except GanttError as exc:
                st.error(f"Baseline failed: {exc.message}")

    # --- Descriptions below buttons (all level) ---
    desc_validate, desc_save, desc_build, desc_baseline = st.columns(4)

    with desc_validate:
        st.caption("Check for errors (circular deps, missing data, etc.)")
    with desc_save:
        st.caption("Write changes to the JSON file on disk")
    with desc_build:
        st.caption("Generate a timestamped .xlsx Gantt workbook")
    with desc_baseline:
        st.caption("Record each task's current scheduled start and finish as the original baseline dates")

    # -- Below the button row: dirty indicator and contextual info -----------

    if st.session_state.dirty:
        st.markdown(
            '<span style="color:#E68A00; font-style:italic;">Unsaved changes</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span style="color:#2E8B57; font-style:italic;">All changes saved</span>',
            unsafe_allow_html=True,
        )

    if st.session_state.get("_baseline_just_set"):
        st.session_state["_baseline_just_set"] = False
        st.info(
            "**What just happened?** Each task's computed start and finish "
            "dates were saved as the baseline — your original plan. Future "
            "delays or completions will shift the live schedule, but the "
            "baseline stays fixed so you can see how far off-plan you are "
            "in the Excel output."
        )
        st.markdown(
            "**Related settings in the sidebar:**\n"
            "- **Auto-delay on load** — when you open a project after missed days, "
            "PMSuite can automatically calculate how many days each overdue task "
            "slipped and offer to record that delay. This keeps your schedule "
            "current without manual data entry.\n"
            "- **Keep local snapshots** — every time you save, PMSuite stores a "
            "backup copy of your project file. If you ever need to recover a "
            "previous version, these snapshots have you covered. Set to 0 to disable."
        )


# ---------------------------------------------------------------------------
# Summary task table (read-only overview above the editors)
# ---------------------------------------------------------------------------

def _render_summary_table(project: Project) -> None:
    if not project.tasks:
        st.info("No tasks yet. Use 'Add new task' below to get started.")
        return

    tasks_data = []
    for t in project.tasks:
        dep_str = ", ".join(
            f"{d.id}[{d.type}{', lag ' + str(d.lag_days) if d.lag_days else ''}]"
            for d in t.dependencies
        ) if t.dependencies else ""
        tasks_data.append({
            "TASK ID": t.id,
            "Name": t.name,
            "Location": t.completion_location,
            "Calendar": t.calendar_mode,
            "Cycle": t.cycle_time_days if t.cycle_time_days is not None else "(parent)",
            "Manual Start": str(t.manual_start_date) if t.manual_start_date else "",
            "Parent": t.parent_id or "",
            "Dependencies": dep_str,
            "Complete": "Yes" if t.is_complete else "",
            "Delay": t.delay_days if t.delay_days else "",
        })

    st.dataframe(tasks_data, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def _render_sidebar() -> str | None:
    with st.sidebar:
        st.header("Project")

        if st.button("New Project"):
            st.session_state.show_new_project_form = not st.session_state.show_new_project_form

        if st.session_state.show_new_project_form:
            _render_new_project_form()

        options = _list_project_files()
        current_path = st.session_state.project_path

        default_idx = 0
        if current_path is not None:
            for i, opt in enumerate(options):
                if opt != "-- select --":
                    if _resolve_path(opt) == current_path:
                        default_idx = i
                        break

        selection = st.selectbox("Open a project", options, index=default_idx)

        # Settings panel
        if st.session_state.project is not None:
            st.divider()
            project = st.session_state.project
            st.subheader("Settings")
            new_auto_delay = st.checkbox(
                "Auto-delay on load",
                value=project.settings.auto_delay_on_load,
                key="setting_auto_delay",
            )
            if new_auto_delay != project.settings.auto_delay_on_load:
                project.settings.auto_delay_on_load = new_auto_delay
                _mark_dirty()

            new_snapshots = st.number_input(
                "Keep local snapshots",
                min_value=0,
                max_value=100,
                value=project.settings.keep_local_snapshots,
                key="setting_snapshots",
            )
            if new_snapshots != project.settings.keep_local_snapshots:
                project.settings.keep_local_snapshots = new_snapshots
                _mark_dirty()

    return selection


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="PMSuite Gantt Builder", layout="wide")
    _init_session_state()

    # Sidebar and project selection
    selection = _render_sidebar()

    # Handle project switching
    if selection and selection != "-- select --":
        new_path = _resolve_path(selection)
        current_path = st.session_state.project_path

        if current_path is None or new_path != current_path:
            if st.session_state.dirty:
                st.warning("You have unsaved changes in the current project.")
                col_cancel, col_discard, col_save_switch = st.columns(3)
                with col_cancel:
                    if st.button("Cancel"):
                        _allow_rerun()
                        st.rerun()
                with col_discard:
                    if st.button("Discard & Switch"):
                        _load_project(new_path)
                        _allow_rerun()
                        st.rerun()
                with col_save_switch:
                    if st.button("Save & Switch"):
                        try:
                            api.save_project(
                                st.session_state.project,
                                st.session_state.project_path,
                            )
                        except Exception as exc:
                            st.error(f"Save failed: {exc}")
                            return
                        _load_project(new_path)
                        _allow_rerun()
                        st.rerun()
                return
            else:
                _load_project(new_path)

    project = st.session_state.project
    path = st.session_state.project_path

    if project is None:
        st.title("PMSuite - Gantt Builder")
        st.info("Pick a project from the sidebar, or create a new one.")
        _render_new_here()
        return

    title = f"PMSuite - {project.project.id} - {project.project.name}"
    st.title(title)
    st.caption(f"{len(project.tasks)} tasks | Timezone {project.project.timezone}")

    _inject_beforeunload(st.session_state.dirty)

    # Walkthrough
    _render_new_here()

    # Auto-catchup prompt
    _render_auto_catchup_prompt(project)
    _render_auto_catchup_banner()

    # Action buttons
    _render_action_buttons(project, path)
    st.divider()

    # Dependency explanation
    _render_dependency_explanation()

    # Summary table
    _render_summary_table(project)
    st.divider()

    # Add task
    _render_add_task(project)

    # Task editors
    st.subheader("Edit Tasks")
    _render_task_table(project)


if __name__ == "__main__":
    main()
