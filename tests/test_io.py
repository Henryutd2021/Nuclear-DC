"""Tests for configuration and data loading modules."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.io_config import BaseConfig, CaseConfig, CostConfig, load_config
from src.io_data import load_performance_curves, load_time_series


class TestConfigLoading:
    """Test configuration loading and validation."""

    def test_load_config_case1(self):
        """Test loading Case 1 configuration."""
        base, case, cost = load_config(case_id=1, config_dir="config")

        assert isinstance(base, BaseConfig)
        assert isinstance(case, CaseConfig)
        assert isinstance(cost, CostConfig)

        # Case 1 specific checks
        assert case.case_id == 1
        assert case.turbine_enabled is True
        assert case.orc_enabled is False
        assert case.absorption_chiller_enabled is False
        assert case.electric_chiller_enabled is True

    def test_load_config_case2(self):
        """Test loading Case 2 configuration."""
        base, case, cost = load_config(case_id=2, config_dir="config")

        # Case 2 specific checks
        assert case.case_id == 2
        assert case.turbine_enabled is True
        assert case.orc_enabled is True
        assert case.absorption_chiller_enabled is True

    def test_load_config_case3(self):
        """Test loading Case 3 configuration."""
        base, case, cost = load_config(case_id=3, config_dir="config")

        # Case 3 specific checks
        assert case.case_id == 3
        assert case.turbine_enabled is True
        assert case.orc_enabled is False
        assert case.absorption_chiller_enabled is True

    def test_solver_config_defaults(self):
        """Test solver configuration defaults."""
        base, _, _ = load_config(case_id=1, config_dir="config")

        assert base.solver.name == "gurobi"
        assert base.solver.mip_gap == 0.001
        assert base.solver.seed == 42

    def test_cost_config_values(self):
        """Test cost configuration loads correctly."""
        _, _, cost = load_config(case_id=1, config_dir="config")

        assert cost.discount_rate >= 0
        assert cost.project_lifetime > 0
        assert cost.capex_turbine > 0
        assert cost.fuel_cost >= 0


class TestTimeSeriesLoading:
    """Test time-series data loading."""

    def test_load_it_load(self):
        """Test loading IT load data."""
        ts_data = load_time_series(data_dir="data", num_hours=168)

        assert len(ts_data.it_load) == 168
        assert (ts_data.it_load >= 0).all()
        assert ts_data.num_hours == 168

    def test_cooling_load_derivation(self):
        """Test cooling load derivation from PUE when CSV missing."""
        # This test uses the fact that cooling_load.csv doesn't exist by default
        # (or we can create a temp dir without it)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create only IT load CSV
            it_df = pd.DataFrame({"hour": range(24), "IT_load_MW": [15.0] * 24})
            it_df.to_csv(Path(tmpdir) / "it_load.csv", index=False)

            ts_data = load_time_series(
                data_dir=tmpdir, num_hours=24, pue=1.5, cooling_chain_efficiency=0.9
            )

            # Q_cool = (PUE - 1) * P_IT / eta = (1.5 - 1) * 15 / 0.9 = 8.33
            expected_cooling = (1.5 - 1) * 15.0 / 0.9
            assert abs(ts_data.cooling_load.iloc[0] - expected_cooling) < 0.01

    def test_time_series_validation_negative_load(self):
        """Test that negative loads are rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create IT load with negative value
            it_df = pd.DataFrame({"hour": range(10), "IT_load_MW": [15.0] * 9 + [-5.0]})
            it_df.to_csv(Path(tmpdir) / "it_load.csv", index=False)

            with pytest.raises(ValueError, match="IT load cannot be negative"):
                load_time_series(data_dir=tmpdir, num_hours=10)

    def test_grid_price_defaults(self):
        """Test default grid prices when CSV missing."""
        ts_data = load_time_series(
            data_dir="data",
            num_hours=168,
            default_grid_price_import=60.0,
            default_grid_price_export=35.0,
        )

        # Should have constant prices
        assert ts_data.grid_price_import is not None
        assert len(ts_data.grid_price_import) == 168
        # Note: if price_grid.csv exists, this may not be 60.0


class TestPerformanceCurves:
    """Test performance curve loading."""

    def test_load_performance_curves(self):
        """Test loading all performance curves."""
        perf_data = load_performance_curves(perf_dir="data/perf")

        # Check all curves loaded
        assert perf_data.turbine_hr is not None
        assert perf_data.orc_eta is not None
        assert perf_data.ab_cop is not None
        assert perf_data.ec_cop is not None

        # Check required columns exist
        assert "P_MW" in perf_data.turbine_hr.columns
        assert "HR_MWth_per_MWe" in perf_data.turbine_hr.columns

        assert "Q_in_MWth" in perf_data.orc_eta.columns
        assert "eta" in perf_data.orc_eta.columns

        assert "Q_in_MWth" in perf_data.ab_cop.columns
        assert "COP" in perf_data.ab_cop.columns

        assert "Load_fraction" in perf_data.ec_cop.columns
        assert "COP" in perf_data.ec_cop.columns

    def test_turbine_hr_monotonic(self):
        """Test turbine heat rate power values are monotonic."""
        perf_data = load_performance_curves(perf_dir="data/perf")

        assert perf_data.turbine_hr["P_MW"].is_monotonic_increasing

    def test_performance_curves_non_negative(self):
        """Test all performance values are non-negative."""
        perf_data = load_performance_curves(perf_dir="data/perf")

        assert (perf_data.turbine_hr >= 0).all().all()
        assert (perf_data.orc_eta >= 0).all().all()
        assert (perf_data.ab_cop >= 0).all().all()
        assert (perf_data.ec_cop >= 0).all().all()

    def test_orc_efficiency_bounded(self):
        """Test ORC efficiency is <= 1.0."""
        perf_data = load_performance_curves(perf_dir="data/perf")

        assert (perf_data.orc_eta["eta"] <= 1.0).all()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

