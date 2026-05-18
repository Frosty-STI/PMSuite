# HANDOFF — PMSuite Gantt Builder

This document is the resume point for any fresh agent or developer picking up where we left off. Depth lives in the cross-referenced docs.

## Where we are right now (HEAD `309c66b` on `main`, with pre-Step-6 hardening in the working tree)

**The backend is feature-complete through Step 5. A pre-Step-6 review pass hardened parent-aware scheduling, project-timezone timestamps, validation edge cases, Excel holiday-gap rendering, docs, and license metadata.**

Latest commits (most recent first):

| Hash      | Step | Summary |
|-----------|------|---------|
| `309c66b` | 5.5  | Checkpoint 2 iteration: DAL rename, long-pole detection, demo parallel tasks, Excel polish |
| `c824203` | 5    | Full Option E Excel rendering + real holiday seeding for demos |
| `38a85a2` | 4.5  | Baseline fields + Cycle Time (Days) header rename |
| `1829fa5` | 4    | Parent completion cascade with preserve-earlier-children rule |
| `f40e9dd` | 3    | Delay propagation engine with auto-catchup and undo |
| `3a61f29` | 2    | Full SS / FF / SF dependency types with lag |
| `e3bde5e` | 1    | Backward-pass CPM with total float and critical-path detection |
| `b7c357d` | doc  | Initial comprehensive documentation (HANDOFF, MASTERECAP, etc.) |
| `10a294d` | 0    | Walking-skeleton scaffold |

**95/95 tests passing** (`pytest -q` ~0.7 sec). The end-to-end pipeline plus editing/delay/completion/baseline/dependency/critical-path/validation/Excel structural workflows are functional.

## What works today

- **Forward-pass scheduling** with full FS / SS / FF / SF dependency types and positive/negative lag.
- **Backward-pass CPM** computes `total_float` for every leaf and marks tasks with float == 0 as critical (completed tasks excluded).
- **Per-task calendar mode** (`working_days` vs `e_days`), per-location work-weeks, per-location holidays.
- **Manual-start as floor** combined with dependency-driven starts; unanchored leaves are validation errors.
- **Parent / multi-level hierarchy** with rollup; parents can have their own dependencies and manual starts, inherited by descendant leaves.
- **Dependencies on parent tasks** use the parent predecessor's rolled-up descendant schedule.
- **Cumulative `delay_days`** with audit `delay_log`. Manual and auto-catchup-on-load both flow through here.
- **Auto-catchup math:** Option B (per-task accurate, static). Fresh-project baseline initialization; idempotent within a day.
- **Completion semantics:** auto-fill date, freeze effective dates, parent cascade with preserve-earlier-children, undo within session.
- **Project baseline:** `set_project_baseline()` snapshots current dates into `baseline_start` / `baseline_finish` per task.
- **Atomic JSON I/O** with rotating snapshots.
- **Two-tier collect validation** (structural fails fast, logical collects).
- **Project-timezone timestamps** for saves, snapshots, `last_export`, and Excel filenames.
- **Excel workbook generation** with full Option E rendering:
  - 5 sheets: Chart Key & Info, Day View, Week View, Schedule Calculations, Critical Path Notes.
  - Frozen-pane metadata: TASK ID, Name, Location, Cycle Time (Days), Baseline Start, Baseline Finish.
  - Segmented bar colors (planned blue, completed green, delayed orange, overdue red).
  - Critical-path dark-red stripe via top/bottom border.
  - Today vertical line (thick black left border on every body cell in today's column).
  - Multi-line date column headers with weekday, date, and holiday name(s) per location.
  - Day View / Week View rows sort chronologically by scheduled dates, while TASK IDs remain stable creation identifiers.
  - Per-row weekend/holiday "gap" shading for working-day tasks.
  - E-day tasks render continuous through weekends and holidays.
  - Parent summary bars in dark gray with critical inheritance.
- **Streamlit UI shell** (read-only) — picks project, displays task table, runs Validate / Save / Build Excel.

## What's still stubbed (next session's work)

In priority order (matching the original 9-step plan with steps 1–5 now done):

6. **Streamlit editing surface** — task add/edit/delete in-place, dependency picker with "Dependency Explanation" expander, mark-complete checkbox wired to the cascade, dirty-state badge, browser `beforeunload` warning, New Project form, single-project switching dialog.
7. **Holiday editor page** — dedicated Streamlit route, tabbed by location, table of `{date, name, source}` with add/edit/delete, "Re-seed from library" with diff preview.
8. **Expand `examples/npde_demo.json`** — currently 13 tasks; target ~30–50 tasks modeling a generic NPDE program (kickoff → mask design → wafer fab → assembly → burn-in → qual → datasheet → CSR), using public-domain semiconductor flow knowledge only. Real holidays already seeded.
9. **Remaining test files / expansions** — broaden `test_validation.py`, add `test_scheduler.py` calendar math edge cases, `test_locations.py`, `test_holidays.py`, more `test_excel_builder.py` structural assertions, `test_excel_visual.py` (opt-in), `test_performance.py` (slow marker).

## Files modified during this session (beyond the original walking skeleton)

```
gantt_builder/
├── api.py             — re-exports all new public functions
├── baseline.py        — NEW. set_project_baseline + BaselineResult
├── completion.py      — NEW. mark_task_complete, unmark, undo
├── critical_path.py   — backward pass implemented; SS/FF/SF in CPM math
├── delays.py          — NEW. preview_auto_catchup, apply_*, undo, is_pending
├── errors.py          — added TaskNotFoundError, CompletedTaskCannotBeDelayedError
├── editing.py         — Step 6 API primitives: add/update/delete tasks and dependency edits
├── excel_builder.py   — full Option E rendering
├── models.py          — Task gained baseline_start, baseline_finish;
│                         Project gained all_descendant_ids / _leaf_ids helpers
├── scheduler.py       — dependency-floor dispatcher for FS/SS/FF/SF;
│                         _subtract_days_in_calendar helper
└── ...

tests/
├── test_baseline.py        — NEW. 5 tests
├── test_completion.py      — NEW. 15 tests
├── test_critical_path.py   — NEW. 8 tests
├── test_delays.py          — NEW. 19 tests
├── test_dependencies.py    — NEW. 12 tests
├── test_api.py             — original 2 tests
├── test_models.py          — original 4 tests
├── test_project_io.py      — original 5 tests
└── ...

examples/
├── small_demo.json    — baseline populated; 27 real DAL/US 2026–2027 holidays
└── npde_demo.json     — baseline populated; 173 real holidays across
                         DAL / MLA / TAI / FR-BIP / AIZU
```

95 tests total. All passing.

## Latest demo workbooks (locally; gitignored)

```
C:\Users\Frosty\PMsuite\output\gantt_DEMO-SMALL_2026-05-14_225130.xlsx
C:\Users\Frosty\PMsuite\output\gantt_DEMO-NPDE_2026-05-14_225130.xlsx
```

Both showcase the full Option E rendering. NPDE is the more interesting one (5 locations, mixed calendar modes, real holidays).

## The user's targeting

- **Demo audience:** external customers / cross-team handoff.
- **Path A (go-mode):** working through steps autonomously with checkpoint reviews at natural boundaries.
- **Public-web data only.** Never TI-internal information in the public repo.
- **Per-feature commits.** Each step lands as its own pushed commit.
- **License: MIT** (locked).
- **Real 2026–2027 holidays** already seeded into both demo projects.
- **Color palette: locked** per MASTERECAP Q26a.

We were at **Checkpoint 2** when the user asked for this handoff — backend complete + Excel polished, waiting for the user to verify the workbooks look right before charging into Step 6 (Streamlit UI).

## What a fresh agent should do on resume

1. Greet, confirm the user is ready to continue Path A.
2. Read `MASTERECAP.md` for the design contract and `HANDOFF.md` (this file) for current state.
3. Run `pytest -q` from `C:\Users\Frosty\PMsuite` — should show 82 passing.
4. Confirm the user's verdict on the latest demo workbooks (Checkpoint 2 visual review). If they say "go", start Step 6.

## Step 6 — Streamlit editing surface — concrete starting plan

The current `ui/streamlit_app.py` is read-only: dropdown + display + Validate / Save / Build Excel buttons. Step 6 expands it without changing the underlying API contract.

**Required additions:**

1. **`st.session_state` model for project + dirty flag:**
   ```python
   if "project" not in st.session_state:
       st.session_state.project = None
       st.session_state.project_path = None
       st.session_state.dirty = False
       st.session_state.last_auto_catchup_result = None
       st.session_state.last_completion_result = None
   ```
2. **Editable task table** using `st.data_editor`. Each column gets an appropriate editor (text input for name, dropdown for location/calendar_mode, number for cycle_time/delay_days, date picker for manual_start_date / actual_completion_date, checkbox for is_complete).
3. **Add Task button** that creates a new row via `next_task_id` and increments the counter.
4. **Delete Task button** that rejects deletion if any task depends on the target (surface affected IDs).
5. **Dependency editor** as a popover or expander per row. Multi-select of other task IDs, dropdown for type (FS/SS/FF/SF), number input for lag_days.
6. **"Dependency Explanation" expander** above the task table, containing plain-language descriptions of each type (text per STREAMLIT.md §planned features).
7. **Mark-complete checkbox** wired through `api.mark_task_complete()` so cascades fire automatically. When checked, auto-fills `actual_completion_date` to today. Surface a banner if children with earlier dates were preserved.
8. **Dirty-state badge** ("● Unsaved changes") near the project header that appears any time in-memory state diverges from on-disk.
9. **Browser `beforeunload` warning** via `st.components.v1.html` injecting `window.onbeforeunload`. Wire to `st.session_state.dirty`.
10. **Auto-catchup-on-load prompt**: when `api.is_auto_catchup_pending(project)` returns True, show a modal/expander with the `preview_auto_catchup` result. Buttons: **Apply** (calls `apply_auto_catchup`, shows banner with **Undo this batch**), **Skip for now**.
11. **New Project form** in the sidebar — `st.form` with name, ID slug (auto-suggested), timezone (default America/Chicago), default location, output directory. Writes a skeleton JSON to `projects/<slug>.json`.
12. **Project switcher confirmation dialog** when switching with `dirty=True`.

**Tests to add alongside** (or right after — UI is harder to test, structural is enough):

- `tests/test_api.py` extended: verify `add_task` / `update_task` / `delete_task` API stubs work (these don't exist yet — the Streamlit will need them in api.py).
- Smoke test that the Streamlit script imports cleanly and `main()` runs without errors when given a fresh `st.session_state`.

**Implementation order suggestion:**
1. ~~Add `add_task` / `update_task` / `delete_task` / `add_dependency` / `remove_dependency` to the API~~ — landed in Step 6 start.
2. Refactor Streamlit to use `st.session_state` for the project.
3. Replace `st.dataframe` with `st.data_editor`.
4. Wire add/delete buttons.
5. Wire the dependency editor.
6. Wire mark-complete.
7. Add the dirty badge and `beforeunload`.
8. Add auto-catchup-on-load prompt.
9. Add New Project form.

**Heads-up — Streamlit complexity:** `st.data_editor` is powerful but state management around it (especially undoing changes, syncing with `st.session_state`) is fiddly. Budget extra debugging time.

## Suggested skills for next session

- **No `grill-me` or `handoff` needed** mid-stream.
- Plain `Edit` / `Write` / `Bash` / `PowerShell` / `Read` / `Glob` / `Grep`.
- For Streamlit testing, may want to launch Streamlit via PowerShell with `run_in_background=True` and observe via curl or screenshots. Or use `streamlit run --headless --server.port 8502` and rely on Python imports for behavior tests.

## Local layout (unchanged from initial scaffold)

```
C:\Users\Frosty\PMsuite\          # local clone; pushed to https://github.com/Frosty-STI/PMSuite
├── HANDOFF.md                    # this file
├── MASTERECAP.md                 # all decisions including Q27/Q28 addenda
├── DESIGN.md                     # architecture-level design rationale
├── API.md                        # Python API contract (with mark_complete, baseline, delays funcs)
├── JSONFILE.md                   # JSON schema (with baseline_start/finish)
├── EXCELBUILDER.md               # Excel spec (Option E implemented)
├── STREAMLIT.md                  # UI spec (Step 6 work pending)
├── README.md
├── pyproject.toml
├── .gitignore
├── gantt_builder/
│   ├── api.py
│   ├── baseline.py
│   ├── completion.py
│   ├── critical_path.py
│   ├── delays.py
│   ├── errors.py
│   ├── excel_builder.py
│   ├── locations.py
│   ├── logging_config.py
│   ├── models.py
│   ├── project_io.py
│   ├── scheduler.py
│   └── validation.py
├── ui/streamlit_app.py
├── tests/                        # 12 test files, 95 tests passing
├── examples/                     # both demos have real holidays + baseline
├── output/                       # gitignored generated Excel files
└── .logs/gantt_builder.log
```

User auto-memory at `C:\Users\Frosty\.claude\projects\C--Users-Frosty\memory\`:
- `user_domain_semiconductor_npde.md` — NPDE domain context (e-day vs working-day, global sites).
- `MEMORY.md` — index.

## Critical knowledge for next agent

- **Git identity for commits** — use inline `-c user.name="Frosty-STI" -c user.email="s1lv3rstreak@gmail.com"` per commit; do NOT modify the global git config (per safety guidelines).
- **`gh` CLI** is not on PATH; plain `git push` works against the existing remote.
- **`streamlit.exe`** at `C:\Users\Frosty\AppData\Roaming\Python\Python312\Scripts\` isn't on PATH; use `python -m streamlit run ui\streamlit_app.py`.
- **PowerShell prints stderr as red even on success** — pip install warnings and Python logging both go through stderr but don't indicate errors. Always check the actual content / exit code.
- **Tests run from PowerShell** with `python -m pytest -q "C:\Users\Frosty\PMsuite\tests" --rootdir "C:\Users\Frosty\PMsuite"`.
- **`-m "not slow"` flag** skips the (not-yet-written) performance tests; safe to always use.
- **Pydantic v2 model serialization** uses `model_dump(mode="json", exclude_defaults=False, exclude_none=False)` for canonical output. Every save updates `project.updated_at` automatically.
- **Demo project files get rewritten** when run through save_project — this is intentional (canonical formatting + updated_at), but means the linter / system may flag them as "modified outside the conversation." Don't revert.
- **Color palette is locked** at MASTERECAP Q26a values. Don't redecorate without an explicit user ask.

## Tone the user expects

- Crisp, decisive. They've been answering "your suggestion" or specific overrides — they know what they want.
- One question at a time when ambiguity arises.
- Don't ask permission for things already authorized (push to GitHub, MIT license, per-feature commits).
- Don't pad. The user has been engaged for many hours; respect their attention.
- Tell them which commit just landed and what to verify at checkpoints. End each step with "go?" or a clear question.
