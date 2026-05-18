# PMSuite — JSON-Driven Excel Gantt Chart Builder

A Python tool that generates Excel Gantt chart workbooks from a structured JSON project file. Designed for semiconductor New Product Development & Execution (NPDE) workflows that span multiple global sites with different work-weeks and holidays.

The JSON project file is the source of truth. The system loads the JSON, validates it, calculates the project schedule, applies dependency and delay logic, and generates a complete Excel workbook containing Gantt chart views, schedule calculations, and critical path notes.

## What it is

- **Source of truth:** structured JSON project files (`projects/*.json`).
- **Output artifact:** timestamped Excel workbooks (`output/gantt_<project_id>_<YYYY-MM-DD>_<HHMMSS>.xlsx`).
- **Editing surface:** local Streamlit UI calling the documented Python API. Manual Excel edits do not sync back to JSON.
- **Audience:** project managers, engineers, and program coordinators across globally distributed semiconductor sites.

## Installation

```bash
git clone https://github.com/Frosty-STI/PMSuite.git
cd PMSuite
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -e ".[dev]"
```

Requires Python 3.11 or newer.

## Quick start

Launch the Streamlit UI:

```bash
streamlit run ui/streamlit_app.py
```

On first run, the app creates a `projects/` directory. Use the sidebar to:

1. Load `examples/small_demo.json` to explore an existing project.
2. Click **New Project** in the sidebar to create your own.
3. Edit tasks in the table; click **Save** to persist; click **Build Excel** to generate a workbook in `output/`.

## How it works

```
JSON project file  →  Python loader/validator
                  →  Scheduling engine (calendar math, dependency cascade, delay propagation)
                  →  Excel builder (xlsxwriter)
                  →  Generated workbook with Day View, Week View, Schedule Calculations, Critical Path Notes
```

The scheduler resolves per-task calendar modes (working days vs e-days), per-task completion locations (DAL, MLA, CLARK, TAI, TIPI, TIEMA, FR-BIP, AIZU), holiday partitioning, parent/subtask rollups, parent-aware scheduling floors, and rich finish-to-start / start-to-start / finish-to-finish / start-to-finish dependencies with predecessor-calendar lag.

## Your data is local

**Your project JSON files live on YOUR machine and are NEVER pushed to GitHub.** The `projects/` directory is gitignored. Rotating local snapshots are kept in `projects/.backups/` for crash recovery (last 10 by default, configurable per project).

If you want versioned project history beyond local snapshots, back up `projects/` to your own cloud / network share / external drive.

The GitHub repository is for source code, documentation, and example projects only.

## Project file structure

See [DESIGN.md](DESIGN.md) for the complete JSON schema, validation rules, scheduling semantics, and location/holiday model.

## API reference

The Python API lives in `gantt_builder.api`. Documented function signatures in the module; structured `GanttError` exceptions with `.to_envelope()` for serialization. See [DESIGN.md](DESIGN.md) for the full API contract.

## Configuration

Per-project settings live inside each project's JSON file under the `settings` block. There is no global configuration. See [DESIGN.md](DESIGN.md) for the settings schema.

## Contributing

Contributions to source code, documentation, and example projects are welcome. User project files stay local — do not commit `projects/*.json`.

Workflow:

```bash
git clone https://github.com/Frosty-STI/PMSuite.git
pip install -e ".[dev]"
pytest -q
```

See [DESIGN.md](DESIGN.md) for the design decisions behind the current architecture.

## License

MIT.
