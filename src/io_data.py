"""Data loading and preprocessing for time-series and performance curves."""

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


class TimeSeriesData:
    """Container for time-series inputs."""

    def __init__(
        self,
        it_load: pd.Series,
        cooling_load: pd.Series,
        ambient_temp: Optional[pd.Series] = None,
        grid_price_import: Optional[pd.Series] = None,
        grid_price_export: Optional[pd.Series] = None,
    ):
        self.it_load = it_load
        self.cooling_load = cooling_load
        self.ambient_temp = ambient_temp
        self.grid_price_import = grid_price_import
        self.grid_price_export = grid_price_export
        self.num_hours = len(it_load)

    def validate(self) -> None:
        """Validate time-series data."""
        # Check all series have same length
        series_dict = {
            "it_load": self.it_load,
            "cooling_load": self.cooling_load,
            "ambient_temp": self.ambient_temp,
            "grid_price_import": self.grid_price_import,
            "grid_price_export": self.grid_price_export,
        }

        lengths = {k: len(v) for k, v in series_dict.items() if v is not None}
        if len(set(lengths.values())) > 1:
            raise ValueError(f"Time series have inconsistent lengths: {lengths}")

        # Check non-negativity
        if (self.it_load < 0).any():
            raise ValueError("IT load cannot be negative")
        if (self.cooling_load < 0).any():
            raise ValueError("Cooling load cannot be negative")
        if self.grid_price_import is not None and (self.grid_price_import < 0).any():
            raise ValueError("Grid import price cannot be negative")
        if self.grid_price_export is not None and (self.grid_price_export < 0).any():
            raise ValueError("Grid export price cannot be negative")

        # Check for NaNs
        for name, series in series_dict.items():
            if series is not None and series.isna().any():
                raise ValueError(f"{name} contains NaN values")


class PerformanceData:
    """Container for equipment performance curves."""

    def __init__(
        self,
        turbine_hr: pd.DataFrame,
        orc_eta: pd.DataFrame,
        ab_cop: pd.DataFrame,
        ec_cop: pd.DataFrame,
    ):
        """
        Performance curve data.

        Expected formats:
        - turbine_hr: columns ['P_MW', 'HR_MWth_per_MWe']
        - orc_eta: columns ['Q_in_MWth', 'eta'] (efficiency)
        - ab_cop: columns ['Q_in_MWth', 'COP']
        - ec_cop: columns ['Load_fraction', 'COP']
        """
        self.turbine_hr = turbine_hr
        self.orc_eta = orc_eta
        self.ab_cop = ab_cop
        self.ec_cop = ec_cop

    def validate(self) -> None:
        """Validate performance curves."""
        # Check turbine heat rate is monotonic increasing in power
        if not self.turbine_hr["P_MW"].is_monotonic_increasing:
            raise ValueError("Turbine HR curve: P_MW must be monotonic increasing")

        # Check non-negativity
        for name, df in [
            ("turbine_hr", self.turbine_hr),
            ("orc_eta", self.orc_eta),
            ("ab_cop", self.ab_cop),
            ("ec_cop", self.ec_cop),
        ]:
            if (df < 0).any().any():
                raise ValueError(f"{name} contains negative values")

        # Check efficiencies/COPs are reasonable
        if (self.orc_eta["eta"] > 1).any():
            raise ValueError("ORC efficiency cannot exceed 1.0")
        if (self.ab_cop["COP"] > 2.0).any():
            print("Warning: Absorption COP > 2.0 (unusually high for double-effect)")
        if (self.ec_cop["COP"] > 10).any():
            print("Warning: Electric chiller COP > 10 (unusually high)")


def load_time_series(
    data_dir: Path | str,
    num_hours: int,
    pue: float = 1.5,
    cooling_chain_efficiency: float = 0.9,
    default_grid_price_import: float = 50.0,
    default_grid_price_export: float = 30.0,
) -> TimeSeriesData:
    """
    Load time-series data from CSV files.

    Args:
        data_dir: Path to data directory
        num_hours: Expected number of hours
        pue: PUE for deriving cooling load if cooling_load.csv missing
        cooling_chain_efficiency: Efficiency factor for PUE→cooling conversion
        default_grid_price_import: Default import price if no CSV
        default_grid_price_export: Default export price if no CSV

    Returns:
        TimeSeriesData object
    """
    data_dir = Path(data_dir)

    # Load IT load (required)
    it_load_path = data_dir / "it_load.csv"
    if not it_load_path.exists():
        raise FileNotFoundError(f"Required file not found: {it_load_path}")

    it_df = pd.read_csv(it_load_path)
    if "hour" not in it_df.columns or "IT_load_MW" not in it_df.columns:
        raise ValueError("it_load.csv must have columns: hour, IT_load_MW")

    it_load = it_df["IT_load_MW"].iloc[:num_hours]

    # Load or derive cooling load
    cooling_load_path = data_dir / "cooling_load.csv"
    if cooling_load_path.exists():
        cool_df = pd.read_csv(cooling_load_path)
        if "hour" not in cool_df.columns or "cooling_load_MWth" not in cool_df.columns:
            raise ValueError("cooling_load.csv must have columns: hour, cooling_load_MWth")
        cooling_load = cool_df["cooling_load_MWth"].iloc[:num_hours]
    else:
        # Derive from PUE: Q_cool = (PUE - 1) * P_IT / eta_chain
        print(f"cooling_load.csv not found. Deriving from PUE={pue}")
        cooling_load = (pue - 1) * it_load / cooling_chain_efficiency

    # Load ambient temperature (optional)
    ambient_temp = None
    ambient_path = data_dir / "ambient.csv"
    if ambient_path.exists():
        amb_df = pd.read_csv(ambient_path)
        if "hour" in amb_df.columns and "wet_bulb_C" in amb_df.columns:
            ambient_temp = amb_df["wet_bulb_C"].iloc[:num_hours]
        else:
            print("Warning: ambient.csv found but missing expected columns (hour, wet_bulb_C)")

    # Load grid prices (optional)
    grid_price_import = None
    grid_price_export = None
    price_path = data_dir / "price_grid.csv"
    if price_path.exists():
        price_df = pd.read_csv(price_path)
        if "hour" in price_df.columns:
            if "price_import" in price_df.columns:
                grid_price_import = price_df["price_import"].iloc[:num_hours]
            if "price_export" in price_df.columns:
                grid_price_export = price_df["price_export"].iloc[:num_hours]
    else:
        # Use constant default prices
        grid_price_import = pd.Series([default_grid_price_import] * num_hours)
        grid_price_export = pd.Series([default_grid_price_export] * num_hours)

    ts_data = TimeSeriesData(
        it_load=it_load,
        cooling_load=cooling_load,
        ambient_temp=ambient_temp,
        grid_price_import=grid_price_import,
        grid_price_export=grid_price_export,
    )
    ts_data.validate()

    return ts_data


def load_performance_curves(perf_dir: Path | str) -> PerformanceData:
    """
    Load performance curves from CSV files.

    Args:
        perf_dir: Path to data/perf directory

    Returns:
        PerformanceData object
    """
    perf_dir = Path(perf_dir)

    # Turbine heat rate
    turb_hr = pd.read_csv(perf_dir / "turbine_hr.csv")
    required_cols = ["P_MW", "HR_MWth_per_MWe"]
    if not all(col in turb_hr.columns for col in required_cols):
        raise ValueError(f"turbine_hr.csv must have columns: {required_cols}")

    # ORC efficiency
    orc_eta = pd.read_csv(perf_dir / "orc_eta.csv")
    required_cols = ["Q_in_MWth", "eta"]
    if not all(col in orc_eta.columns for col in required_cols):
        raise ValueError(f"orc_eta.csv must have columns: {required_cols}")

    # Absorption COP
    ab_cop = pd.read_csv(perf_dir / "ab_cop.csv")
    required_cols = ["Q_in_MWth", "COP"]
    if not all(col in ab_cop.columns for col in required_cols):
        raise ValueError(f"ab_cop.csv must have columns: {required_cols}")

    # Electric chiller COP
    ec_cop = pd.read_csv(perf_dir / "ec_cop.csv")
    required_cols = ["Load_fraction", "COP"]
    if not all(col in ec_cop.columns for col in required_cols):
        raise ValueError(f"ec_cop.csv must have columns: {required_cols}")

    perf_data = PerformanceData(
        turbine_hr=turb_hr,
        orc_eta=orc_eta,
        ab_cop=ab_cop,
        ec_cop=ec_cop,
    )
    perf_data.validate()

    return perf_data


if __name__ == "__main__":
    # Quick test
    print("Data loading module loaded successfully.")
    print("TimeSeriesData and PerformanceData classes available.")

