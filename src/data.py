"""Year-aware hourly time series loader for Nuclear-DC (v2.5)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union

import pandas as pd

_VALID_YEARS: set[int] = {2022, 2023, 2024}
_HOURS_PER_YEAR: int = 8760


@dataclass(frozen=True)
class TimeSeries:
    """Aligned hourly inputs for a single ERCOT operating year.

    All Series are 0-indexed of length ``num_hours`` after any slicing.
    """

    year: int
    num_hours: int
    it_load_MW: pd.Series
    wet_bulb_C: pd.Series
    price_import_usd_per_mwh: pd.Series
    carbon_intensity_g_per_kwh: pd.Series


def _read_column(path: Path, col: str, start: int, n: int) -> pd.Series:
    if not path.exists():
        raise FileNotFoundError(f"Time-series file not found: {path}")
    df = pd.read_csv(path)
    if col not in df.columns:
        raise ValueError(f"{path.name} missing required column {col!r}")
    available = len(df) - start
    if available < n:
        raise ValueError(
            f"{path.name}: only {available} rows available from start={start}, "
            f"need {n}"
        )
    return df[col].iloc[start : start + n].reset_index(drop=True).astype(float)


def load_time_series(
    project_root: Union[Path, str],
    year: int,
    num_hours: int,
    start_hour: int = 0,
) -> TimeSeries:
    """Load aligned hourly time series for one ERCOT operating year.

    Args:
        project_root: Repo root containing ``data/`` and ``config/``.
        year: One of {2022, 2023, 2024}.
        num_hours: How many consecutive hours to load (1..8760).
        start_hour: First hour to include (0-indexed).

    Returns:
        A frozen ``TimeSeries`` with IT load, wet-bulb temperature, DAM-LMP
        import price, and hourly ERCOT carbon intensity.

    Raises:
        ValueError: invalid year, non-positive num_hours, negative start_hour,
            or slice extending past hour 8760.
        FileNotFoundError: any of the required CSV files are missing.
    """
    if year not in _VALID_YEARS:
        raise ValueError(
            f"year must be one of {sorted(_VALID_YEARS)}, got {year!r}"
        )
    if num_hours <= 0:
        raise ValueError(f"num_hours must be positive, got {num_hours!r}")
    if start_hour < 0:
        raise ValueError(f"start_hour must be non-negative, got {start_hour!r}")
    if start_hour + num_hours > _HOURS_PER_YEAR:
        raise ValueError(
            f"start_hour ({start_hour}) + num_hours ({num_hours}) exceeds "
            f"{_HOURS_PER_YEAR}"
        )

    root = Path(project_root)
    it_path = root / "data" / "workload" / "dc_200mw_real_60u_2018.csv"
    wb_path = root / "data" / "weather" / f"houston_ambient_{year}.csv"
    price_path = root / "data" / "ercot" / f"{year}_dam_lmp_houston.csv"
    carbon_path = (
        root
        / "data"
        / "environmental"
        / f"ercot_carbon_intensity_hourly_{year}.csv"
    )

    return TimeSeries(
        year=year,
        num_hours=num_hours,
        it_load_MW=_read_column(it_path, "IT_load_MW", start_hour, num_hours),
        wet_bulb_C=_read_column(wb_path, "wet_bulb_C", start_hour, num_hours),
        price_import_usd_per_mwh=_read_column(
            price_path, "price_usd_per_mwh", start_hour, num_hours
        ),
        carbon_intensity_g_per_kwh=_read_column(
            carbon_path, "carbon_intensity_g_per_kwh", start_hour, num_hours
        ),
    )
