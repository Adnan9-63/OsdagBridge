# OsdagBridge Software Testing & Issue Reporting (Non-Civil)
**IIT Bombay FOSSEE Winter Internship 2026 Screening Task**  
**Author:** Md Adnan  
**Fork Repository:** [https://github.com/Adnan9-63/OsdagBridge](https://github.com/Adnan9-63/OsdagBridge) (Branch: `dev`)  
**Upstream Target:** [https://github.com/Nidhikhare12/OsdagBridge](https://github.com/Nidhikhare12/OsdagBridge)  

---

## 1. Overview & Verified Environment

This repository branch contains the complete test suite, automated test harnesses, saved JSON logs, standalone regression tests, and clean unified patches evaluating **OsdagBridge** (composite plate girder bridge design software under IRC:5, IRC:6, IRC:22, IRC:24, and IS 800:2007).

### Verified Environment Specifications
All tests, GUI interactions, OpenCASCADE 3D CAD renders, and OpenSees grillage analyses were executed within Conda environment `osdagbridge-env`:
- **Operating System:** Windows 11 x86_64
- **Python:** `3.12.16` (CPython, conda-forge)
- **PySide6 (Qt for Python):** `6.11.3`
- **pythonocc-core (OpenCASCADE 7.8/8.0 C++ bindings):** `8.0.1.2`
- **OpenSeesPy:** `3.8.0.0`
- **opsvis:** `1.3.8`
- **SciPy:** `1.18.1`
- **xarray:** `2026.9.0`
- **pytest:** `9.2.0`
- **pypdfium2:** `5.15.2`

---

## 2. Upstream Defect Contributions & Patch Portfolio

All 191 pre-existing upstream issues and pull requests on `Nidhikhare12/OsdagBridge` were audited prior to filing to guarantee zero duplicate submissions. The table below lists the 5 verified novel issues and 1 corroborating resolution submitted upstream:

| Issue / Reference | Defect Summary & Impact | Severity | Target Module | Clean Patch File |
|---|---|---|---|---|
| [**Issue #262**](https://github.com/Nidhikhare12/OsdagBridge/issues/262) | **End Panel Stiffener Thickness Reports Unphysical 1.2 mm in Report:** In Optimized mode, Table 5.7 exports raw contact crushing (`1.15 mm`) ignoring outstand slenderness ($14.64\text{ mm}$) and minimum plate thickness ($10\text{ mm}$). | High (Civil/Design) | `designer.py:3580`<br>`plategirderbridge.py:4239` | [`fix_06_stiffener_end_thickness_governing.patch`](patches/fix_06_stiffener_end_thickness_governing.patch) |
| [**Issue #263**](https://github.com/Nidhikhare12/OsdagBridge/issues/263) | **Custom Material Grade Dropped to None in output_dict:** When user defines a custom steel grade, `output_dict['steeldesign.details.material_grade']` evaluates to `None` and designation renders blank in design report. | Medium (Data Pipeline) | `plategirderbridge.py:4273`<br>`chap2.py:150` | [`fix_05_custom_material_grade_propagation.patch`](patches/fix_05_custom_material_grade_propagation.patch) |
| [**Issue #264**](https://github.com/Nidhikhare12/OsdagBridge/issues/264) | **Windows PDF Report Generator Deadlock:** `subprocess.run(pdflatex)` missing `stdin=subprocess.DEVNULL` and `timeout=60`, causing GUI to hang permanently on package prompts or syntax warnings. | High (Process Hang) | `report_generator.py:964` | [`fix_04_pdflatex_hang_timeout.patch`](patches/fix_04_pdflatex_hang_timeout.patch) |
| [**Issue #265**](https://github.com/Nidhikhare12/OsdagBridge/issues/265) | **Intermediate Stiffener Spacing Renders Blank in Table 5.7:** Full verification omitted `c_req_min_mm` from calculator dict, resulting in `None` in `output_dict` and an empty cell in the formal report. | Low/Med (Reporting) | `designer.py:1575`<br>`plategirderbridge.py:4238` | [`fix_08_intermediate_stiffener_spacing_report.patch`](patches/fix_08_intermediate_stiffener_spacing_report.patch) |
| [**Issue #266**](https://github.com/Nidhikhare12/OsdagBridge/issues/266) | **Custom Material Definitions Dropped on .osi Reload:** `InputDock.populate_from_dict()` fails to reconstruct `_material_custom_fields`, silently resetting custom steel to `E 350A` and concrete to `M40`. | High (State Loss) | `input_dock.py:1080`<br>`template_page.py:859` | [`fix_07_osi_custom_material_reload.patch`](patches/fix_07_osi_custom_material_reload.patch) |
| [**Comment on #53**](https://github.com/Nidhikhare12/OsdagBridge/issues/53#issuecomment-7095025168) | **Dead Menu Actions Reflection Audit:** PySide6 reflection (`isSignalConnected`) proves 8 QActions across Database, Graphics, and Help menus have 0 connected receivers (also resolves #123). | High (UI/Signals) | `template_page.py:1817-1845` | [`fix_01_dead_menu_actions.patch`](patches/fix_01_dead_menu_actions.patch) |

### Additional Supporting Patches
- [`fix_02_missing_shear_modulus_g.patch`](patches/fix_02_missing_shear_modulus_g.patch): Sets fallback elastic shear modulus $G = E / (2(1+\nu))$ if omitted in minimal project inputs.
- [`fix_03_stiffener_material_sync.patch`](patches/fix_03_stiffener_material_sync.patch): Automatically propagates custom girder steel properties to stiffener components.

---

## 3. Summary of Test Cases (TC-01 to TC-16)

The comprehensive test suite (`run_test_matrix.py`, `run_deep_audit.py`, and `run_extended_audit.py`) executed 16 end-to-end scenarios covering nominal design, custom materials, boundary geometry, multi-run persistence, and secondary components:

| Test ID | Scenario Description | Status | Duration | Key Observations & Verified Telemetry |
|---|---|:---:|:---:|---|
| **TC-01** | Baseline Nominal Design & Artifact Generation | **PASS** | 250.98s | Standard 25m span, 7.5m carriageway, Class 70R loading. Verified 3D CAD, moment/shear envelopes, and 28-page PDF report. |
| **TC-02** | Custom Material Properties (Steel & Concrete) | **FAIL** | 130.86s | Custom $f_y = 350\text{ MPa}, f_u = 490\text{ MPa}$, deck $M\,35$. Discovered `steeldesign.details.material_grade` loss in output dictionary (Issue #263). |
| **TC-03** | Stiffener Material Inheritance & Configuration | **PASS** | 127.68s | Stiffener design check audit. Discovered the $1.2\text{ mm}$ end bearing thickness defect (Issue #262). |
| **TC-04** | 4 Consecutive Multi-Run State Persistence & Reset | **PASS** | 723.93s | 4 consecutive design iterations (25m $\rightarrow$ 35m $\rightarrow$ $15^\circ$ Skew $\rightarrow$ 25m) without restart. Verified memory cleanup and zero dictionary leakage. |
| **TC-05** | .osi Save & Load Round-Trip Integrity | **PASS** | 1.04s | Validated YAML schema and serialization for baseline, custom material, stiffener, and skewed project files. |
| **TC-06** | Boundary & Extreme Geometric Inputs | **PASS** | 0.00s | Verified input boundary rejection (10m short span clamped, 45m span, $45^\circ$ skew rejected, 60m extreme span). |
| **TC-07** | Invalid / Malformed Input & Error Handling | **PASS** | 0.32s | Verified negative spans, zero widths, and non-numeric inputs trigger modal warnings without crashing. |
| **TC-08** | Menu Bar Actions & Signal Introspection | **FAIL** | 0.02s | PySide6 reflection audit identified 8 dead QActions (Issues #53 & #123). Provided patch `fix_01`. |
| **TC-09** | Controlled A/B Custom Material Verification | **PASS** | 195.98s | Identical 25m geometry: Run A ($f_y=250$) vs. Run B ($f_y=450$). Both yield $M_d = \text{None}$ and $UR = 23.88$; custom grade dropped to None (Issue #263). |
| **TC-10** | Additional Inputs Coverage (Wind, Seismic, Deck) | **PASS** | 125.14s | Zone V seismic coefficients ($Z=0.36, (S_a/g)=2.8$), $50\text{ m/s}$ basic wind speed, footpath configurations. |
| **TC-11** | 3-Way End-to-End Consistency Audit | **PASS** | 0.09s | Cross-audited UI widgets vs `input_dict` vs `output_dict` vs PDF report. Confirmed Table 5.7 blank spacing discrepancy (Issue #265). |
| **TC-12** | Multi-Run Graphical State Verification | **PASS** | 281.60s | Verified OpenCASCADE 3D viewport redraws across span transitions ($25\text{m} \rightarrow 35\text{m}$) and skew angles ($0^\circ \rightarrow 15^\circ$). |
| **TC-13** | Concrete Deck A/B & Shear Connectors | **PASS** | 211.29s | Modular ratio updated ($m=8.00 \rightarrow 5.88$), but transformed composite $I_z$ remained $2,186,569.09\text{ cm}^4$ in initial sizing telemetry. |
| **TC-14** | Custom Material .osi Round-Trip State Loss | **FAIL** | 115.57s | Discovered defect where saving custom materials to `.osi` and reloading silently resets steel to `E 350A` and concrete to `M40` (Issue #266). |
| **TC-15** | Component-Level Verification | **PASS** | 123.92s | Audited Rolled Beam, Welded Beam, Cross Bracing (K/X bracings) across all 6 components $\times$ 5 software layers. |
| **TC-16** | Visual Proof Extraction & Technical Charts | **PASS** | 2.89s | Programmatically rendered Page 28 of generated PDF to extract visual proof of Table 5.7 stiffener defects (`fig_table57_stiffener_bug.png`). |

---

## 4. Verification Commands

To verify all findings and test suites locally:

```powershell
# 1. Run the standalone regression suite (direct imports against real modules, 12.28s):
python -m pytest fossee_submission/tests/test_fossee_regression.py -v

# 2. Verify all 8 unified patches apply cleanly with zero reject:
git apply --check fossee_submission/patches/*.patch
```

---

## 5. Directory Structure of `fossee_submission/`

```
fossee_submission/
├── README.md                            # Comprehensive submission summary
├── osi_cases/                           # 9 verified .osi project input files
│   ├── TC01_baseline_nominal.osi
│   ├── TC02_custom_materials.osi
│   ├── TC03_stiffeners.osi
│   ├── TC04_multirun_final.osi
│   ├── TC09A_default_materials.osi
│   ├── TC09B_custom_materials.osi
│   ├── TC10_additional_inputs.osi
│   ├── TC13_custom_concrete_deck.osi
│   └── TC14_custom_materials.osi
├── patches/                             # 8 verified unified git patches
│   ├── fix_01_dead_menu_actions.patch
│   ├── fix_02_missing_shear_modulus_g.patch
│   ├── fix_03_stiffener_material_sync.patch
│   ├── fix_04_pdflatex_hang_timeout.patch
│   ├── fix_05_custom_material_grade_propagation.patch
│   ├── fix_06_stiffener_end_thickness_governing.patch
│   ├── fix_07_osi_custom_material_reload.patch
│   └── fix_08_intermediate_stiffener_spacing_report.patch
├── report/                              # Technical report and proof figures
│   ├── compile_report.py                # Standalone script to compile report
│   ├── generate_plots.py                # Standalone script to generate plots
│   ├── OsdagBridge_Testing_Report.tex   # Academic LaTeX source
│   ├── OsdagBridge_Testing_Report.pdf   # Compiled PDF report (9 pages, 699 KB)
│   └── figures/                         # High-resolution visual proof figures
│       ├── fig_gui_3d_cad.png
│       ├── fig_gui_custom_material.png
│       ├── fig_multirun_persistence.png
│       └── fig_table57_stiffener_bug.png
├── tests/
│   └── test_fossee_regression.py        # 5-test standalone regression suite (12.28s)
├── scripts/
│   ├── telemetry_logger.py              # Dictionary audit & logging hook
│   ├── run_test_matrix.py               # TC-01 to TC-08 test runner
│   ├── run_deep_audit.py                # TC-09 to TC-12 deep audit runner
│   └── run_extended_audit.py            # TC-13 to TC-16 extended audit runner
└── logs/
    ├── test_cases_summary.csv           # Master CSV summary of all test cases
    ├── test_cases_summary.json          # Master JSON telemetry log
    ├── pytest_verification.log          # Verbatim pytest execution log
    └── run_1_dict_audit.json            # 3-way dictionary audit log
```
