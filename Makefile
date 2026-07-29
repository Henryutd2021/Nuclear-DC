.PHONY: help data data-tier2 data-tier3 data-clean test lint format check manuscript-applied-energy

PYTHON := python3

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

manuscript-applied-energy:  ## Compile the Applied Energy manuscript with BibTeX
	cd "MANUSCRIPT/Applied Energy" && latexmk main.tex

# =============================================================================
# Data lifecycle (see data/README.md "How to get the data")
# =============================================================================

data: data-tier2  ## Default: regenerate Tier 2 (public re-fetches + derivations, ~10 min)

data-tier2:  ## Re-fetch Tier 2 data from public sources (ERCOT, EIA, Open-Meteo, Henry Hub)
	@echo "[Tier 2] Fetching ERCOT DAM SPP 2022-2024 (~30 s)..."
	$(PYTHON) data/_raw/fetch_ercot_dam.py
	@echo "[Tier 2] Fetching ERCOT RTM SPP 2022-2024 (~3 min)..."
	$(PYTHON) data/_raw/fetch_ercot_rtm.py
	@echo "[Tier 2] Fetching EIA-930 ERCO 2022-2024 (~5 min first run; cached after)..."
	$(PYTHON) data/_raw/fetch_eia930_erco.py
	@echo "[Tier 2] Fetching EIA Henry Hub daily 2022-2024 (~10 s)..."
	$(PYTHON) data/_raw/fetch_henry_hub.py
	@echo "[Tier 2] Fetching Open-Meteo Houston weather 2022-2024 (~5 s)..."
	$(PYTHON) data/_raw/fetch_open_meteo_houston.py
	@echo "[Tier 2] Building real hourly carbon intensity..."
	$(PYTHON) data/_raw/build_real_carbon_intensity.py
	@echo "[Tier 2] Rebuilding performance curves..."
	$(PYTHON) data/_raw/build_performance_curves.py
	@echo "[Tier 2] Rebuilding ambient + price_grid bridge (default 2024)..."
	$(PYTHON) data/_raw/build_ambient_and_price_bridge.py --year 2024
	@if [ -d data/workload/raw_nlr_colocation ] && [ -f data/workload/raw_nlr_colocation/colocation_10MW_2840nodes_60u_power.csv ]; then \
		echo "[Tier 2] NLR raw data present — building AI workload aggregates..."; \
		$(PYTHON) data/_raw/build_real_ai_workload.py; \
	else \
		echo "[Tier 2] NLR raw data NOT present — see data/MANUAL_COLLECTION.md to obtain"; \
		echo "[Tier 2] Skipping workload aggregation"; \
	fi
	@echo "[Tier 2] Done."

data-tier3:  ## Print manual instructions for Tier 3 (NLR 1 GB AI workload dataset)
	@echo "=========================================================================="
	@echo "Tier 3 — Manual download required (1 GB, third-party data)"
	@echo "=========================================================================="
	@echo ""
	@echo "Source: Vercellino et al. 2026 'Measurement of Generative AI Workload"
	@echo "         Power Profiles for Whole-Facility Data Center Infrastructure"
	@echo "         Planning'. arXiv:2604.07345  |  DOI 10.7799/3025227"
	@echo ""
	@echo "Steps:"
	@echo "  1. Visit https://data.nlr.gov/submissions/312"
	@echo "  2. Download dataset.zip (~1 GB)"
	@echo "  3. Unzip and copy CSVs to data/workload/raw_nlr_colocation/:"
	@echo "       cp PATH/03_whole-facility_profiles/colocation/simulated_data/*.csv \\"
	@echo "          data/workload/raw_nlr_colocation/"
	@echo "       cp PATH/03_whole-facility_profiles/inference/simulated_data/*.csv \\"
	@echo "          data/workload/raw_nlr_colocation/"
	@echo "  4. Run: make data-tier2  (will pick up the new CSVs and rebuild aggregates)"
	@echo ""
	@echo "Or for direct CLI download:"
	@echo "  curl -L -o /tmp/nlr.zip https://data.nlr.gov/system/files/312/1775845072-dataset.zip"
	@echo ""

data-clean:  ## Remove Tier 2 + Tier 3 regenerable files (does NOT delete Tier 1 tracked files)
	@echo "Removing Tier 2 regenerable files..."
	rm -f data/ercot/*_dam_spp_all.csv.gz data/ercot/*_dam_lmp_houston.csv
	rm -f data/ercot/*_rtm_spp_all.csv.gz data/ercot/*_rtm_lmp_houston_hourly.csv
	rm -f data/ercot/*_eia930_erco_full.csv data/ercot/*_genmix_erco.csv
	rm -f data/ercot/*_load_system_actual.csv
	rm -f data/weather/houston_ambient_*.csv data/weather/houston_hourly_*.csv
	rm -f data/weather/houston_wet_bulb_combined.csv
	rm -f data/environmental/ercot_carbon_intensity_hourly_*.csv
	rm -f data/workload/dc_200mw_real_*u_*.csv data/workload/cooling_load_pue*.csv
	rm -f data/economics/henry_hub_daily_*.csv data/economics/henry_hub_monthly_summary.csv
	rm -f data/_raw/*.log data/_raw/*.xls
	@echo "Removing Tier 3 (NLR raw 1-min profiles)..."
	rm -f data/workload/raw_nlr_colocation/*.csv
	@echo "Tier 1 (tracked) files preserved."

# =============================================================================
# Code quality
# =============================================================================

test:  ## Run pytest
	$(PYTHON) -m pytest tests/

lint:  ## Run ruff + mypy
	ruff check src tests
	mypy src

format:  ## Auto-format with black + ruff fix
	ruff check --fix src tests data/_raw
	black src tests data/_raw

check: lint test  ## Lint + test (CI gate)
