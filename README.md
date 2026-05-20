# Nuclear-Powered Data Center Optimization

A modular Pyomo + Gurobi framework for co-optimizing electricity and chilled-water provision to a data center using nuclear heat, with five operating cases and support for both dispatch-only and capacity co-design optimization.

## Overview

This repository implements an optimization model that minimizes total system cost while meeting data center IT electric load and cooling demands using:

- **Primary heat source:** Nuclear reactor & steam loop with intermediate heat exchanger (IHX)
- **Steam network:** High-pressure and low-pressure headers with flash vessel
- **Power generation:** Steam turbine + optional Organic Rankine Cycle (ORC)
- **Cooling:** Electric-driven chiller + double-effect absorption chiller (heat-driven)
- **Storage:** Stratified chilled-water thermal energy storage (TES)
- **Balance of plant:** Condensers, feedwater network, pumps, heat exchangers, auxiliaries

### Five Operating Cases

0. **Case 0 - Grid-only baseline:** Data center buys all electricity and cooling-driving power from the grid; no on-site reactor. Used as the TAC denominator for the *Premium of Co-generation* metric.
1. **Case 1 - Turbine-only co-located reactor:** All reactor heat → turbine → electricity; cooling via electric chiller only.
2. **Case 2 - Integrated ORC + absorption:** Split heat to turbine + ORC; absorption chiller uses diverted reactor heat.
3. **Case 3 - Turbine + absorption (no ORC):** Turbine generates power; turbine exhaust steam drives absorption chiller.
4. **Case 4 - On-site NGCC alternative:** Natural-gas combined-cycle plant supplies the data center in place of the reactor; benchmark for fossil-baseload comparison.

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Henryutd2021/Nuclear-DC.git
cd Nuclear-DC

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Note:** Requires Gurobi license (academic/commercial). Set `GRB_LICENSE_FILE` environment variable if needed.

### Basic Usage

```bash
# Single-case solves (24-hour smoke test)
python -m src.solve --case 0 --num-hours 24   # grid-only baseline
python -m src.solve --case 1 --num-hours 24   # turbine only
python -m src.solve --case 2 --num-hours 24   # ORC + absorption
python -m src.solve --case 3 --num-hours 24   # turbine + absorption
python -m src.solve --case 4 --num-hours 24   # NGCC alternative

# Full 8760-hour annual run with capacity co-design
python -m src.solve --case 2 --capacity-opt --num-hours 8760

# Drive the full sensitivity grid (baseline + S1..S5, 51 solves)
python scripts/run_all_analyses.py
```

The grid driver writes per-run `summary.json` + compressed dispatch CSVs to `outputs/<group>/<run_id>/`, plus a flat `outputs/master_kpi_table.csv` and `outputs/manifest.json`.

### Configuration

All parameters are specified in YAML files in the `config/` directory:

- **`base.yaml`** - Global defaults (time horizon, solver settings, physical parameters)
- **`plant_case0.yaml`** - Grid-only baseline (no on-site reactor)
- **`plant_case1.yaml`** - Equipment configuration for Case 1 (turbine only)
- **`plant_case2.yaml`** - Equipment configuration for Case 2 (ORC + absorption)
- **`plant_case3.yaml`** - Equipment configuration for Case 3 (turbine + absorption)
- **`plant_case4.yaml`** - Equipment configuration for Case 4 (NGCC alternative)
- **`costs.yaml`** - CAPEX, fixed & variable O&M, fuel costs, penalties

### Input Data

Time-series data in CSV format in the `data/` directory:

- **`it_load.csv`** - IT electric demand [MW] (required)
- **`cooling_load.csv`** - Cooling demand [MWth] (optional; derived from PUE if absent)
- **`grid_price_import.csv`** - Electricity import price [$/MWh] (optional)
- **`grid_price_export.csv`** - Electricity export price [$/MWh] (optional)

Performance curves in `data/perf/`:

- **`turbine_hr.csv`** - Turbine heat rate vs. power output
- **`orc_eta.csv`** - ORC efficiency vs. heat input
- **`ab_cop.csv`** - Absorption chiller COP vs. generator temperature
- **`ec_cop.csv`** - Electric chiller COP vs. ambient conditions

## Repository Structure

```text
Nuclear-DC/
├── README.md                  # This file
├── LICENSE / LICENSES.md      # License information
├── Makefile                   # Data-pipeline + test/lint shortcuts
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Project metadata & tool configs
├── config/                    # YAML configuration
│   ├── base.yaml              # Global settings
│   ├── plant_case0.yaml       # Case 0 (grid-only baseline)
│   ├── plant_case1.yaml       # Case 1 (turbine only)
│   ├── plant_case2.yaml       # Case 2 (ORC + absorption)
│   ├── plant_case3.yaml       # Case 3 (turbine + absorption)
│   ├── plant_case4.yaml       # Case 4 (NGCC alternative)
│   └── costs.yaml             # Economic parameters
├── data/                      # Input time-series + raw fetchers
│   ├── it_load.csv            # IT electric load
│   ├── cooling_load.csv       # Cooling demand (optional)
│   ├── grid_price_import.csv  # Grid import prices (optional)
│   ├── grid_price_export.csv  # Grid export prices (optional)
│   ├── perf/                  # Performance curves (turbine, ORC, AB, EC)
│   └── _raw/                  # Public-source fetchers (ERCOT, EIA, weather, ATB)
├── src/                       # Source code
│   ├── io_config.py           # Configuration loading & validation (Pydantic)
│   ├── io_data.py             # Data loading & preprocessing
│   ├── sets_params.py         # Pyomo sets & parameters
│   ├── model_core.py          # Model structure & variable declarations
│   ├── pwl_helper.py          # Piecewise-linear constraint utilities (SOS2)
│   ├── objective.py           # Total annualized cost objective
│   ├── solve.py               # CLI & solver interface
│   ├── cases/                 # Per-case build entry points (case0..case4)
│   ├── constraints/           # Modular constraint modules
│   │   ├── demand.py          # IT & cooling demand balances
│   │   ├── steam_network.py   # IHX, HP/LP headers, flash vessel
│   │   ├── routing.py         # Heat routing & case logic
│   │   ├── turbine.py         # Turbine performance & ramping
│   │   ├── orc.py             # ORC with recuperator & pump
│   │   ├── absorption.py      # Absorption chiller (generator T/P)
│   │   ├── electric_chiller.py # Electric chiller
│   │   ├── storage.py         # TES dynamics & losses
│   │   ├── condenser_fw.py    # Condenser & feedwater network
│   │   ├── auxiliaries.py     # Parasitic loads (pumps, etc.)
│   │   └── capacity.py        # Equipment sizing constraints
│   └── results/               # Output processing
│       ├── writers.py         # CSV/JSON export
│       └── postprocess.py     # KPI calculation & reporting
├── scripts/                   # Run drivers
│   └── run_all_analyses.py    # 51-run baseline + S1..S5 sensitivity grid
├── tests/                     # Unit & integration tests
├── notebooks/                 # Jupyter analysis notebooks
│   ├── make_paper_figures.ipynb  # Figure suite driver
│   ├── figure_helpers.py
│   └── build_notebook.py
├── figures/                   # Compiled paper figures
│   └── fig1_schematic/        # LaTeX/TikZ schematic of the heat-and-power network
├── docs/                      # Plan, model diagram, gap analysis, changelog
└── outputs/                   # Solver outputs (git-ignored)
    ├── <group>/<run_id>/summary.json
    ├── <group>/<run_id>/dispatch.csv.gz
    ├── master_kpi_table.csv
    └── manifest.json
```

## Key Features

### Architecture

- **Modular constraint architecture** - Each subsystem in separate file for maintainability
- **Pydantic validation** - Rigorous input validation with type checking
- **SOS2 piecewise-linear** - Accurate turbine/chiller efficiency curves
- **Flexible configuration** - YAML-based configs separate from code

### Optimization Capabilities

- **Two optimization modes:**
  - **Dispatch-only** - Fixed capacities, optimize hourly operation
  - **Capacity co-design** - Optimize both equipment sizes and operation
- **Equipment ramping constraints** - Realistic turbine ramp rates
- **Multiple cases** - Compare different system architectures
- **Time flexibility** - Analyze horizons from hours to weeks

### Physics Modeling

- **Detailed steam network** - IHX, pressure headers, flash vessel, mass/energy balances
- **Realistic performance curves** - Heat rate degradation, part-load efficiency
- **Thermal storage dynamics** - Charge/discharge efficiency, thermal losses
- **Auxiliary loads** - Pumps, cooling towers, parasitic consumption

### Outputs & Analysis

- **Comprehensive results** - Hourly dispatch, cost breakdowns, KPIs
- **Multiple formats** - CSV (time-series), JSON (summaries), log files
- **Rich console output** - Real-time solve progress, formatted results
- **Visualization-ready** - Structured data for plotting and analysis

## Model Formulation

### Decision Variables

**Time-indexed (hourly) flows:**

- **Electrical:** Turbine/ORC power output, grid imports/exports, chiller consumption, auxiliary loads
- **Thermal (steam):** Primary/secondary circuit flows, HP/LP header flows, flash vessel flows
- **Thermal (heat):** Reactor output, heat to turbine/ORC/absorption, condenser heat rejection
- **Cooling:** Chilled-water from electric/absorption chillers, TES charge/discharge, TES state-of-charge

**Capacity variables (co-design mode only):**

- Equipment sizes: Turbine, ORC, chillers, TES tank capacity

### Objective Function

Minimize **Total Annualized Cost (TAC)** including:

1. **Capital costs (annualized):**
   - Turbine, ORC, absorption chiller, electric chiller, TES
   - Annualized using capital recovery factor (CRF)

2. **Fixed O&M:**
   - Annual fixed maintenance per unit capacity

3. **Variable O&M & fuel:**
   - Per-MWh generation/production costs
   - Reactor fuel cost (per MWh thermal)

4. **Grid electricity:**
   - Import/export costs (time-varying prices supported)

5. **Penalties (soft constraints):**
   - Unmet IT load penalty
   - Unmet cooling demand penalty

### Constraints

**Energy balances:**

- IT electric power balance (generation = demand + auxiliary loads)
- Cooling demand balance (chillers + TES = data center cooling)

**Steam network:**

- IHX heat transfer (primary to secondary)
- HP/LP header mass and energy balances
- Flash vessel performance
- Feedwater and condenser network

**Heat routing:**

- Reactor heat allocation to turbine/ORC/absorption
- Case-specific equipment availability logic

**Equipment performance (piecewise-linear):**

- Turbine heat rate curve (heat input vs. power output)
- ORC efficiency with recuperator and pump losses
- Absorption chiller COP with generator temperature/pressure
- Electric chiller COP

**Thermal storage:**

- Energy dynamics (charge - discharge - losses = Δ SOC)
- Thermal loss rate (hourly percentage)
- Charge/discharge efficiency
- Capacity limits

**Operating constraints:**

- Minimum load fractions
- Ramping limits (turbine)
- Capacity bounds (equipment-specific)

**Case logic:**

- Equipment availability flags enforce case-specific configurations
- Disabled equipment capacities forced to zero

## Outputs

For a single-case solve, the model writes hourly dispatch (CSV) and a scalar KPI summary (JSON) under `outputs/`, together with the Gurobi log. The sensitivity-grid driver (`scripts/run_all_analyses.py`) additionally produces a flat `outputs/master_kpi_table.csv` covering every (case × year × PUE × reactor-CAPEX × BESS × equipment-CAPEX) cell, and a `manifest.json` recording the run grid plus per-run wall time.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_io.py -v

# Run tests matching pattern
pytest tests/ -k "steam" -v
```

### Code Quality

```bash
# Format code with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/

# Type checking with mypy
mypy src/

# Run all quality checks
black src/ tests/ && ruff check . && mypy src/
```

### Adding New Constraints

1. Create new file in `src/constraints/`
2. Implement function: `def add_XXX_constraints(model: pyo.ConcreteModel) -> None:`
3. Import and call in `src/solve.py` → `build_full_model()`
4. Add tests in `tests/test_constraints.py`

## System Requirements

### Software

- **Python:** 3.9 or higher (3.10+ recommended)
- **Gurobi:** 11.0+ (requires valid license)
  - Academic license: Free for qualifying users
  - Commercial license: Required for production use
- **Operating System:** Linux, macOS, or Windows

### Hardware

- **RAM:** 4GB minimum; 8GB+ recommended for week-long (168-hour) horizons
- **CPU:** Multi-core recommended (Gurobi will use available threads)
- **Disk:** ~100MB for framework + outputs

### Performance

- **Typical solve times (Gurobi 11, 12-core workstation):**
  - 24-hour smoke test: a few seconds
  - 168-hour horizon: 10–60 seconds
  - 8760-hour annual run: 1–10 minutes per case (depends on case and whether capacity co-design is enabled)
  - Full 51-run sensitivity grid via `scripts/run_all_analyses.py`: roughly 1–2 hours end-to-end

## Troubleshooting

### Gurobi license issues

```bash
# Set license file path
export GRB_LICENSE_FILE=/path/to/gurobi.lic

# Test Gurobi installation
python -c "import gurobipy; print(gurobipy.gurobi.version())"
```

### Infeasible model

- Check equipment capacity bounds in case config files
- Verify time-series data has no missing values
- Review solver log in `outputs/solve_caseX.log`
- Enable verbose output: Edit `base.yaml` → `solver.log_to_console: true`

## License

MIT License

## Citation

```bibtex
@software{nuclear_dc_optimization,
  title  = {Nuclear-Powered Data Center Optimization Framework},
  author = {Honglin Li},
  year   = {2026},
  url    = {https://github.com/Henryutd2021/Nuclear-DC}
}
```

## Contact

For questions, issues, or collaboration opportunities:

- **Issues:** Use GitHub issue tracker
- **Email:** <honglin.li@utdallas.edu>

---

**Last Updated:** May 2026
