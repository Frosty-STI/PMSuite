# HANDOFF -- PMSuite Gantt Builder

This document is the resume point for any fresh agent or developer picking up where we left off. Depth lives in the cross-referenced docs.

## Where we are right now

**Steps 7a+7b+7c are complete. Child task hierarchy is live in both Streamlit and Excel. The "Complete?" checkbox is live and the Playwright suite is 25/25 green. The backend has been feature-complete since Step 5. The app is a functional editing tool, not a read-only viewer.**

Latest commits (most recent first):

| Hash      | Step | Summary |
|-----------|------|---------|
| (pending) | 7c   | Child task hierarchy: Streamlit Add Child Task + Parent picker, Excel row grouping |
| `91695ac` | 7a+7b | Complete? checkbox + Playwright 25/25 green |
| `abecad1` | 7    | Step 7: Playwright UI verification suite (in progress) |
| (pending) | 6    | Streamlit editing surface, New Here? walkthrough, button descriptions, Executive Changes Summary |
| `2b24ce7` | 6a   | Step 6 editing API primitives (add/update/delete task, add/remove dependency) |
| `bc38ea7` | 5.6  | Restore compact Gantt timeline widths |
| `e0998d2` | 5.5  | Sort Gantt views chronologically |
| `0e838cc` | 5.4  | Harden Step 5 readiness before Streamlit editing |
| `309c66b` | 5.3  | Checkpoint 2: DAL rename, long-pole detection, Chart Key sheet, demo polish |
| `6dbc79a` | 5.2  | Documentation refresh for steps 1-5 |
| `c824203` | 5    | Full Option E Excel rendering + real holiday seeding |
| `38a85a2` | 4.5  | Baseline fields + Cycle Time (Days) header rename |
| `1829fa5` | 4    | Parent completion cascade with preserve-earlier-children rule |
| `f40e9dd` | 3    | Delay propagation engine with auto-catchup and undo |
| `3a61f29` | 2    | Full SS / FF / SF dependency types with lag |
| `e3bde5e` | 1    | Backward-pass CPM with total float and critical-path detection |
| `b7c357d` | doc  | Comprehensive design documentation (6 files) |
| `10a294d` | 0    | Walking-skeleton scaffold |

**120 tests passing** (95 backend ~0.8 sec + 25 Playwright ~4 min).

## What works today

### Backend (Steps 1-5, complete)

- **Forward-pass scheduling** with full FS / SS / FF / SF dependency types and positive/negative lag.
- **Backward-pass CPM** computes `total_float` for every leaf; long-pole critical set for display.
- **Per-task calendar mode** (`working_days` vs `e_days`), per-location work-weeks, per-location holidays.
- **Manual-start as floor** combined with dependency-driven starts; unanchored leaves are validation errors.
- **Parent / multi-level hierarchy** with rollup; parents inherit dependency/manual-start floors to descendants.
- **Dependencies on parent tasks** use the parent predecessor's rolled-up descendant schedule.
- **Cumulative `delay_days`** with audit `delay_log`. Manual and auto-catchup-on-load both flow through here.
- **Auto-catchup math:** Option B (per-task accurate, static). Fresh-project baseline initialization; idempotent within a day.
- **Completion semantics:** auto-fill date, freeze effective dates, parent cascade with preserve-earlier-children, undo within session.
- **Project baseline:** `set_project_baseline()` snapshots current dates into `baseline_start` / `baseline_finish` per task.
- **Atomic JSON I/O** with rotating snapshots.
- **Two-tier collect validation** (structural fails fast, logical collects).
- **Project-timezone timestamps** for saves, snapshots, `last_export`, and Excel filenames.
- **Editing API:** `add_task`, `update_task`, `delete_task`, `add_dependency`, `remove_dependency` with full invariant enforcement.

### Excel (Step 5, complete)

- 5 sheets: Chart Key & Info, Day View, Week View, Schedule Calculations, Critical Path Notes.
- Frozen-pane metadata: TASK ID, Name, Location, Cycle Time (Days), Baseline Start, Baseline Finish, Dependencies.
- Segmented bar colors (planned blue, completed green, delayed orange, overdue red).
- Critical-path dark-red stripe via top/bottom border.
- Today vertical line (thick black left border on every body cell in today's column).
- Multi-line date column headers with weekday, date, and holiday name(s) per location.
- Hierarchy-aware row order: parents above children (pre-order tree walk), chronological within siblings. Task IDs stable, not reordered.
- **Row grouping with outline levels** in Day View and Week View: child rows are collapsible under their parent via Excel's `+`/`-` toggle. Recursive levels for nested children (grandchild = level 2, etc.). Summary rows above groups.
- Indented task names in frozen-pane Name column reflecting hierarchy depth.
- Per-row weekend/holiday gap shading for working-day tasks; e-day tasks continuous.
- Parent summary bars in dark gray with critical inheritance.

### Streamlit UI (Step 6, complete)

- **Session state persistence** -- project, path, dirty flag, auto-catchup result survive reruns.
- **Task editing** -- expander-based editors with: name, location dropdown, calendar mode, cycle time, manual start date (checkbox toggle), delay days, parent picker (filtered to prevent cycles), completion checkbox wired to `mark_task_complete` cascade.
- **Dependency editing** -- per-task list of current predecessors with remove buttons; add-dependency form with type (FS/SS/FF/SF) and lag selection.
- **Add Task** -- form with auto-generated TASK-NNN ID, defaults to today for manual start. Includes **Parent task dropdown** to assign parent_id at creation time.
- **Add Child Task** -- button inside each task expander pre-fills parent_id, location, and calendar mode from the parent task. Creates arbitrarily deep nesting.
- **Hierarchy display** -- tasks displayed in pre-order tree walk (parent above children), with depth-based indentation in expander labels.
- **Delete Task** -- blocks when dependents/children exist, surfaces affected IDs.
- **Action buttons** with concise descriptions: Validate, Save, Build Excel, Set Baseline.
- **Dirty-state badge** -- "Save *" button styling + title badge when unsaved changes exist.
- **Browser beforeunload warning** -- JavaScript injection when dirty.
- **Auto-catchup-on-load prompt** -- Apply/Skip with dismissible banner, per-task detail expander, one-click undo.
- **Dependency Explanation expander** -- plain-language FS/SS/FF/SF descriptions.
- **New Project form** -- sidebar form with name, auto-slugged ID, timezone, default location.
- **Project switcher dialog** -- Cancel/Discard/Save & Switch when switching with unsaved changes.
- **Settings panel** -- sidebar toggles for auto_delay_on_load and keep_local_snapshots.
- **"New Here?" walkthrough** -- pale green banner with 10-step guide grounded in MASTERECAP Q1-Q35. Placeholder content; will be refreshed before shipping (Step 11).
- **Summary table** -- read-only dataframe overview above the task editors.
- **"Complete?" indicator** -- disabled checkbox on each collapsed task row (far right) reflecting `task.is_complete`. Session-state sync ensures it updates immediately on in-session completion changes.
- **Playwright verification** -- 25 tests across 10 classes verify all editing flows end-to-end. Automatic screenshot-on-failure. Run: `pytest tests/test_streamlit_playwright.py -m playwright`.

## Roadmap (remaining steps)

| Step | Status | Description |
|------|--------|-------------|
| 7a | **Complete** | **UI: "Complete?" checkbox on collapsed task expanders** -- read-only disabled checkbox in `st.columns([8, 2])` layout, session-state sync to fix Streamlit widget caching, URL query param project loading. |
| 7b | **Complete** | **Playwright UI verification** -- 25 tests across 10 classes, all green. Fixed subprocess pipe buffer deadlock, locator ambiguity from dependency text, and Streamlit checkbox off-viewport clicks. Screenshot-on-failure infrastructure. |
| 7c | **Complete** | **Child task hierarchy in Streamlit + Excel** -- (1) **Streamlit:** "Add Child Task" button inside each task expander (pre-fills parent_id, location, calendar mode). "Parent task" dropdown in Add Task form. Task list displayed in hierarchy order with depth indentation. Parent picker in task editor already existed. (2) **Excel:** `xlsxwriter` row grouping with `outline_level` on Day View and Week View. `outline_settings(symbols_below=False)` puts collapse toggles on the parent row above. Indented task names in frozen-pane Name column. Recursive levels for nested children. |
| 8 | Pending | **TI holiday calendar ingestion** -- replace library-seeded holidays with actual TI WW Holiday Calendar data from `C:\Users\Frosty\Documents\TI WW Holiday Calendar.xlsx`. Parse the Excel file, map each PMSuite site to its country column (DAL→USA, MLA→Malaysia, CLARK→Philippines, AIZU→Japan, FR-BIP→Germany, TIEMA→Malaysia, TIPI→Philippines, TAI→Taiwan), and seed site-specific holidays including company holidays and local observances. For DAL (USA column empty in calendar), keep the existing `holidays` library as fallback. Update demo project files with the real calendar data. |
| 9 | Pending | **Expand npde_demo.json** -- currently 13 tasks; target ~30-50 tasks modeling a generic NPDE program using public-domain semiconductor flow knowledge. |
| 10 | Pending | **Test backfill** -- broaden test_validation.py, add test_scheduler.py calendar math edge cases, test_locations.py, test_holidays.py, more test_excel_builder.py structural assertions, test_excel_visual.py (opt-in), test_performance.py (slow marker). |
| 11 | Pending | **Final Walkthrough Refresh** -- update the "New Here?" walkthrough content in `streamlit_app.py` to reflect the final shipped feature set, polish wording for non-technical users, and verify every step still matches the implemented behavior. Run after all other steps are complete. |

## Local layout

```
C:\Users\Frosty\PMSuite\
├── HANDOFF.md                        # this file
├── EXECUTIVE_CHANGES_SUMMARY.md      # every push with detailed explanations
├── MASTERECAP.md                     # all design decisions (Q1-Q35)
├── DESIGN.md                         # architecture-level rationale
├── API.md                            # Python API contract
├── JSONFILE.md                       # JSON schema reference
├── EXCELBUILDER.md                   # Excel output spec
├── STREAMLIT.md                      # UI spec
├── PLAYWRIGHT_SCREENING.md           # Playwright test design decisions & coverage
├── README.md
├── LICENSE                           # MIT
├── pyproject.toml
├── .gitignore
├── gantt_builder/
│   ├── __init__.py
│   ├── api.py                        # public API surface (re-exports all modules)
│   ├── baseline.py                   # set_project_baseline + BaselineResult
│   ├── completion.py                 # mark_task_complete, unmark, undo
│   ├── critical_path.py              # backward pass, long-pole detection
│   ├── delays.py                     # auto-catchup, manual delay, undo
│   ├── editing.py                    # add/update/delete task, add/remove dependency
│   ├── errors.py                     # GanttError hierarchy (17 exception types)
│   ├── excel_builder.py              # full Option E rendering (5 sheets)
│   ├── locations.py                  # 8-site enum, work-weeks, holiday seeding
│   ├── logging_config.py             # rotating file + stderr logger
│   ├── models.py                     # Pydantic v2 models (Project/Task/Dependency/Settings)
│   ├── project_io.py                 # atomic load/save with snapshots
│   ├── scheduler.py                  # forward-pass scheduler (FS/SS/FF/SF)
│   ├── time_utils.py                 # project-timezone helpers
│   └── validation.py                 # two-tier collect validation
├── ui/
│   ├── __init__.py
│   └── streamlit_app.py              # full editing surface (Step 6)
├── tests/                            # 12 backend test files (95 tests) + 2 Playwright files (23 tests)
│   ├── fixtures/
│   │   └── npde_playwright_test_fixture.json  # Playwright test fixture (past/future dates)
│   ├── playwright_helpers.py         # composable async helpers for Playwright tests
│   ├── test_streamlit_playwright.py  # 23 Playwright UI tests (10 classes, 18 flows)
│   ├── test_api.py                   # end-to-end pipeline
│   ├── test_baseline.py              # 5 tests
│   ├── test_completion.py            # 15 tests
│   ├── test_critical_path.py         # 8 tests
│   ├── test_delays.py                # 19 tests
│   ├── test_dependencies.py          # 12 tests
│   ├── test_editing.py               # 11 tests
│   ├── test_excel_builder.py         # structural assertions
│   ├── test_models.py                # pydantic validation
│   ├── test_project_io.py            # I/O round-trip
│   └── test_validation.py            # logical validation
├── examples/
│   ├── small_demo.json               # 7 tasks, DAL only, 27 US holidays
│   └── npde_demo.json                # 13 tasks, 5 locations, 173 holidays
├── scripts/                          # one-off migration/rebuild utilities
├── projects/                         # GITIGNORED -- user project JSONs
│   └── .backups/                     # rotating snapshots
├── output/                           # GITIGNORED -- generated Excel files
└── .logs/gantt_builder.log           # GITIGNORED -- rotating log
```

## The user's targeting

- **Demo audience:** external customers / cross-team handoff.
- **Path A (go-mode):** working through steps autonomously with checkpoint reviews at natural boundaries.
- **Public-web data only.** Never TI-internal information in the public repo.
- **Per-feature commits.** Each step lands as its own pushed commit.
- **License: MIT** (locked).
- **Real 2026-2027 holidays** already seeded into both demo projects.
- **Color palette: locked** per MASTERECAP Q26a.
- **Executive Changes Summary** (`EXECUTIVE_CHANGES_SUMMARY.md`) must be updated with every push.

## What a fresh agent should do on resume

1. Read `MASTERECAP.md` for the design contract and `HANDOFF.md` (this file) for current state.
2. Read `EXECUTIVE_CHANGES_SUMMARY.md` for the history of every push.
3. Run `pytest -q --ignore=tests/test_streamlit_playwright.py` from `C:\Users\Frosty\PMSuite` -- should show 95 backend tests passing. Optionally run `pytest tests/test_streamlit_playwright.py -m playwright` for the 25 Playwright UI tests (~4 min).
4. Check the roadmap above for the next pending step and start there.

## Critical knowledge for next agent

- **Git identity for commits** -- use inline `-c user.name="Frosty-STI" -c user.email="s1lv3rstreak@gmail.com"` per commit; do NOT modify the global git config.
- **`gh` CLI** is not on PATH; plain `git push` works against the existing remote.
- **Streamlit launch:** `python -m streamlit run ui\streamlit_app.py` (streamlit.exe isn't on PATH).
- **PowerShell prints stderr as red even on success** -- pip install warnings and Python logging both go through stderr but don't indicate errors. Always check the actual content / exit code.
- **Tests run from PowerShell** with `python -m pytest -q "C:\Users\Frosty\PMSuite\tests" --rootdir "C:\Users\Frosty\PMSuite"`.
- **Pydantic v2 model serialization** uses `model_dump(mode="json", exclude_defaults=False, exclude_none=False)` for canonical output. Every save updates `project.updated_at` automatically.
- **Demo project files get rewritten** when run through save_project -- this is intentional (canonical formatting + updated_at). Don't revert.
- **Color palette is locked** at MASTERECAP Q26a values. Don't redecorate without an explicit user ask.
- **MANDATORY: Update EXECUTIVE_CHANGES_SUMMARY.md with every push to GitHub.** Every commit that gets pushed must have a corresponding entry in `EXECUTIVE_CHANGES_SUMMARY.md` documenting what changed and why. Use the same format as existing entries: `## Push N -- hash -- date`, followed by a bold title, detailed explanation, and a "Why" paragraph. This is a non-negotiable requirement -- do not push without updating this file.

## Tone the user expects

- Crisp, decisive. They know what they want.
- One question at a time when ambiguity arises.
- Don't ask permission for things already authorized (push to GitHub, MIT license, per-feature commits).
- Don't pad. Respect their attention.
- Tell them which commit just landed and what to verify at checkpoints.
