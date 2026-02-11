# RotorDyn Calculator

Rotor dynamics lateral vibration calculator using the **Myklestad-Prohl transfer matrix method**.

Features a modern browser-based GUI with interactive Plotly charts and editable data tables. Can be packaged as a standalone Windows `.exe` via PyInstaller.

![screenshot](docs/screenshot.png)

## Features

- **File Import**: Upload `.rin` input files (drag & drop or file picker)
- **Parameter Editing**: Inline editing of shaft sections, bearings, and calculation options via AG Grid tables
- **Critical Speed Analysis**: Computes critical speeds, mode shapes, generalized/effective mass
- **Interactive Charts**: Plotly mode shape plots with bearing position markers, hover data, multi-mode overlay
- **Data Export**: Excel (.xlsx), CSV, and legacy `.rout` format export
- **Dark Mode**: Toggle between dark and light themes

## Quick Start

### Prerequisites

- Python 3.11+

### Install & Run

```bash
git clone https://github.com/Jusfan99/rotordyn.git
cd rotordyn
pip install -e .
python main.py
```

The app will start a local server and open your default browser automatically.

### Run from CLI (no GUI)

```bash
python -m rotordyn input.rin
```

## Project Structure

```
rotordyn/
├── rotordyn/
│   ├── config.py        # Constants (Young's modulus, gravity)
│   ├── models.py        # Data models (ShaftSection, Bearing, Rotor, etc.)
│   ├── parser.py        # .rin file parser
│   ├── engine.py        # Myklestad-Prohl solver
│   ├── formatter.py     # Legacy text output formatter
│   ├── ascii_plot.py    # ASCII mode shape plots (CLI)
│   └── gui/
│       ├── app.py       # NiceGUI main application
│       ├── components.py # Plotly figures, grid data helpers
│       └── export.py    # Excel/CSV/rout export
├── tests/               # pytest test suite (26 tests)
├── main.py              # GUI entry point
└── pyproject.toml
```

## Building Windows EXE

The GitHub Actions workflow builds a standalone Windows executable automatically on version tags:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Or trigger manually from the **Actions** tab on GitHub.

The build uses PyInstaller with `--onedir --windowed` and bundles all NiceGUI/Plotly assets.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| GUI Framework | [NiceGUI](https://nicegui.io) (FastAPI + Vue.js + Quasar) |
| Charts | [Plotly](https://plotly.com/python/) |
| Tables | [AG Grid](https://www.ag-grid.com/) (via NiceGUI) |
| Solver | NumPy + SciPy |
| Packaging | PyInstaller |
| CI/CD | GitHub Actions |

## Testing

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
