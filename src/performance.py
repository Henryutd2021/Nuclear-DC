"""Part-load performance curves for the vapor-compression chiller and NGCC.

Both are expressed as a *relative* shape (multiplier vs load fraction, equal to
1.0 at full load) so they can be applied on top of the model's own full-load
operating points (the Houston-derated VCC COP and the NGCC HHV efficiency)
rather than the absolute values in the source datasets, which sit on a
different efficiency basis.
"""

from __future__ import annotations

import numpy as np

# --- VCC: relative COP vs cooling-load fraction ----------------------------
# Shape from data/_raw/build_performance_curves.py (AHRI 550/590 IPLV plus the
# Black & Veatch off-design library), normalized to 1.0 at full load. Water-
# cooled centrifugal chillers gain efficiency at part load, peaking near
# 40-50% load (the IPLV hump). data/perf/ec_cop.csv stores the absolute curve
# on a 5.75 full-load basis; here we keep only the load-relative shape.
_VCC_LOAD_FRAC = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
_VCC_REL_COP = np.array([0.0, 0.70, 0.95, 1.10, 1.18, 1.18, 1.14, 1.08, 1.04, 1.01, 1.00])

# --- NGCC: relative heat rate vs electrical-load fraction -------------------
# Representative F-class combined-cycle part-load characteristic: heat rate
# rises (efficiency falls) as load drops below the design point. Values are a
# typical CCGT shape; confirm against a preferred plant-specific source before
# publication. Relative heat-rate multiplier, 1.0 at full load.
_NGCC_LOAD_FRAC = np.array([0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00])
_NGCC_REL_HR = np.array([1.170, 1.100, 1.065, 1.040, 1.022, 1.008, 1.000])


def vcc_cop_at_load(load_fraction, cop_full_load: float):
    """VCC COP at a given cooling-load fraction (scalar or array)."""
    rel = np.interp(load_fraction, _VCC_LOAD_FRAC, _VCC_REL_COP)
    return rel * cop_full_load


def vcc_pwl_points(cop_full_load: float, q_max: float):
    """Breakpoints (cooling MWth, electricity MWe) for the VCC SOS2 piecewise.

    Returns parallel lists ``(q_pts, p_pts)`` with ``p = q / COP(load)`` at each
    cooling breakpoint; the first point is the origin. The resulting electricity
    function is non-convex (the IPLV hump), which is why an SOS2 representation
    is required instead of a convex piecewise relaxation.
    """
    q_pts = [float(lf * q_max) for lf in _VCC_LOAD_FRAC]
    p_pts = [0.0]
    for lf in _VCC_LOAD_FRAC[1:]:
        cop = float(vcc_cop_at_load(lf, cop_full_load))
        p_pts.append(float(lf * q_max) / cop)
    return q_pts, p_pts


def ngcc_hr_multiplier(load_fraction):
    """Relative heat rate at a given electrical-load fraction (>=1.0)."""
    return np.interp(load_fraction, _NGCC_LOAD_FRAC, _NGCC_REL_HR)


def ngcc_efficiency_at_load(load_fraction, eta_full: float):
    """NGCC net efficiency at a given electrical-load fraction (scalar/array)."""
    return eta_full / ngcc_hr_multiplier(load_fraction)
