# EXCELBUILDER — Excel Workbook Output Spec

What the generated Excel workbook contains, how it's structured, and what the visual encoding means.

For the API entry point, see [API.md §build_excel](API.md#build_excelproject-output_dirnone---path). For the rendering decisions behind these choices, [MASTERECAP.md §Q15](MASTERECAP.md#q15--gantt-bar-rendering).

## File output

### Filename pattern

```
<output_dir>/gantt_<project_id>_<YYYY-MM-DD>_<HHMMSS>.xlsx
```

Example: `output/gantt_DEMO-NPDE_2026-05-13_142205.xlsx`

- Timestamp in project timezone (default `America/Chicago`).
- Lexically sortable — most recent at the bottom of an alphabetical sort.
- Collision-safe: `_2`, `_3`, ... suffix if multiple builds fire in the same second.

### No `_latest.xlsx` auto-copy

The system never maintains a `_latest` mirror. Users can identify the most recent file by sorting filename alphabetically descending. This eliminates the "which file is current?" ambiguity that comes with auto-mirroring.

### No automatic retention or cleanup in v1

Generated files accumulate in `output/`. Users prune manually.

## Library

**Production: `xlsxwriter`** (write-only).

**Tests: `openpyxl`** (reads generated files for structural assertions).

The regenerate-from-JSON model means we never need to modify an existing workbook, so `xlsxwriter`'s read-only limitation costs us nothing while we gain superior outline grouping, conditional formatting, and large-file write speed.

## Workbook structure — 4 sheets

| Sheet                    | Granularity  | Purpose                                    |
|--------------------------|--------------|--------------------------------------------|
| **Day View**             | 1 column / day | Detailed scrollable Gantt                |
| **Week View**            | 1 column / week | Compressed overview, same date span      |
| **Schedule Calculations** | tabular     | Auditable per-task computed values         |
| **Critical Path Notes**  | summary     | Risk dashboard for non-technical users     |

## Date axis (shared by Day View + Week View)

```
start_axis = floor_to_monday(min(earliest_task_start, today) - 7 days)
end_axis   = ceil_to_sunday (max(latest_effective_finish, today) + 14 days)
```

- **Today always included** in the axis, even on completed historical projects.
- **Monday week start** in v1 (ISO 8601, USA-anchored).
- **Override** via `settings.date_axis_start` and `settings.date_axis_end` in JSON.

Day View has one column per day across this span; Week View has one column per Monday-to-Sunday week across the same span. The user scrolls horizontally to navigate.

## Frozen panes

Both Day View and Week View freeze:
- The task metadata columns on the left (TASK ID, Name, Location).
- The date header row at the top.

`worksheet.freeze_panes(1, N)` where `N` = number of metadata columns (currently 3, may grow to include Calendar Mode and other quick-reference fields).

## Bar rendering (Option E — segmented static cell coloring)

Each task row has cells colored per its date range and status:

| Segment                                                          | Color (hex)    | When applied |
|------------------------------------------------------------------|----------------|--------------|
| **Planned** (incomplete, between computed_start and computed_finish) | `#4A90D9` (muted blue) | Default state for in-progress / upcoming work |
| **Completed** (full bar) — when `is_complete: true`               | `#2E8B57` (green) | After completion |
| **Delay extension** (computed_finish → effective_finish)          | `#E68A00` (orange) | When `delay_days > 0` |
| **Overdue** (today > effective_finish, incomplete)                | `#D9534F` (red) outline or fill | Live state |
| **Critical path indicator**                                      | `#8B0000` (dark red) border or left stripe | Tasks where `total_float == 0` |
| **Today column** (all rows)                                       | `#FFF8C4` (pale yellow) shade | Always |
| **Weekend column** (Day View only, all rows)                      | `#F0F0F0` (light gray) shade | Saturdays + Sundays |
| **Holiday column** (Day View only, per-row by location)           | `#E0E0E0` (darker gray) + name in header | Where task's location has a holiday on that date |
| **Parent summary bar**                                            | `#555555` (dark gray) with black border caps | Rolled-up parent rows |

**No text on bars.** Task ID + Name live in the frozen leftmost columns where they have room. Bars are pure color encoding.

### Multi-segment example

A task with `cycle_time_days: 5`, `delay_days: 2`, `is_complete: false`, overdue by 1 day:

```
Day:        D1  D2  D3  D4  D5  D6  D7  D8
Color:    blue blue blue blue blue oran oran red
                                   |         |
                                   delay     overdue marker
```

- Days 1–5: planned (blue) — covers `computed_start` through `computed_finish`.
- Days 6–7: delay extension (orange) — covers `computed_finish + 1` through `effective_finish`.
- Day 8 (= today): overdue marker (red) — today is past `effective_finish` and task is incomplete.

## Sheet 1 — Day View

### Columns

| Column index | Header     | Width | Notes |
|--------------|------------|-------|-------|
| 0            | TASK ID    | 12    | Monospace, frozen left |
| 1            | Name       | 28    | Frozen left |
| 2            | Location   | 10    | Frozen left |
| 3..N         | (dates)    | 4 each | One per day across the axis |

### Per-row rendering

For each task row, iterate the date columns and apply the segmented color rules above. Holiday and weekend shading apply per-row when the task's `completion_location` would otherwise be in working state on that date (or for e-day tasks, when the day is a holiday of the task's location).

## Sheet 2 — Week View

### Columns

| Column index | Header     | Width | Notes |
|--------------|------------|-------|-------|
| 0            | TASK ID    | 12    | Frozen left |
| 1            | Name       | 28    | Frozen left |
| 2            | Location   | 10    | Frozen left |
| 3..N         | (weeks)    | 10 each | One per Monday-of-week date |

Each week column represents Mon–Sun. A task overlapping any day in the week gets that week colored.

**No per-location work-week aggregation** — column headers are USA-anchored Monday dates regardless of which location's tasks are in the row. This was Option C from the Q19 grilling; it avoids per-location duplicate sheets.

## Sheet 3 — Schedule Calculations

The audit table. Every task is one row. Columns are in this exact order, left to right:

| #  | Column                  | Source                                | Notes |
|----|-------------------------|---------------------------------------|-------|
| 0  | TASK ID                 | `task.id`                             | Frozen left |
| 1  | Name                    | `task.name`                           | Frozen left |
| 2  | Hierarchy Level         | derived (count of parent_id hops)     | 0 = root |
| 3  | Parent ID               | `task.parent_id`                      | Empty for roots |
| 4  | Location                | `task.completion_location`            | |
| 5  | Calendar Mode           | `task.calendar_mode`                  | `working_days` or `e_days` |
| 6  | Cycle Time              | `task.cycle_time_days`                | Empty for parents |
| 7  | Manual Start Date       | `task.manual_start_date`              | ISO date or empty |
| 8  | Computed Start          | scheduler                             | Derived |
| 9  | Computed Finish         | scheduler                             | Derived |
| 10 | Delay Days              | `task.delay_days`                     | Cumulative |
| 11 | Effective Finish        | scheduler                             | Derived |
| 12 | Actual Completion Date  | `task.actual_completion_date`         | ISO date or empty |
| 13 | Is Complete             | `task.is_complete`                    | TRUE/FALSE |
| 14 | Dependencies            | derived string                        | Format: `TASK-001[FS, lag 0]; TASK-002[SS, lag 2]` |
| 15 | Total Float             | `critical_path.total_float[task.id]`  | Currently always 0 (stub) |
| 16 | Is Critical             | `task.id in critical_path.critical_task_ids` | TRUE/FALSE |
| 17 | Was On Critical Path    | `project.history[task_id].was_on_critical_path` | TRUE/FALSE, snapshot at completion |
| 18 | Downstream Impact       | count of tasks depending on this one | int |
| 19 | Validation Warnings     | derived string                        | Semicolon-separated warnings, empty if clean |

Header row frozen. Columns 0–1 (ID + Name) frozen left.

## Sheet 4 — Critical Path Notes

Risk and timing dashboard for non-technical users. Layout top to bottom:

1. **Auto-generated plain-language summary at the top.** Example: `"Project DEMO-NPDE ends 2026-08-15. 12 tasks on critical path. 3 overdue. 2 delayed."`
2. **Summary block** — Label/Value pairs:
   - Project (id + name)
   - Project end date (derived)
   - Total tasks
   - Critical path tasks count
   - Overdue incomplete tasks count
   - Tasks with delay > 0 count
3. **Critical path tasks table** (planned).
4. **Tasks currently delaying the project** (subset of critical with `delay_days > 0`).
5. **Top 5 near-critical** (lowest non-zero `total_float`).
6. **Overdue incomplete tasks** (all, regardless of critical path membership).
7. **Recently completed late** (last 30 days, derived from `delay_log`).
8. **Recently completed early** (last 30 days).
9. **Dependency warnings**.

**Walking-skeleton status:** items 1–2 implemented (summary + counts). Items 3–9 to be filled in as the backward-pass CPM, delay engine, and history tracking come online.

## E-day vs working-day rendering

- **E-day tasks** color every day in their range (no weekend skips). Holiday columns still gray-shade for the task's location.
- **Working-day tasks** color only the working days of their location between `computed_start` and `effective_finish`. Non-working days within the bar range render as the column's weekend/holiday gray, NOT the task's bar color.

This makes "this task runs continuously vs. only on business days" immediately visible.

## Per-task holiday shading

Holidays are per-location. A USA Thanksgiving holiday gray-shades the column only for tasks whose `completion_location == "USA"` — an MLA task running on USA Thanksgiving is fine. Implementation iterates the holiday list per row's location when rendering cells.

Column header for a holiday day labels the date AND the holiday name (e.g., `Thu\n2026-11-26\nThanksgiving (USA)`). When multiple locations share a holiday on the same date, the header lists all of them: `(USA, FR-BIP, AIZU)`.

## Performance budget

Cold-start budget at 50–300 tasks: **< 6 seconds total** (load → validate → schedule → build).

`xlsxwriter` writes 100k+ formatted cells in well under a second on a modern laptop. A typical 300-task project with a 1-year axis is ~110k cells in Day View; comfortable.

At 2000+ tasks (no hard cap), performance degrades gracefully — Day View writes scale linearly with task count × axis-day count.

## What's NOT yet implemented (walking skeleton)

The walking skeleton ships a valid 4-sheet workbook with:
- Task IDs, Names, Locations populated.
- Basic planned (blue) / completed (green) cell coloring in Day View.
- Week View overlap coloring.
- Schedule Calculations with derived columns.
- Critical Path Notes summary block.

Still to land in the full-rendering commit:
- Delay extension (orange) segments.
- Overdue (red) markers.
- Critical path (dark red) indicators.
- Today column highlight.
- Weekend column shading in Day View.
- Holiday column shading per row's location.
- Parent summary bars with caps.
- Holiday names in column headers.
- Per-row hover tooltips or comments showing delay reason / completion date.

When the full-rendering commit lands, this document and the corresponding test in `tests/test_excel_builder.py` should be updated together.
