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

## Push 16 -- (pending) -- 2026-05-17

**Step 6: Streamlit editing surface, New Here? walkthrough, button descriptions**

Full rewrite of `ui/streamlit_app.py` from read-only walking skeleton to complete editing surface: `st.session_state` persistence for project + dirty flag, task add/edit/delete via expander-based editors, dependency picker with add/remove and type/lag selection, mark-complete wired to cascade API, auto-catchup-on-load prompt with Apply/Skip/Undo, dirty-state badge with browser `beforeunload` warning, New Project form, project switcher with Cancel/Discard/Save & Switch dialog, sidebar settings panel, Set Baseline button, Dependency Explanation expander.

Added concise descriptions under each action button (Validate, Save, Build Excel, Set Baseline). Added "New Here?" walkthrough -- a pale green banner expanding into a 10-step guide grounded in MASTERECAP design decisions (Q1-Q35).

Created `EXECUTIVE_CHANGES_SUMMARY.md` with backfilled entries for all prior commits. Updated HANDOFF.md roadmap with Step 10 (Playwright UI verification) and Step 11 (Final Walkthrough Refresh).

**Why:** Step 6 is the transition from "backend tool" to "usable application." Without an editing surface, users must hand-edit JSON -- which defeats the purpose of building a UI. The walkthrough ensures first-time users can orient themselves without reading 6 documentation files. Button descriptions reduce the "what does this do?" friction for non-technical users.
