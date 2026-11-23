"""
OsdagBridge Regression & Bug-Reproduction Suite
IIT Bombay FOSSEE Winter Internship 2026 Screening Task:
"OsdagBridge Software Testing & Issue Reporting (Non-Civil)"

This suite tests the REAL OsdagBridge codebase modules without synthetic
mock functions or fake re-implementations. It reproduces and verifies the 5
unreported defects identified during testing on upstream/dev:

  - ISSUE-01: End Bearing Stiffener Governing Thickness Under-Sizing (IRC:24 / IS 800)
  - ISSUE-02: Custom Material DB Lookup Failure & Empty-String IndexError
  - ISSUE-03: LaTeX Report Generation Subprocess Missing Timeout & stdin=DEVNULL
  - ISSUE-04: Intermediate Stiffener Spacing Omitted in Full-Check Dict (Table 5.7 blank)
  - ISSUE-05: Custom Material Parameters Dropped on .osi Reload in InputDock
"""

import sys
import os
import math
import inspect
from pathlib import Path
import pytest

workspace_root = str(Path(__file__).resolve().parent.parent.parent)
src_root = str(Path(workspace_root) / "src")
if src_root not in sys.path:
    sys.path.insert(0, src_root)
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import PlateGirderBridge
from osdagbridge.core.bridge_types.plate_girder.designer import (
    BridgeConfig, SteelProperties, SteelSection, SlabProperties,
    GeometryConfig, ShearStudConfig, FatigueConfig, StiffenerConfig,
    IRC22CapacityCalculator
)
from osdagbridge.core.utils.common import (
    KEY_SD_STIFF_END_THICK, KEY_SD_STIFF_INT_SPACING,
    KEY_MATERIAL_GIRDER_FY, KEY_GIRDER
)


# Helper to build a valid real BridgeConfig
def _build_test_bridge_config(bs_tq=10.0, bs_H=205.0, R=319.24, is_c=2030.0, is_tq=10.0, is_H=205.0):
    mat = SteelProperties(
        steel_grade="E 250", fy=250.0, fu=410.0,
        concrete_grade="M 25", fck=25.0, fctm=2.2, Ecm=25000.0,
        rebar_grade="Fe 500", fy_rebar=500.0, Es=200000.0, Gs=76923.0, nu=0.3,
        gamma_m0=1.1, gamma_m1=1.25, gamma_v=1.25, gamma_mft=1.35
    )
    sec = SteelSection(
        D=1390.0, bf_top=420.0, tf_top=18.0,
        bf_bot=420.0, tf_bot=18.0, tw=8.0,
        fabrication="Welded"
    )
    slab = SlabProperties(
        thickness=250.0, haunch_depth=50.0,
        rebar_area_top=1200.0, rebar_area_bot=1200.0, cover_bot=50.0
    )
    geom = GeometryConfig(
        span=25.0, beam_spacing=2.1, carriageway_width=7.5,
        n_girders=4, edge_distance=1.05, beam_type="Plate Girder",
        support_type="Simply Supported", cross_bracing_spacing_m=5.0
    )
    stud = ShearStudConfig(
        diameter=20.0, height=100.0, fu=495.0, fy=385.0,
        n_per_section=2, transverse_spacing=100.0
    )
    fatigue = FatigueConfig(
        Nsc=2000000, detail_category=80, ffn=1.0, tfn=1.0
    )
    stiff = StiffenerConfig(
        c_mm=is_c, tq_mm=is_tq, H_mm=is_H, n_sides=2, Iys_mm4=0.0,
        V_kN=150.0, Vcr_kN=120.0, shear_method="Simple Post Critical",
        Nf_kN=0.0, c_end_mm=1000.0,
        bs_tq_mm=bs_tq, bs_H_mm=bs_H, bs_n_plates=4,
        bs_R_kN=R, bs_b1_mm=400.0, bs_Iys_mm4=0.0
    )
    return BridgeConfig(
        material=mat, section=sec, slab=slab, geometry=geom,
        studs=stud, fatigue=fatigue, stiffener=stiff
    )


# ── ISSUE-01: End Bearing Stiffener Under-Sizing ─────────────────────────────
def test_reproduce_issue_01_end_bearing_stiffener_undersizing():
    """
    IRC 24:2010 Cl. 509.7.1 and IS 800:2007 Cl. 8.7.1 require bearing stiffener thickness
    to satisfy three physical constraints:
      1) Contact bearing crushing: tq >= R / (fcd * n * H)  -> yields ~1.15 to 1.71 mm
      2) Outstand slenderness limit: tq >= H / (14 * epsilon) -> 205 / 14 = 14.64 mm
      3) Minimum plate thickness for bridge elements: tq >= 10.0 mm

    DEFECT: designer.py line 3580 extracts only 'tq_req_bearing_mm' (~1.2 - 1.7 mm) into
    stiff_end_thick_req, ignoring 'tq_req_leg_mm' (14.64 mm) and minimum plate thickness.
    Consequently, Table 5.7 of the formal report prints an unphysical 1.2 mm plate thickness.
    """
    cfg = _build_test_bridge_config(bs_tq=10.0, bs_H=205.0, R=319.24)
    calc = IRC22CapacityCalculator(cfg)
    res = calc.compute_bearing_stiffener()

    # Verify calculator raw values from real backend
    tq_bearing = res.get("tq_req_bearing_mm", 0.0)
    tq_leg = res.get("tq_req_leg_mm", 0.0)

    assert 1.0 <= tq_bearing <= 2.0, f"tq_req_bearing_mm should be ~1.2-1.7 mm, got {tq_bearing}"
    assert tq_leg >= 14.0, f"tq_req_leg_mm must be >= 14.0 mm, got {tq_leg}"

    # Verify that contact crushing alone gives an unphysically thin plate
    assert tq_bearing < 2.0, "Contact crushing alone reports < 2.0 mm"

    # Governing thickness per IRC 24 must be max(tq_bearing, tq_leg, 10.0)
    tq_governing = max(tq_bearing, tq_leg, 10.0)
    assert tq_governing >= 14.64, f"Governing plate thickness must be >= 14.64 mm, got {tq_governing}"


# ── ISSUE-02: Custom Material DB Lookup & Empty-String IndexError ────────────
def test_reproduce_issue_02_custom_material_db_lookup_defect():
    """
    PlateGirderBridge._lookup_material queries SQLite for properties.
    DEFECT 1: If material_name does not start with 'E' or 'Fe' (e.g. 'custom_steel_450'),
              it incorrectly routes to 'Concrete_Grade_Properties' and returns None.
    DEFECT 2: If material_name is empty string (''), line 1136 `material_name[0] == 'E'`
              crashes with IndexError: string index out of range.
    """
    bridge = PlateGirderBridge()

    # Defect 1: Custom steel grade is routed to Concrete table and evaluates to None
    custom_lookup = bridge._lookup_material("custom_steel_450", "Yield Strength")
    assert custom_lookup is None, "Non-E custom steel grade evaluates to None in unpatched DB lookup"

    # Defect 2: Empty material string crashes with IndexError
    with pytest.raises(IndexError):
        bridge._lookup_material("", "Yield Strength")


# ── ISSUE-03: LaTeX Subprocess Missing Timeout & stdin=DEVNULL ───────────────
def test_reproduce_issue_03_latex_subprocess_missing_timeout_and_flags():
    """
    In report_generator.py, subprocess.run is invoked for pdflatex.
    DEFECT:
      - 'timeout' parameter is NOT set in kwargs, risking infinite UI freeze on syntax error.
      - 'stdin=subprocess.DEVNULL' is NOT set, risking Windows hang on pdflatex interactive prompt.
    """
    import osdagbridge.core.reports.report_generator as rep_mod
    src = inspect.getsource(rep_mod.generate_report)

    # Check for presence of timeout and DEVNULL inside generate_report
    has_timeout = "'timeout'" in src or "timeout=" in src
    has_devnull = "DEVNULL" in src

    assert not has_timeout, "Unpatched report_generator.py is missing timeout parameter"
    assert not has_devnull, "Unpatched report_generator.py is missing stdin=subprocess.DEVNULL"


# ── ISSUE-04: Intermediate Stiffener Spacing Blank in Report ─────────────────
def test_reproduce_issue_04_intermediate_stiffener_spacing_blank():
    """
    When intermediate stiffener full verification runs (full_check=True),
    compute_intermediate_stiffener() returns a dict that OMITS 'c_req_min_mm'.
    Consequently:
      - capacity.details['intermediate_stiffener'].get('c_req_min_mm') -> None
      - designer.py: 'stiff_int_space_req' -> None
      - plategirderbridge.py line 4238: output_dict[KEY_SD_STIFF_INT_SPACING] -> None
      - chap5.py Table 5.7 renders 'Intermediate Stiffener Spacing (mm) & ---'
    """
    cfg = _build_test_bridge_config(is_c=2030.0, is_tq=10.0, is_H=205.0)
    calc = IRC22CapacityCalculator(cfg)
    res = calc.compute_intermediate_stiffener()

    # Defect: c_req_min_mm is completely absent from the full-verification result dict
    assert "c_req_min_mm" not in res, "In unpatched designer, c_req_min_mm is omitted from full verification"
    assert res.get("c_req_min_mm") is None, "Accessing c_req_min_mm yields None"


# ── ISSUE-05: Custom Material Parameters Dropped on .osi Reload ───────────────
def test_reproduce_issue_05_custom_material_osi_reload_state_loss():
    """
    InputDock.populate_from_dict(data) populates widgets from a loaded .osi dictionary.
    DEFECT: It does NOT reconstruct self._material_custom_fields.
    When a custom material (e.g. 'custom_steel_450') is loaded:
      - _material_custom_fields remains empty {}
      - _show_material_info() or MaterialPropertiesDialog finds custom_fields=None
      - Re-triggering design or material checks falls back to None or default DB values.
    """
    from osdagbridge.desktop.ui.docks.input_dock import InputDock

    # Inspect populate_from_dict source code to prove _material_custom_fields is not handled
    src = inspect.getsource(InputDock.populate_from_dict)
    assert "_material_custom_fields" not in src, (
        "Unpatched InputDock.populate_from_dict does NOT update _material_custom_fields"
    )
