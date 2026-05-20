"""Tests for src.config — Pydantic schemas + v2.5 locked values."""

from pathlib import Path

import pytest

from src.config import load_config

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_load_case0_returns_run_config():
    cfg = load_config(case_id=0, project_root=PROJECT_ROOT)
    assert cfg.case.case_id == 0
    assert cfg.case.label == "Grid-only baseline"


def test_case0_equipment_flags_match_v25_locked_spec():
    cfg = load_config(case_id=0, project_root=PROJECT_ROOT)
    eq = cfg.case.equipment
    # v2.5 §B Case 0 = pure grid + VCC
    assert eq.reactor_enabled is False
    assert eq.turbine_enabled is False
    assert eq.orc_enabled is False
    assert eq.absorption_chiller_enabled is False
    assert eq.electric_chiller_enabled is True
    assert eq.tes_enabled is False
    assert eq.bess_enabled is False
    assert eq.ngcc_enabled is False
    assert eq.grid_import_enabled is True
    assert eq.grid_export_enabled is False


def test_case0_capacities_cover_pue150_worst_hour():
    """Case 0 chiller must cover (PUE-1)*P_IT_max at the most cooling-heavy PUE."""
    cfg = load_config(case_id=0, project_root=PROJECT_ROOT)
    # P_IT_max ≈ 142.4 MW (NLR Vercellino dataset), PUE=1.50 → Q_cool ≈ 71 MWth
    # Allow margin → capacity ≥ 120 MWth
    assert cfg.case.capacities.electric_chiller_capacity_MWth >= 120.0


def test_case0_vcc_houston_derated_cop_is_below_nameplate():
    cfg = load_config(case_id=0, project_root=PROJECT_ROOT)
    vcc = cfg.case.vcc
    assert vcc is not None
    assert vcc.cop_houston < vcc.cop_baseline   # derating applied
    assert vcc.cop_baseline == pytest.approx(3.5, abs=0.01)
    assert vcc.cop_houston == pytest.approx(3.2, abs=0.05)


def test_financial_params_match_v25_locked_values():
    """v2.5 §A: WACC=6.7%, n=20 → CRF=0.0922 (reconciled 2026-05-19)."""
    cfg = load_config(case_id=0, project_root=PROJECT_ROOT)
    assert cfg.financial.WACC_nominal == pytest.approx(0.067, abs=1e-4)
    assert cfg.financial.project_lifetime_years == 20
    assert cfg.financial.capital_recovery_factor == pytest.approx(0.0922, abs=1e-4)


def test_crf_self_consistent_with_formula():
    """CRF = i(1+i)^n / ((1+i)^n - 1) must match the stored value."""
    cfg = load_config(case_id=0, project_root=PROJECT_ROOT)
    i = cfg.financial.WACC_nominal
    n = cfg.financial.project_lifetime_years
    computed = i * (1 + i) ** n / ((1 + i) ** n - 1)
    assert computed == pytest.approx(cfg.financial.capital_recovery_factor, abs=1e-4)


def test_base_time_and_solver_loaded():
    cfg = load_config(case_id=0, project_root=PROJECT_ROOT)
    assert cfg.base.time.num_hours > 0
    assert cfg.base.time.delta_t == pytest.approx(1.0)
    assert cfg.base.solver.name in {"gurobi", "highs", "cbc"}
    assert 0 < cfg.base.solver.mip_gap < 1


def test_invalid_case_id_rejected():
    with pytest.raises(ValueError, match=r"case_id"):
        load_config(case_id=5, project_root=PROJECT_ROOT)
    with pytest.raises(ValueError, match=r"case_id"):
        load_config(case_id=-1, project_root=PROJECT_ROOT)


def test_missing_yaml_raises_filenotfound():
    """Bogus project root must raise FileNotFoundError on the first yaml read."""
    with pytest.raises(FileNotFoundError):
        load_config(case_id=0, project_root="/nonexistent/path/Nuclear-DC")
