# Nuclear-Powered Data Center Optimization

A modular Pyomo + Gurobi framework for co-optimizing electricity and chilled-water provision to a data center using nuclear heat, with three operating cases and support for both dispatch-only and capacity co-design optimization.

## Overview

This repository implements an optimization model that minimizes total system cost while meeting data center IT electric load and cooling demands using:

- **Primary heat source:** Nuclear reactor & steam loop with intermediate heat exchanger (IHX)
- **Steam network:** High-pressure and low-pressure headers with flash vessel
- **Power generation:** Steam turbine + optional Organic Rankine Cycle (ORC)
- **Cooling:** Electric-driven chiller + double-effect absorption chiller (heat-driven)
- **Storage:** Stratified chilled-water thermal energy storage (TES)
- **Balance of plant:** Condensers, feedwater network, pumps, heat exchangers, auxiliaries

### Three Operating Cases

1. **Case 1 - Baseline (Turbine Only):** All reactor heat → turbine → electricity; cooling via electric chiller only
2. **Case 2 - Integrated ORC + Absorption:** Split heat to turbine + ORC; absorption chiller uses diverted heat
3. **Case 3 - Turbine + Absorption (No ORC):** Turbine generates power; turbine exhaust drives absorption chiller

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
# Run Case 1 (baseline) with 24-hour horizon
python -m src.solve --case 1 --num-hours 24

# Run Case 2 (ORC + absorption) with full week
python -m src.solve --case 2 --num-hours 168

# Run Case 3 (turbine + absorption)
python -m src.solve --case 3 --num-hours 24

# Enable capacity optimization mode
python -m src.solve --case 2 --capacity-opt --num-hours 168
```

### Configuration

All parameters are specified in YAML files in the `config/` directory:

- **`base.yaml`** - Global defaults (time horizon, solver settings, physical parameters)
- **`plant_case1.yaml`** - Equipment configuration for Case 1 (baseline)
- **`plant_case2.yaml`** - Equipment configuration for Case 2 (ORC + absorption)
- **`plant_case3.yaml`** - Equipment configuration for Case 3 (turbine + absorption)
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

```
Nuclear-DC/
├── README.md                  # This file
├── LICENSE                    # License information
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Project metadata & tool configs
├── config/                   # Configuration files
│   ├── base.yaml             # Global settings
│   ├── plant_case1.yaml      # Case 1 configuration
│   ├── plant_case2.yaml      # Case 2 configuration
│   ├── plant_case3.yaml      # Case 3 configuration
│   └── costs.yaml            # Economic parameters
├── data/                     # Input time-series data
│   ├── it_load.csv           # IT electric load
│   ├── cooling_load.csv      # Cooling demand (optional)
│   ├── grid_price_import.csv # Grid import prices (optional)
│   ├── grid_price_export.csv # Grid export prices (optional)
│   └── perf/                 # Performance curves
│       ├── turbine_hr.csv    # Turbine heat rate
│       ├── orc_eta.csv       # ORC efficiency
│       ├── ab_cop.csv        # Absorption COP
│       └── ec_cop.csv        # Electric chiller COP
├── src/                      # Source code
│   ├── io_config.py          # Configuration loading & validation (Pydantic)
│   ├── io_data.py            # Data loading & preprocessing
│   ├── sets_params.py        # Pyomo sets & parameters
│   ├── model_core.py         # Model structure & variable declarations
│   ├── pwl_helper.py         # Piecewise-linear constraint utilities (SOS2)
│   ├── objective.py          # Total annualized cost objective
│   ├── solve.py              # CLI & solver interface
│   ├── constraints/          # Modular constraint modules
│   │   ├── __init__.py
│   │   ├── demand.py         # IT & cooling demand balances
│   │   ├── steam_network.py  # IHX, HP/LP headers, flash vessel
│   │   ├── routing.py        # Heat routing & case logic
│   │   ├── turbine.py        # Turbine performance & ramping
│   │   ├── orc.py            # ORC with recuperator & pump
│   │   ├── absorption.py     # Absorption chiller (generator T/P)
│   │   ├── electric_chiller.py # Electric chiller
│   │   ├── storage.py        # TES dynamics & losses
│   │   ├── condenser_fw.py   # Condenser & feedwater network
│   │   ├── auxiliaries.py    # Parasitic loads (pumps, etc.)
│   │   └── capacity.py       # Equipment sizing constraints
│   └── results/              # Output processing
│       ├── writers.py        # CSV/JSON export
│       └── postprocess.py    # KPI calculation & reporting
├── tests/                    # Unit & integration tests
│   ├── test_io.py            # Config & data loading tests
│   ├── test_pwl.py           # Piecewise-linear helper tests
│   ├── test_constraints.py   # Constraint module tests
│   ├── test_storage.py       # TES dynamics tests
│   └── test_end_to_end.py    # Full model solve tests
├── notebooks/                # Jupyter analysis notebooks
│   └── demo_case_compare.ipynb
└── outputs/                  # Solver outputs (git-ignored)
    ├── dispatch_caseX.csv    # Hourly dispatch results
    ├── cost_summary_caseX.json # Cost breakdown
    └── solve_caseX.log       # Solver log
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

## Example Outputs

After solving, the framework generates:

### 1. Dispatch Results (`outputs/dispatch_caseX.csv`)

Hourly time-series data:

```csv
hour,P_tur_g_MW,P_ORC_g_MW,P_elc_MW,Q_rx_MWth,Q_chw_AB_MWth,Q_chw_EC_MWth,E_tank_MWh,...
0,34.2,5.8,12.4,98.5,8.2,15.3,25.0,...
1,34.5,5.9,12.1,99.1,8.5,14.9,24.2,...
...
```

### 2. Cost Summary (`outputs/cost_summary_caseX.json`)

```json
{
  "total_annualized_cost": 8496316.74,
  "capex_annualized": 3245123.45,
  "fixed_om": 1234567.89,
  "variable_om_fuel": 3456789.12,
  "grid_costs": 123456.78,
  "penalties": 0.0,
  ...
}
```

### 3. Console Output

```
============================================================
Solve Results
============================================================
Status: optimal
Solve time: 0.10 seconds
Optimal solution found!
Objective value (TAC): $8,496,316.74/year
✅ All IT load met
✅ All cooling demand met

============================================================
KEY PERFORMANCE INDICATORS
============================================================
Total Annualized Cost:     $8,496,317/year
LCOE (Levelized Cost):     $10,085.25/MWh
LCOC (Cooling Cost):       $40,311.48/MWh_th

Capacity Factors:
  Turbine:                 98.3%
  ORC:                     8.9%

Cooling Mix:
  Absorption fraction:     0.0%
  Electric chiller:        100.0%

TES Utilization:           50.0%
  Max SOC:                 25.0 MWh
  Avg SOC:                 24.8 MWh
```

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

### Adding New Cases

1. Create `config/plant_caseX.yaml` with equipment flags
2. Update case descriptions in documentation
3. Test with: `python -m src.solve --case X --num-hours 24`

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

- **Typical solve times:**
  - 24-hour horizon: < 30 seconds
  - 168-hour horizon: 1-5 minutes
  - Depends on case complexity and solver settings

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

## Future Enhancements

- [ ] Unit commitment with binary variables (startup/shutdown costs)
- [ ] Multi-stage stochastic optimization (demand uncertainty)
- [ ] Additional cooling technologies (mechanical chillers, free cooling)
- [ ] Grid services (frequency regulation, reserves)
- [ ] Renewable integration (solar PV, wind)
- [ ] Advanced visualization dashboard
- [ ] Sensitivity analysis automation
- [ ] Multi-objective optimization (cost vs. emissions)

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Make changes with tests
4. Ensure all tests pass (`pytest`)
5. Format code (`black src/ tests/`)
6. Submit pull request

## License

MIT License

## Citation


```bibtex
@software{nuclear_dc_optimization,
  title = {Nuclear-Powered Data Center Optimization Framework},
  author = {Honglin Li},
  year = {2025},
  url = {https://github.com/Henryutd2021/Nuclear-DC}
}
```

## Contact

For questions, issues, or collaboration opportunities:

- **Issues:** Use GitHub issue tracker
- **Email:** honglin.li@utdallas.edu

---

**Last Updated:** October 2025
