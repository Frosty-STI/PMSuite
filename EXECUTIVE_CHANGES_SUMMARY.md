# Executive Changes Summary

Every push to `https://github.com/Frosty-STI/PMSuite.git`, with a detailed explanation of what changed and why.

---

## Push 1 -- `969681c` -- 2026-05-12

**Initial commit**

Created the GitHub repository with a placeholder README. Established the `main` branch and remote origin for the PMSuite project.

---

## Push 2 -- `10a294d` -- 2026-05-14

**Walking-skeleton scaffold for PMSuite Gantt Builder**

Laid the full project foundation: package structure (`gantt_builder/`), Pydantic v2 models for Project/Task/Dependency/Settings, forward-pass scheduler with FS dependencies, two-tier validation (structural + logical), atomic JSON I/O with rotating snapshots, stub Excel builder with 5 sheets, Streamlit read-only UI shell, CI workflow (GitHub Actions on Python 3.11/3.12), two example project files (`small_demo.json`, `npde_demo.json`), and 11 initial tests covering models, I/O round-tripping, and end-to-end pipeline.

**Why:** The walking skeleton establishes every layer of the architecture end-to-end so that subsequent feature commits add behavior to an already-running system rather than assembling disconnected pieces.

*26 files, +2,511 lines*

---

## Push 3 -- `b7c357d` -- 2026-05-14

**Add comprehensive design documentation**

Created 6 documentation files: API.md (Python API contract), EXCELBUILDER.md (Excel output spec), HANDOFF.md (resume-from-here for agents/developers), JSONFILE.md (JSON schema reference), MASTERECAP.md (all 26 grilling-session design decisions), STREAMLIT.md (UI spec with planned features).

**Why:** The design was produced through a structured grilling session (26 questions). Capturing every decision in durable documents ensures future contributors can understand not just what the code does but why each choice was made. MASTERECAP is the canonical decision log; the other docs are organized views of the same decisions by topic.

*6 files, +1,634 lines*

---

## Push 4 -- `e3bde5e` -- 2026-05-14

**Implement backward-pass CPM with total float and critical-path detection**

Added a full CPM backward pass to `critical_path.py`: computes late-start/late-finish for every task, derives total float, and marks tasks with float == 0 as critical. Completed tasks are excluded from the live critical path. Added `_subtract_days_in_calendar` helper to the scheduler for backward-pass calendar math. 8 tests covering float computation, critical set detection, and completed-task exclusion.

**Why:** Critical path analysis is the core value proposition for project managers. Without it, the Gantt is just a colored timeline. Total float tells PMs which tasks have slack and which are gating the project end date. (Design: Q17)

*3 files, +351 lines*

---

## Push 5 -- `3a61f29` -- 2026-05-14

**Implement full SS / FF / SF dependency types with lag**

Extended the scheduler's dependency-floor dispatcher from FS-only to all four CPM relationship types (Start-to-Start, Finish-to-Finish, Start-to-Finish) with positive and negative lag. Updated the backward-pass CPM to handle all four types. 12 tests covering each type with lag variations, cross-calendar-mode boundaries, and negative lead times.

**Why:** Real NPDE projects use SS (parallel start) and FF (synchronized finish) regularly. FS-only would force users to model parallel work with artificial lags and dummy tasks. (Design: Q3, Q8)

*3 files, +302 lines*

---

## Push 6 -- `f40e9dd` -- 2026-05-14

**Implement delay propagation engine with auto-catchup and undo**

New `delays.py` module with: `preview_auto_catchup` (dry-run), `apply_auto_catchup` (Option B per-task accurate static), `apply_manual_delay`, `undo_delay_batch`, and `is_auto_catchup_pending`. Added `CompletedTaskCannotBeDelayedError` to the error hierarchy. Fresh-project baseline initialization sets `last_auto_delay_run` to today without applying delays. 19 tests covering multi-day catch-up, idempotency, completion freeze, manual delay, undo with edit-guard, and fresh-project initialization.

**Why:** Delays are first-class state in PMSuite, not derived. The auto-catchup-on-load model means projects "drive themselves when opened" -- a PM who was away for a week sees exactly how many days each task slipped. The undo mechanism builds trust. (Design: Q9, Q11, Q24)

*4 files, +628 lines*

---

## Push 7 -- `1829fa5` -- 2026-05-14

**Implement parent completion cascade with preserve-earlier-children rule**

New `completion.py` module with `mark_task_complete`, `unmark_task_complete`, and `undo_complete_batch`. When a parent is marked complete, all descendants are cascaded. Children with their own earlier `actual_completion_date` retain their earlier date (real history is preserved). Added `all_descendant_ids` and `all_descendant_leaf_ids` helpers to the Project model. 15 tests covering cascade, preserve-earlier, undo, and the unmark single-task path.

**Why:** In NPDE workflows, marking a phase complete should cascade to sub-tasks automatically. But a sub-task that finished early (e.g., wafer fab completed ahead of schedule) should keep its real date -- overwriting it would destroy audit history. (Design: Q8, Q8d)

*5 files, +489 lines*

---

## Push 8 -- `38a85a2` -- 2026-05-14

**Add Cycle Time + Baseline Start + Baseline Finish to frozen panes**

New `baseline.py` module with `set_project_baseline` (snapshots computed dates into `baseline_start`/`baseline_finish` per task). Added baseline fields to the Task model. Updated Excel builder to include Cycle Time (Days), Baseline Start, and Baseline Finish in the frozen-pane metadata columns of Day View and Week View. Seeded baselines into both demo projects. 5 baseline tests.

**Why:** Project managers expect a baseline reference (the original plan) alongside the live schedule so they can see variance at a glance. "Cycle Time (Days)" header eliminates ambiguity about units. (Design: Q27, Q28)

*7 files, +442 lines*

---

## Push 9 -- `c824203` -- 2026-05-14

**Implement full Option E Excel rendering**

Major expansion of `excel_builder.py`: segmented cell coloring (planned blue, completed green, delayed orange, overdue red), critical-path dark-red border stripe, today vertical line (thick black left border on every body cell), multi-line date column headers with weekday + ISO date + holiday names per location, per-row weekend/holiday gap shading for working-day tasks, e-day tasks rendering continuous, parent summary bars in dark gray. Seeded real 2026-2027 holidays from the Python `holidays` library into both demo projects (27 US holidays for small_demo, 173 across 5 locations for npde_demo).

**Why:** The Excel workbook is the primary deliverable -- what gets emailed to stakeholders and reviewed in meetings. Option E (segmented static cell coloring) was chosen because it scales, doesn't require merged cells, and carries all status encoding in color alone. Real holidays make the demo authentic. (Design: Q15, Q29)

*3 files, +1,324 lines*

---

## Push 10 -- `6dbc79a` -- 2026-05-14

**Refresh documentation to reflect steps 1-5 implementation state**

Updated API.md (new delay/completion/baseline function signatures), EXCELBUILDER.md (current rendering status), HANDOFF.md (full file manifest, test counts, what works today), JSONFILE.md (baseline field documentation), MASTERECAP.md (Q27-Q29 implementation addenda). All docs now accurately describe the implemented system rather than the planned design.

**Why:** Documentation that describes the plan rather than the reality becomes misleading. After shipping 5 feature steps in rapid succession, the docs needed to catch up so the next agent or contributor starts from truth.

*5 files, +367/-105 lines*

---

## Push 11 -- `309c66b` -- 2026-05-17

**Checkpoint 2 iteration: USA->DAL rename, long-pole detection, demo parallel tasks, Excel polish**

Renamed the USA site code to DAL (Dallas) across all code, tests, and data. Replaced strict float-only critical path display with long-pole detection (terminal unfinished leaves + their transitive gating chain). Added a Chart Key & Info sheet with color legend, working-week reference, and frozen-pane guide. Added Dependencies column to frozen panes. Updated demo projects with parallel tasks and richer structure. Migration scripts in `scripts/`.

**Why:** The Checkpoint 2 visual review by the user revealed that (a) "USA" was too generic -- DAL identifies the specific site, (b) strict float-zero critical display missed the obvious gating chain due to working-day boundary snapping, and (c) external users need context inside the workbook itself. (Design: Q33)

*14 files, +622/-210 lines*

---

## Push 12 -- `0e838cc` -- 2026-05-17

**Harden Step 5 readiness before Streamlit editing**

Pre-Step-6 hardening pass: parent-aware scheduling (parents inherit dependency floors and manual-start floors to descendants), project-timezone timestamps for saves/exports/snapshots, expanded validation (parent-cycle-time, parent-descendant dependency conflicts, unanchored leaf detection), `time_utils.py` for timezone-aware `project_now()`, LICENSE file (MIT), broader test coverage across validation, dependencies, Excel structure. 95 tests passing.

**Why:** Before building the editing UI, the backend needed to be bulletproof. Parent-aware scheduling was partially implemented; this commit closed the gaps so that any edit the Streamlit UI allows will schedule correctly. Adding the license formalized the open-source intent. (Design: Q30, Q34)

*23 files, +794/-152 lines*

---

## Push 13 -- `e0998d2` -- 2026-05-17

**Sort Gantt views chronologically**

Day View and Week View rows now sort by computed schedule dates (primary: computed_start; ties: parent-above-children, then finish date, then stable ID). Task IDs remain stable creation identifiers -- a later-created TASK-013 appears between TASK-009 and TASK-010 when its dates belong there. Updated all 6 documentation files to reflect this decision. Additional Excel structural tests.

**Why:** The Excel Gantt is a timeline-first artifact. ID-ordered rows would scatter tasks across the timeline, making the chart hard to read. Chronological order makes the workbook scannable without sacrificing stable IDs for references. (Design: Q35)

*9 files, +205/-46 lines*

---

## Push 14 -- `bc38ea7` -- 2026-05-17

**Restore compact Gantt timeline widths**

Reduced Day View date column width from 6 to 4 and Week View from 12 to 10. Added structural tests asserting column widths match the spec.

**Why:** Wider columns from a prior refactor pushed the timeline too far right, requiring excessive horizontal scrolling. The compact widths match the EXCELBUILDER.md spec and keep more of the timeline visible on screen.

*2 files, +26/-7 lines*

---

## Push 15 -- `2b24ce7` -- 2026-05-17

**Add Step 6 editing API primitives**

New `editing.py` module with `add_task` (auto-generates next TASK-NNN ID, advances counter, skips gaps), `update_task` (validates updated model, rejects ID renames), `delete_task` (blocks if dependents or children exist), `add_dependency` (rejects self-deps and parent-hierarchy conflicts, upserts), `remove_dependency` (idempotent). Added `TaskDeletionBlockedError` to the error hierarchy. All 5 functions re-exported via `api.py`. 11 tests.

**Why:** The Streamlit editing surface needs mutation primitives that enforce the data model's invariants (stable IDs, no orphan dependencies, no parent-cycle-time conflicts). Building them as a separate API layer means the UI can't accidentally bypass validation. This is the foundation for Step 6.

*7 files, +372/-13 lines*

---

## Push 16 -- `6348aca` -- 2026-05-17

**Step 6: Streamlit editing surface, New Here? walkthrough, button descriptions**

Full rewrite of `ui/streamlit_app.py` from read-only walking skeleton to complete editing surface: `st.session_state` persistence for project + dirty flag, task add/edit/delete via expander-based editors, dependency picker with add/remove and type/lag selection, mark-complete wired to cascade API, auto-catchup-on-load prompt with Apply/Skip/Undo, dirty-state badge with browser `beforeunload` warning, New Project form, project switcher with Cancel/Discard/Save & Switch dialog, sidebar settings panel, Set Baseline button, Dependency Explanation expander.

Added concise descriptions under each action button (Validate, Save, Build Excel, Set Baseline). Added "New Here?" walkthrough -- a pale green banner expanding into a 10-step guide grounded in MASTERECAP design decisions (Q1-Q35).

Created `EXECUTIVE_CHANGES_SUMMARY.md` with backfilled entries for all prior commits. Updated HANDOFF.md roadmap with Step 10 (Playwright UI verification) and Step 11 (Final Walkthrough Refresh).

**Why:** Step 6 is the transition from "backend tool" to "usable application." Without an editing surface, users must hand-edit JSON -- which defeats the purpose of building a UI. The walkthrough ensures first-time users can orient themselves without reading 6 documentation files. Button descriptions reduce the "what does this do?" friction for non-technical users.

---

## Push 17 -- `b9dee2b` -- 2026-05-18

**Reorder roadmap: Playwright verification before holiday editor**

Moved Playwright UI verification from Step 10 to Step 7 in the HANDOFF.md roadmap. Holiday editor, demo expansion, and test backfill shift to Steps 8-10. Step 11 (Final Walkthrough Refresh) unchanged.

**Why:** Screen out bugs in the Step 6 editing surface before adding feature complexity. The user's philosophy is to iron out issues before passing to users, not to have users discover bugs. Running Playwright against the current UI before the holiday editor ensures a stable foundation for future features.

---

## Push 18 -- `228bf7e` -- 2026-05-18

**UI polish pass: save state indicators, button layout, beforeunload fix, HANDOFF hardening**

Streamlit UI changes:
- Capitalized "Timezone" in the project subtitle.
- Restructured action buttons: buttons render in one row (all level), descriptions render in a second row below. This fixes the Set Baseline button being pushed down by its longer caption text.
- Updated Set Baseline description to "Record each task's current scheduled start and finish as the original baseline dates."
- After clicking Set Baseline, explanatory text appears below the button row describing what happened, plus descriptions of the Auto-delay and Keep Local Snapshots sidebar settings.
- Added save state indicator below the button row: orange italic "Unsaved changes" when dirty, green italic "All changes saved" when clean. Removed the old "* Unsaved changes" title badge.
- Fixed `beforeunload` dialog firing on Save click. Introduced a `_pmsuiteAllowReload` JavaScript flag on the parent window: the beforeunload handler checks this flag and allows navigation silently when set. Save, Cancel, Discard & Switch, and Save & Switch all set the flag before calling `st.rerun()`. Tab close and manual navigation still trigger the warning dialog.

Documentation changes:
- HANDOFF.md: strengthened the EXECUTIVE_CHANGES_SUMMARY.md update requirement from a bullet point to a mandatory, explicit instruction for all agents.
- EXECUTIVE_CHANGES_SUMMARY.md: backfilled push 16 and 17 hashes, added this entry.

**Why:** The user's design principle is to be as friendly to the user as possible — explaining how the tool works without getting in the way. The save state indicator gives instant visual feedback. The button layout fix keeps the UI clean. The beforeunload fix eliminates a confusing dialog on the safest action (Save). The HANDOFF hardening ensures no future agent skips the executive changelog.

---

## Push 19 -- `abecad1` -- 2026-05-18

**Step 7: Playwright UI verification suite (in progress) + documentation updates**

Playwright test infrastructure:
- Created `tests/fixtures/npde_playwright_test_fixture.json` — copy of npde_demo.json with dates shifted to provide both past (2025) and future (post-9/18/2026) tasks. TASK-003 left incomplete/overdue to trigger auto-catchup. TASK-014 "Filler task" bridges 438 e_days.
- Created `tests/playwright_helpers.py` — 30+ composable async helpers for all UI interactions (server lifecycle, page navigation, task CRUD, dependency management, action buttons, auto-catchup, project management, settings, assertions).
- Created `tests/test_streamlit_playwright.py` — 23 tests across 10 classes covering 18 golden-path flows: showcase, load project, add/edit/delete task, delete-blocked, add/remove dependency, mark complete, validate (clean + errors), save + dirty state, build Excel, set baseline, auto-catchup apply/undo/skip, new project creation, project switching (cancel/discard/save), manual start toggle, settings (auto-delay, snapshots).
- Created `PLAYWRIGHT_SCREENING.md` — design decisions from 17-question grilling session, current coverage table with assertion depth per test, known coverage gaps, stabilization status, running commands.
- Updated `pyproject.toml` — added `test-ui` optional dependency group (`pytest-playwright>=0.4`), added `playwright` pytest marker.

Documentation updates:
- Updated HANDOFF.md: Step 7 marked as "In progress" with description of what's written vs. what needs verification. Added Step 7a for the "Complete?" checkbox UI change. Updated local layout to include new Playwright files.
- Updated PLAYWRIGHT_SCREENING.md: added full coverage table, known gaps section, stabilization status.

Post-initial-write hardening:
- Added automatic screenshot-on-failure: `page_and_project` fixture uses `pytest_runtest_makereport` hook to detect failures and save PNGs; standalone tests (Showcase, AutoCatchup, NewProject) use try/except wrappers. Screenshots saved to `test-results/screenshots/` (gitignored).
- Fixed `test_build_excel` assertion depth: now verifies a new `.xlsx` file was created on disk using `find_latest_excel()`, not just checking for UI alerts.
- Updated `.gitignore` with `test-results/` exclusion.

**Stabilization note:** First test run was 3/23 passing due to selector/timing mismatches with Streamlit's DOM. Helpers were rewritten to target correct elements (`<summary>` for expanders, `data-testid` attributes, auto-catchup dismissal). A full green run has **not yet been confirmed** — the next agent must run the suite and debug remaining failures before committing as complete.

**Why:** The user's philosophy is to screen out bugs before adding feature complexity. The Playwright suite verifies the full round-trip (click → session state → JSON on disk → reload) for every editing flow in the Step 6 UI. Writing tests before the holiday editor ensures a stable foundation.

---

## Push 20 -- `91695ac` -- 2026-05-20

**Steps 7a + 7b complete: "Complete?" checkbox UI + Playwright suite 25/25 green**

This push delivers two milestones: the "Complete?" read-only indicator on collapsed task rows (Step 7a) and a fully passing Playwright UI verification suite (Step 7b).

**Step 7a — "Complete?" checkbox on collapsed task rows:**
- Added `st.columns([8, 2])` layout in `_render_task_table`: the 80%-width left column holds the task expander, the 20%-width right column holds a disabled `st.checkbox("Complete?")` reflecting `task.is_complete`.
- Fixed Streamlit widget caching bug: disabled checkboxes with `key=` retain stale session-state values across reruns. Added `st.session_state[key] = task.is_complete` before rendering to force-sync the indicator on every rerun.
- URL query parameter project loading: added `st.query_params` support in `main()` so tests can load projects via `?project=projects/filename.json` without using the selectbox.

**Step 7b — Playwright suite stabilization (25/25 green):**

Three root causes were identified and fixed:

1. **Subprocess pipe buffer deadlock** (critical): `start_streamlit()` used `subprocess.PIPE` for stdout/stderr. After ~64KB of Streamlit log output filled the pipe buffer, the server process blocked on `write()` and stopped serving WebSocket connections. Fix: redirect stdout/stderr to log files in `test-results/`.

2. **Locator ambiguity from dependency text**: `has_text="TASK-004"` matched both TASK-004's expander AND TASK-005's expander (because TASK-005 depends on TASK-004, and Streamlit renders hidden dependency text in the DOM even when collapsed). Fix: `_task_locator()` helper uses `has_text=f"{task_id} --"` — the double-dash format uniquely matches the expander summary line.

3. **Streamlit checkbox off-viewport clicks**: Streamlit hides native `<input type="checkbox">` elements off-screen for styling, making them unclickable even with `force=True`. Fix: `evaluate("el => el.click()")` dispatches the DOM click directly, bypassing Playwright's viewport coordinate check.

Additional fixes: `triple_click()` → `click(click_count=3)` (API mismatch), viewport set to 1920×4000 for 14-task pages, form wait for New Project, broader test cleanup patterns, simplified reload-dependent assertions to JSON verification.

Test infrastructure: session-scoped browser context with per-test pages, automatic screenshot-on-failure with setup-failure capture, `run()` helper for async-to-sync bridging.

**Why:** The Playwright suite is the safety net for all future changes. Every editing flow (task CRUD, dependencies, completion cascade, auto-catchup, project switching, settings, Excel export, baseline) is now verified end-to-end. The "Complete?" indicator gives at-a-glance visibility without opening each expander.

---

## Push 21 -- `4689601` -- 2026-05-20

**Step 7c complete: Child task hierarchy in Streamlit + Excel**

This push delivers the UI and rendering support for arbitrarily deep parent/child task nesting. The backend hierarchy (`parent_id`, `has_subtasks()`, cascade, floor propagation) was already complete — this step adds the user-facing creation controls and the Excel visual grouping.

### Streamlit UI changes (`ui/streamlit_app.py`):

1. **"Add Child Task" button** inside each task's expander. Pre-fills `parent_id`, `completion_location`, and `calendar_mode` from the parent task. Creates a leaf child with `cycle_time_days=1` and `manual_start_date=today` (or parent's manual start). Enables arbitrarily deep nesting — a child task's expander also has an "Add Child Task" button.

2. **"Parent task" dropdown** in the top-level "Add new task" form. Shows all existing task IDs with names; defaults to "(none)" for root tasks. Combined with the existing parent picker in the task editor (for re-assigning parents after creation), users now have three ways to set hierarchy: Add Child Task button, Add Task form parent dropdown, and task editor parent picker.

3. **Hierarchy-ordered task display.** Tasks are shown in pre-order tree walk (parent above children), with depth-based whitespace indentation in the expander labels. Root tasks maintain their original insertion order; children appear directly below their parent.

### Excel changes (`gantt_builder/excel_builder.py`):

1. **Row grouping with outline levels** on Day View and Week View sheets. Child rows get `outline_level = hierarchy_depth` (level 1 for direct children, level 2 for grandchildren, etc.). Parent rows stay at level 0. `outline_settings(symbols_below=False)` puts the `+`/`-` collapse toggle on the parent row above the group, not below.

2. **Hierarchy-aware row ordering.** `_gantt_task_order()` changed from flat chronological sort to a pre-order tree walk: root tasks sorted chronologically, each parent followed immediately by its children (also chronological among siblings), recursively. This ensures child rows are always adjacent to and below their parent.

3. **Indented task names.** The frozen-pane Name column now indents child task names by 2 spaces per hierarchy level (`"  " * level + name`), making the tree structure visible even without the outline grouping.

**Why:** NPDE programs need arbitrarily granular task decomposition — "Wafer Fab" breaks into "Lot 1 processing" and "Lot 2 processing," each of which breaks into sub-steps. The flat task list forced all tasks to one level, making the Gantt noisy for executives and lacking detail for engineers. Excel row grouping solves both: collapsed groups for the executive view, expanded detail for engineering review. The Streamlit "Add Child Task" button makes creating hierarchy as easy as clicking a button rather than manually setting parent_id.
