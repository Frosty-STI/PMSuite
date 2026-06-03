# HANDOFF -- PMSuite Gantt Builder

This document is the resume point for any fresh agent or developer picking up where we left off. Depth lives in the cross-referenced docs.

## Where we are right now

**Step 8 (Interactive Gantt) is rendering and functional. The Frappe Gantt custom component is live inside the Streamlit UI with status-colored bars, dependency arrows, click/drag interactions, and sidebar editing. The horizontal scrollbar bug is fixed. Two known bugs remain: (1) the right-click context menu no longer appears on task bars, and (2) the overall visual design needs further polish. The Playwright suite is 25/25 green. The backend has been feature-complete since Step 5. 95 backend tests pass.**

Latest commits (most recent first):

| Hash      | Step | Summary |
|-----------|------|---------|
| `eb4e5c9` | 8a   | Fix horizontal scrollbar clipped by iframe boundary |
| `a2b9b53` | 8    | Step 8: Interactive Gantt rendering + visual redesign (3 bugs fixed, CSS rewrite) |
| `42ce709` | 7d   | UI polish: uniform task labels, hierarchy indentation, immediate completion toggle, parent editor consistency |
| `d6e3b6b` | 7c+  | NPDE demo hierarchy, auto-clear parent cycle_time, UI polish attempts, README rewrite |
| `4689601` | 7c   | Child task hierarchy: Streamlit Add Child Task + Parent picker, Excel row grouping |
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
- **"New Here?" walkthrough** -- pale green banner with 10-step guide grounded in MASTERECAP Q1-Q35. Placeholder content; will be refreshed before shipping (Step 12).
- **Summary table** -- read-only dataframe overview above the task editors.
- **"Complete?" indicator** -- disabled checkbox on each collapsed task row (far right) reflecting `task.is_complete`. Session-state sync ensures it updates immediately on in-session completion changes.
- **Playwright verification** -- 25 tests across 10 classes verify all editing flows end-to-end. Automatic screenshot-on-failure. Run: `pytest tests/test_streamlit_playwright.py -m playwright`.

### Interactive Gantt (Step 8, rendering with known bugs)

- **Frappe Gantt custom component** -- React wrapper around `frappe-gantt` v1.2.2, built with Vite, served as a Streamlit custom component from `components/gantt_chart/frontend/build/`.
- **Two-tab layout** -- "Visualized Project Editing" (Gantt chart + sidebar) and "Text Project Editing" (expander editors). Both tabs operate on the same `st.session_state.project`.
- **Toolbar** -- Add Task button, Day/Week/Month view mode switcher, Today button, search box, double-click hint text.
- **Status-colored bars** -- steel blue (planned), teal-green (completed), amber (delayed), signal red (overdue), dark charcoal (parent). Critical path bars have dark red border.
- **Click/drag interactions** -- click selects task (opens sidebar editor), drag moves start date, drag edge resizes duration. Events fire back to Python via `Streamlit.setComponentValue()`.
- **Sidebar editor** -- 30% right panel with full task editing (same fields as the text editor), plus Add Child Task and Delete Task buttons.
- **Context menu** -- right-click on a bar shows Edit / Mark Complete / Add Child / Delete.
- **Search highlighting** -- tasks matching the query stay fully opaque; non-matching tasks fade to 20% opacity.
- **Today marker** -- dark vertical line with date badge.
- **Dependency arrows** -- quiet gray at 60% opacity, rounded joins.
- **CSS theme** -- "Industrial Precision" theme with CSS variable overrides for Frappe Gantt, proper specificity matching, subtle grid, refined popup.
- **Design spec:** [INTERACTIVE_SURFACE.md](INTERACTIVE_SURFACE.md) (38 grilling-session decisions).

#### Known bugs (next session priorities)

1. **Right-click context menu no longer appears on task bars** -- After the scrollbar iframe height fix, right-clicking a Gantt task bar no longer shows the custom context menu (Edit / Mark Complete / Add Child / Delete). The context menu code itself is intact in `GanttComponent.jsx` — `_handleContext` is bound to the SVG's `contextmenu` event in `_buildGantt()`, calls `e.preventDefault()`, reads `e.target.closest(".bar-wrapper")`, and sets React state to render the menu div at `position: fixed` with `e.clientX/Y` coordinates. **Hypotheses to investigate:**
   - The `document.addEventListener("click", this._handleDocClick)` may fire on right-click in some browsers, immediately dismissing the context menu after it appears. Test by adding a `console.log` in `_handleDocClick` to confirm whether it fires during right-click.
   - The context menu div renders inside the iframe with `position: fixed` using `e.clientX/Y`. With the iframe now 20px taller than before (796 vs 776), the coordinate system may have shifted. Check whether the menu renders but is positioned outside the visible area.
   - The `_handleContext` handler may not be binding to the SVG element at all — check whether `el.querySelector("svg")` returns null in `_buildGantt()`.
   - **Debug path:** Add a temporary `console.log("contextmenu fired", e.target)` at the top of `_handleContext` and right-click a bar in headed mode (`HEADED=1`). If it logs, the handler is binding — check positioning. If it doesn't log, the SVG selector or event binding is the issue.

2. **Visual design needs further polish** -- The current theme is functional but needs refinement: bar label readability on narrow bars, grid density in Day view, weekend/holiday shading, hover/selected state contrast. **Use `/frontend-design` for the visual iteration pass.**

## Roadmap (remaining steps)

| Step | Status | Description |
|------|--------|-------------|
| 8 | **In progress** | **Interactive Gantt editing surface** -- Rendering works. Scrollbar fixed. Two bugs remain (context menu + visual polish; see "Known bugs" above). Design spec: [INTERACTIVE_SURFACE.md](INTERACTIVE_SURFACE.md). |
| 9 | Pending | **TI holiday calendar ingestion** -- replace library-seeded holidays with actual TI WW Holiday Calendar data from `C:\Users\Frosty\Documents\TI WW Holiday Calendar.xlsx`. |
| 10 | Pending | **Expand npde_demo.json** -- currently 17 tasks; target ~30-50 tasks modeling a generic NPDE program. |
| 11 | Pending | **Test backfill** -- broaden test_validation.py, add test_scheduler.py calendar math edge cases, test_locations.py, test_holidays.py, more test_excel_builder.py structural assertions, test_excel_visual.py (opt-in), test_performance.py (slow marker). |
| 12 | Pending | **Final Walkthrough Refresh** -- update "New Here?" walkthrough content to reflect the final shipped feature set. |

## Step 8 -- bugs fixed across sessions

### Bug 4: Horizontal scrollbar clipped by iframe boundary (fixed)

**Symptom:** The horizontal scrollbar on `.gantt-container` existed but was obscured by the iframe bottom border. Users could not scroll the Gantt chart horizontally.

**Root cause:** `StreamlitComponentBase.componentDidMount()` and `.componentDidUpdate()` both call `Streamlit.setFrameHeight()` with no arguments, which auto-detects from `document.body.scrollHeight`. This height (776px) did not include the 12px horizontal scrollbar rendered below the content. The iframe was sized to exactly the content height, clipping the scrollbar by 8px.

**Fix:** Skipped `super.componentDidMount()` and `super.componentDidUpdate()` in `GanttComponent` (they only called `setFrameHeight()` with no args). Added `_setFrameHeightWithScrollbar()` helper that measures `.gantt-container.offsetHeight + 20` and passes the explicit value. Both `_buildGantt()` and the `else` branch in `componentDidUpdate` now call this helper.

**Verified:** Playwright diagnostic confirmed `room_below: 12px` (was -8px), programmatic scrolling works (`scrollLeft` 700 → 1000), and the Gantt renders correctly in Week and Day view modes.

Three earlier rendering bugs were diagnosed and fixed using Playwright-based automation to inspect the component iframe:

### Bug 1: `classList.add()` crash (fatal)

**Symptom:** Gantt iframe rendered at 0 height. No chart visible.

**Root cause:** `_prepare_gantt_data()` in `streamlit_app.py` builds CSS class strings with spaces (e.g., `"overdue critical"`, `"planned parent-task"`). Frappe Gantt's `Bar.refresh()` at `bar.js:16` calls `this.group.classList.add(this.task.custom_class)`, which throws `InvalidCharacterError` because `classList.add()` rejects tokens containing spaces.

**Fix:** `GanttComponent.jsx` temporarily monkey-patches `DOMTokenList.prototype.add` during Gantt initialization to split space-separated tokens into individual class names, restored in a `finally` block.

### Bug 2: `calc(100vh - 200px)` in iframe (height collapse)

**Symptom:** Even the error message from Bug 1 was invisible — the container had negative max-height.

**Root cause:** The container used `maxHeight: "calc(100vh - 200px)"`. Inside a Streamlit component iframe, `100vh` equals the iframe's own height (initially 0), producing `calc(0px - 200px) = -200px`.

**Fix:** Removed `maxHeight` and `overflowY: auto` from the container. Let `Streamlit.setFrameHeight()` handle iframe sizing naturally.

### Bug 3: CSS specificity loss (bars invisible)

**Symptom:** Bars rendered as white rectangles on white background — invisible.

**Root cause:** Frappe Gantt's CSS uses `.gantt .bar-wrapper .bar { fill: var(--g-bar-color) }` (specificity 0,3,0). The theme CSS used `.gantt .bar { fill: #8FB6E1 }` (0,2,0) which loses. The CSS variable `--g-bar-color` defaulted to `#fff` (white).

**Fix:** Complete CSS rewrite. Override Frappe's CSS variables at `:root` level. All bar-fill rules now match Frappe specificity (`.gantt .bar-wrapper.STATUS .bar`).

## Local layout

```
C:\Users\Frosty\PMSuite\
├── HANDOFF.md                        # this file
├── EXECUTIVE_CHANGES_SUMMARY.md      # every push with detailed explanations
├── INTERACTIVE_SURFACE.md            # Step 8 design spec (38 grilling-session decisions)
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
├── components/                       # Step 8 -- Streamlit custom components
│   ├── __init__.py
│   └── gantt_chart/
│       ├── __init__.py               # st_gantt() Python wrapper
│       └── frontend/
│           ├── package.json
│           ├── vite.config.js
│           ├── index.html
│           ├── src/
│           │   ├── index.jsx          # entry point (withStreamlitConnection)
│           │   ├── GanttComponent.jsx # main component (StreamlitComponentBase)
│           │   └── gantt-theme.css    # Industrial Precision CSS theme
│           ├── build/                 # Vite production build (COMMITTED for runtime)
│           └── node_modules/          # GITIGNORED
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
│   └── streamlit_app.py              # full editing surface (Step 6) + Gantt tabs (Step 8)
├── tests/                            # 12 backend test files (95 tests) + 2 Playwright files (25 tests)
│   ├── fixtures/
│   │   └── npde_playwright_test_fixture.json
│   ├── playwright_helpers.py
│   ├── test_streamlit_playwright.py
│   ├── test_api.py
│   ├── test_baseline.py
│   ├── test_completion.py
│   ├── test_critical_path.py
│   ├── test_delays.py
│   ├── test_dependencies.py
│   ├── test_editing.py
│   ├── test_excel_builder.py
│   ├── test_models.py
│   ├── test_project_io.py
│   └── test_validation.py
├── examples/
│   ├── small_demo.json               # 7 tasks, DAL only, 27 US holidays
│   └── npde_demo.json                # 17 tasks, 5 locations, 173 holidays
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
3. Run `pytest -q --ignore=tests/test_streamlit_playwright.py` from `C:\Users\Frosty\PMSuite` -- should show 95 backend tests passing.
4. **Two bugs to fix** (see "Known bugs" above):
   - **Right-click context menu broken:** Use `/diagnose` to determine why the context menu no longer appears on right-click. See the hypotheses in the Known Bugs section. The handler code is intact — the issue is likely event coordination or positioning within the iframe.
   - **Visual polish:** Use `/frontend-design` for the next visual iteration pass.
5. After fixing bugs, commit, update `EXECUTIVE_CHANGES_SUMMARY.md`, and push.

## Critical knowledge for next agent

- **Git identity for commits** -- use inline `-c user.name="Frosty-STI" -c user.email="s1lv3rstreak@gmail.com"` per commit; do NOT modify the global git config.
- **`gh` CLI** is not on PATH; plain `git push` works against the existing remote.
- **Streamlit launch:** `python -m streamlit run ui\streamlit_app.py` (streamlit.exe isn't on PATH).
- **PowerShell prints stderr as red even on success** -- pip install warnings and Python logging both go through stderr but don't indicate errors. Always check the actual content / exit code.
- **Tests run from PowerShell** with `python -m pytest -q "C:\Users\Frosty\PMSuite\tests" --rootdir "C:\Users\Frosty\PMSuite"`.
- **Pydantic v2 model serialization** uses `model_dump(mode="json", exclude_defaults=False, exclude_none=False)` for canonical output. Every save updates `project.updated_at` automatically.
- **Demo project files get rewritten** when run through save_project -- this is intentional (canonical formatting + updated_at). Don't revert.
- **MANDATORY: Update EXECUTIVE_CHANGES_SUMMARY.md with every push to GitHub.** Every commit that gets pushed must have a corresponding entry documenting what changed and why. Use the same format as existing entries.

### Step 8-specific knowledge

- **Component build:** `cd C:\Users\Frosty\PMSuite\components\gantt_chart\frontend && npx vite build` — outputs to `build/`.
- **Dev mode toggle:** Set `_RELEASE = False` in `components/gantt_chart/__init__.py` and run `npm start` for Vite dev server on port 3000.
- **`INTERACTIVE_SURFACE.md`** contains all 38 design decisions from the grilling session. It is the spec for Step 8.
- **Frappe Gantt v1.2.2** is the base library. The `@workiom/frappe-gantt` fork has a fatal `const` reassignment bug in its ES build and cannot be used. Drag-to-connect dependency creation is descoped; dependencies are managed via the sidebar panel.
- **CSS specificity matters.** Frappe uses `.gantt .bar-wrapper .bar` (0,3,0). Any bar color overrides must match this specificity. The current theme overrides Frappe CSS variables at `:root` AND uses matching-specificity selectors.
- **`classList.add()` monkey-patch** in `GanttComponent.jsx` is load-bearing — removing it will crash the Gantt for any task with multiple CSS classes (overdue+critical, planned+parent-task, etc.).

## Tone the user expects

- Crisp, decisive. They know what they want.
- One question at a time when ambiguity arises.
- Don't ask permission for things already authorized (push to GitHub, MIT license, per-feature commits).
- Don't pad. Respect their attention.
- Tell them which commit just landed and what to verify at checkpoints.
