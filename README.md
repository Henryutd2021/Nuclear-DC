# Nuclear-Powered Data Center Optimization

A modular Pyomo + Gurobi framework for co-optimizing electricity and chilled-water provision to a data center using nuclear heat. Plan v2.7 covers four operating cases on a single common accounting basis, with a 73-run baseline + 6-dimension sensitivity grid (PUE, ERCOT year, BESS, SMR CAPEX 1D, SMR×absorption CAPEX 2D, and carbon-price policy lever) for techno-economic boundary analysis. All eight KPIs from plan §0.5 D are now populated: TAC, LCOE, LCOC, Heat-Recovery Premium, annual CO₂, carbon abatement cost, EPBT, water footprint.

## Overview

The model minimizes Total Annualized Cost (TAC) while meeting data center IT load and cooling demand. Nuclear cogen (Case 2) routes main steam through the HP turbine first, then diverts a controlled mid-pressure extraction at 5–7 barg to a double-effect LiBr-H₂O absorption chiller for the DC cooling duty — a cascade, not a parallel main-steam tap, so high-grade steam is no longer wasted on a 6 °C cooling load.

- **Primary heat source:** BWRX-300 SMR (870 MWth / 300 MWe gross)
- **Steam network:** Main steam → HP turbine → mid-pressure extraction tap → LP turbine + condenser
- **Power generation:** HP+LP main steam turbine with Willans-line linearization on extraction
- **Cooling (Case 2):** Double-effect LiBr-H₂O absorption chiller driven by HP extraction; VCC backup during P1-A crystallization windows
- **Cooling (other cases):** Vapor-compression chiller only
- **Storage (S3 sensitivity):** 100 MWh / 25 MW Li-ion BESS, binary on/off
- **Reference fossil alternative (Case 3):** On-site NGCC, off-grid

### Four Operating Cases

0. **Case 0 — Grid-only baseline:** Data center buys all electricity from ERCOT and runs a VCC chiller; the TAC denominator for the Heat-Recovery Premium metric.
1. **Case 1 — Nuclear, no heat recovery:** BWRX-300 + main turbine → electricity for IT and VCC; no cogen. Quantifies the gap between "build the reactor" and "use its waste heat too".
2. **Case 2 — Nuclear + cascaded extraction + absorption (v2.7 head-line):** HP extraction at ~160 °C drives the absorption chiller. Willans line charges ~0.083 MWe/MWth diverted (Plan §A7 + §F.1).
3. **Case 3 — On-site NGCC:** Natural-gas combined cycle (net η = 0.55) covers IT and VCC off-grid; benchmark for fossil baseload (was Case 4 in v2.5).

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
# Drive the full v2.7 sensitivity grid (baseline + S1..S6, 73 solves total)
PYTHONPATH=. python scripts/run_all_analyses.py
```

The grid driver writes per-run `summary.json` + compressed dispatch CSVs to `outputs/<group>/<run_id>/`, plus a flat `outputs/master_kpi_table.csv` and `outputs/manifest.json`.

```python
# Programmatic single-case solve
from pathlib import Path
from src.config import load_config
from src.data import load_time_series
from src.cases.case2 import solve_case2

cfg = load_config(case_id=2, project_root=Path("."))
ts = load_time_series(project_root=Path("."), year=2023, num_hours=8760)
result = solve_case2(cfg, ts, pue=1.30)
print(f"TAC = ${result.tac_usd_per_yr / 1e6:.1f} M/yr")
```

### Configuration

All parameters are specified in YAML files in the `config/` directory:

- **`base.yaml`** - Global defaults (time horizon, solver settings, physical parameters)
- **`plant_case0.yaml`** - Grid-only baseline (no on-site reactor)
- **`plant_case1.yaml`** - Case 1 (nuclear, main turbine only, no heat recovery)
- **`plant_case2.yaml`** - Case 2 (nuclear + cascaded HP extraction + double-effect absorption, Willans slope locked at 0.083 MWe/MWth)
- **`plant_case3.yaml`** - Case 3 (NGCC on-site, off-grid)
- **`capex_grid_s5.yaml`** - 5×5 SMR × absorption CAPEX grid for the S5 2D feasibility scan
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
│   ├── plant_case1.yaml       # Case 1 (nuclear, no heat recovery)
│   ├── plant_case2.yaml       # Case 2 (nuclear + cascaded HP extraction + absorption)
│   ├── plant_case3.yaml       # Case 3 (NGCC on-site)
│   ├── capex_grid_s5.yaml     # S5 5×5 SMR × absorption CAPEX grid
│   └── costs.yaml             # Economic parameters
├── data/                      # Input time-series + raw fetchers
│   ├── it_load.csv            # IT electric load
│   ├── cooling_load.csv       # Cooling demand (optional)
│   ├── grid_price_import.csv  # Grid import prices (optional)
│   ├── grid_price_export.csv  # Grid export prices (optional)
│   ├── perf/                  # Performance curves (turbine, ORC, AB, EC)
│   └── _raw/                  # Public-source fetchers (ERCOT, EIA, weather, ATB)
├── src/                       # Source code
│   ├── config.py              # Pydantic configuration loader + S4 reactor / S5 CAPEX helpers
│   ├── data.py                # Time-series loader (ERCOT LMP + NSRDB wet bulb + IT load + AEF)
│   ├── kpi.py                 # Heat-Recovery Premium + LCOE/LCOC helpers
│   ├── cases/                 # Per-case solve entry points (case0..case3, v2.7)
│   │   ├── case0.py           # Grid-only baseline (closed-form LP)
│   │   ├── case1.py           # Nuclear, no recovery (Pyomo MILP via builder)
│   │   ├── case2.py           # Nuclear + cascaded extraction + absorption
│   │   └── case3.py           # NGCC on-site (closed-form LP)
│   └── milp/                  # Pyomo MILP builder for nuclear cases
│       ├── builder.py         # Reactor + turbine Willans + absorption COP(T_wb) + BESS
│       ├── solve.py           # Gurobi solver wrapper
│       └── result.py          # NuclearCaseResult dataclass + extractor
├── scripts/                   # Run drivers
│   └── run_all_analyses.py    # 73-run baseline + S1..S6 sensitivity grid (plan-v2.7)
├── tests/                     # Unit & integration tests (pytest, 85 fast + ~8 integration)
├── notebooks/                 # Figure pipeline (make_v27_figures.py — Fig 2-11 + Graphical Abstract)
├── AE_SMR_DC/                 # Applied Energy manuscript scaffold (cas-dc.cls)
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
  - Full 73-run sensitivity grid via `scripts/run_all_analyses.py`: ~2.5 min on 12-core workstation (Gurobi LP relaxation; see manifest.json for breakdown)

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
