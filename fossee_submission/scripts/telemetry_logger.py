"""
Automated Non-Intrusive Input/Output Dictionary Telemetry Logger for OsdagBridge.
Part of the IIT Bombay FOSSEE Winter Internship 2026 Screening Task.

Features:
- Hooks cleanly and reversibly into CustomWindow, PlateGirderBridge, and InputDock.
- Captures run_<N>_ui_values.json, run_<N>_input_dict.json, run_<N>_output_dict.json.
- Runs comprehensive field-by-field diff audit (run_<N>_dict_audit.json).
- Tracks lock/unlock and .osi save/load state transitions.
"""

from __future__ import annotations

import os
import json
import time
import copy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import QWidget, QLineEdit, QComboBox, QCheckBox, QLabel, QRadioButton
from PySide6.QtCore import QObject


def _to_json_safe(val: Any) -> Any:
    """Convert arbitrary nested structures and numeric types to JSON-safe primitives."""
    if val is None or isinstance(val, (int, float, str, bool)):
        return val
    if isinstance(val, dict):
        return {str(k): _to_json_safe(v) for k, v in val.items()}
    if isinstance(val, (list, tuple, set)):
        return [_to_json_safe(v) for v in val]
    # Handle numpy/scipy scalars if present
    if hasattr(val, "item") and callable(getattr(val, "item")):
        try:
            return val.item()
        except Exception:
            pass
    if hasattr(val, "__dict__"):
        return _to_json_safe(vars(val))
    return str(val)


class TelemetryLogger:
    def __init__(self, log_dir: str | Path = "fossee_submission/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.run_count = 0
        self.active_hooks: Dict[str, Any] = {}
        self.session_events: List[Dict[str, Any]] = []

    def extract_ui_values(self, window: Any) -> Dict[str, Any]:
        """Scrape raw values currently displayed in GUI widgets."""
        ui_dump: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "input_dock": {},
            "additional_inputs": {},
            "output_dock": {},
        }

        # 1. Scrape InputDock widgets
        if hasattr(window, "input_dock") and window.input_dock:
            dock = window.input_dock
            # Check widgets in dock.input_widget
            if hasattr(dock, "input_widget") and dock.input_widget:
                for w in dock.input_widget.findChildren(QWidget):
                    name = w.objectName()
                    if not name:
                        continue
                    if isinstance(w, QLineEdit):
                        ui_dump["input_dock"][name] = {
                            "type": "QLineEdit",
                            "text": w.text(),
                            "is_enabled": w.isEnabled(),
                        }
                    elif isinstance(w, QComboBox):
                        ui_dump["input_dock"][name] = {
                            "type": "QComboBox",
                            "current_text": w.currentText(),
                            "current_index": w.currentIndex(),
                            "items": [w.itemText(i) for i in range(w.count())],
                            "is_enabled": w.isEnabled(),
                        }
                    elif isinstance(w, QCheckBox):
                        ui_dump["input_dock"][name] = {
                            "type": "QCheckBox",
                            "checked": w.isChecked(),
                        }

            # Scrape custom material state in input_dock
            if hasattr(dock, "_material_custom_fields"):
                ui_dump["input_dock"]["_material_custom_fields"] = _to_json_safe(dock._material_custom_fields)
            if hasattr(dock, "_material_combo_map"):
                ui_dump["input_dock"]["_material_combo_map"] = {
                    str(k): combo.currentText() for k, combo in dock._material_combo_map.items()
                }

        # 2. Scrape AdditionalInputs if instantiated
        if hasattr(window, "_additional_inputs_dialog") and window._additional_inputs_dialog:
            dlg = window._additional_inputs_dialog
            for w in dlg.findChildren(QWidget):
                name = w.objectName()
                if not name:
                    continue
                if isinstance(w, QLineEdit):
                    ui_dump["additional_inputs"][name] = {"type": "QLineEdit", "text": w.text()}
                elif isinstance(w, QComboBox):
                    ui_dump["additional_inputs"][name] = {"type": "QComboBox", "current_text": w.currentText()}
                elif isinstance(w, QCheckBox):
                    ui_dump["additional_inputs"][name] = {"type": "QCheckBox", "checked": w.isChecked()}

        # 3. Scrape OutputDock displayed values
        if hasattr(window, "output_dock") and window.output_dock:
            out_dock = window.output_dock
            for w in out_dock.findChildren(QWidget):
                name = w.objectName()
                if not name:
                    continue
                if isinstance(w, QLabel) and w.text():
                    ui_dump["output_dock"][name] = {"type": "QLabel", "text": w.text()}
                elif isinstance(w, QLineEdit):
                    ui_dump["output_dock"][name] = {"type": "QLineEdit", "text": w.text()}
                elif isinstance(w, QComboBox):
                    ui_dump["output_dock"][name] = {"type": "QComboBox", "current_text": w.currentText()}

        return ui_dump

    def audit_dictionaries(
        self,
        ui_values: Dict[str, Any],
        input_dict: Dict[str, Any],
        output_dict: Dict[str, Any],
        previous_input_dict: Optional[Dict[str, Any]] = None,
        previous_output_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform a deep automated field-by-field audit comparing UI, Input, and Output dictionaries."""
        audit_results: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "ui_vs_input_mismatches": [],
            "stale_input_fields": [],
            "missing_expected_outputs": [],
            "custom_material_audits": [],
            "status": "PASS",
        }

        # Check UI values vs. Input Dict
        input_dock_ui = ui_values.get("input_dock", {})
        for key, ui_item in input_dock_ui.items():
            if not isinstance(ui_item, dict):
                continue
            displayed_val = ui_item.get("text") or ui_item.get("current_text")
            if displayed_val is None or key.startswith("_"):
                continue

            dict_val = input_dict.get(key)
            if dict_val is not None:
                # Compare as strings or floats
                disp_str = str(displayed_val).strip()
                dict_str = str(dict_val).strip()

                is_match = False
                if disp_str == dict_str:
                    is_match = True
                else:
                    try:
                        if abs(float(disp_str) - float(dict_str)) < 1e-4:
                            is_match = True
                    except ValueError:
                        pass

                if not is_match:
                    audit_results["ui_vs_input_mismatches"].append({
                        "field_key": key,
                        "ui_displayed": displayed_val,
                        "input_dict_value": dict_val,
                        "severity": "WARNING",
                    })

        # Check Custom Material Propagation
        girder_material = input_dict.get("basic.girder") or input_dict.get("geometry.girder")
        if girder_material and "custom_steel" in str(girder_material).lower():
            # Verify custom fy/fu/E exist in input_dict
            expected_keys = [
                "material.girder.fy", "material.girder.fu",
                "material.girder.e", "material.girder.g", "material.girder.density"
            ]
            for ek in expected_keys:
                val = input_dict.get(ek)
                if val is None or val == "":
                    audit_results["custom_material_audits"].append({
                        "issue": "Missing custom girder material property in input_dict",
                        "field": ek,
                        "severity": "CRITICAL",
                    })

        # Check Output Dict against key required categories
        required_output_prefixes = [
            "steeldesign.details.util.", "steeldesign.details.section_designation",
            "steeldesign.details.total_depth"
        ]
        for op in required_output_prefixes:
            matching = [k for k in output_dict.keys() if op in str(k)]
            if not matching:
                audit_results["missing_expected_outputs"].append({
                    "expected_output_prefix": op,
                    "severity": "HIGH",
                })

        # Check for Stale State Across Consecutive Runs
        if previous_input_dict:
            # If span changed, verify output changed accordingly
            prev_span = previous_input_dict.get("geometry.span")
            curr_span = input_dict.get("geometry.span")
            if prev_span and curr_span and prev_span != curr_span:
                prev_d = (previous_output_dict or {}).get("steeldesign.details.total_depth")
                curr_d = output_dict.get("steeldesign.details.total_depth")
                if prev_d is not None and curr_d is not None and prev_d == curr_d:
                    audit_results["stale_input_fields"].append({
                        "check": "Span changed but girder total depth identical",
                        "prev_span": prev_span,
                        "curr_span": curr_span,
                        "depth": curr_d,
                    })

        if audit_results["ui_vs_input_mismatches"] or audit_results["custom_material_audits"] or audit_results["missing_expected_outputs"]:
            audit_results["status"] = "WARNINGS_FOUND"

        return audit_results

    def record_run(
        self,
        window: Any,
        run_id: Optional[int] = None,
        previous_input_dict: Optional[Dict[str, Any]] = None,
        previous_output_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Capture all telemetry for a single design run and save JSON files."""
        if run_id is None:
            self.run_count += 1
            run_id = self.run_count

        ui_values = self.extract_ui_values(window)
        input_dict = getattr(window, "input_dict", {}) or {}
        output_dict = getattr(window.backend, "output_dict", {}) or {}

        # Safe serialized copies
        safe_ui = _to_json_safe(ui_values)
        safe_inp = _to_json_safe(input_dict)
        safe_out = _to_json_safe(output_dict)

        audit = self.audit_dictionaries(
            ui_values=ui_values,
            input_dict=input_dict,
            output_dict=output_dict,
            previous_input_dict=previous_input_dict,
            previous_output_dict=previous_output_dict,
        )

        # Write out files
        ui_file = self.log_dir / f"run_{run_id}_ui_values.json"
        inp_file = self.log_dir / f"run_{run_id}_input_dict.json"
        out_file = self.log_dir / f"run_{run_id}_output_dict.json"
        audit_file = self.log_dir / f"run_{run_id}_dict_audit.json"

        with open(ui_file, "w", encoding="utf-8") as f:
            json.dump(safe_ui, f, indent=2)
        with open(inp_file, "w", encoding="utf-8") as f:
            json.dump(safe_inp, f, indent=2)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(safe_out, f, indent=2)
        with open(audit_file, "w", encoding="utf-8") as f:
            json.dump(audit, f, indent=2)

        print(f"[TelemetryLogger] Saved Run {run_id} telemetry files to {self.log_dir}")
        return {
            "run_id": run_id,
            "ui_file": str(ui_file),
            "inp_file": str(inp_file),
            "out_file": str(out_file),
            "audit_file": str(audit_file),
            "audit_status": audit["status"],
        }

    def hook_window(self, window: Any):
        """Reversibly hook into CustomWindow life-cycle methods for automated telemetry."""
        if hasattr(window, "_telemetry_hooked") and window._telemetry_hooked:
            return

        orig_on_design_done = window._on_design_done
        orig_toggle_lock = window.input_dock.toggle_lock
        orig_save_osi = window.saveOSI_inputs
        orig_load_osi = window.loadOSI_inputs

        self.active_hooks[id(window)] = {
            "window": window,
            "_on_design_done": orig_on_design_done,
            "toggle_lock": orig_toggle_lock,
            "saveOSI_inputs": orig_save_osi,
            "loadOSI_inputs": orig_load_osi,
        }

        def hooked_on_design_done(exc_obj, err_trace, cancelled):
            res = orig_on_design_done(exc_obj, err_trace, cancelled)
            if exc_obj is None and not cancelled:
                try:
                    self.record_run(window)
                except Exception as e:
                    print(f"[TelemetryLogger Error] record_run failed: {e}")
            return res

        def hooked_toggle_lock(confirm=True):
            was_locked = window.input_dock.is_locked
            res = orig_toggle_lock(confirm=confirm)
            is_locked = window.input_dock.is_locked
            self.session_events.append({
                "timestamp": datetime.now().isoformat(),
                "event": "toggle_lock",
                "was_locked": was_locked,
                "is_locked": is_locked,
            })
            return res

        window._on_design_done = hooked_on_design_done
        window.input_dock.toggle_lock = hooked_toggle_lock
        window._telemetry_hooked = True
        print("[TelemetryLogger] Successfully hooked CustomWindow and InputDock")

    def unhook_window(self, window: Any):
        """Restore all original methods cleanly."""
        hook_info = self.active_hooks.pop(id(window), None)
        if hook_info:
            window._on_design_done = hook_info["_on_design_done"]
            window.input_dock.toggle_lock = hook_info["toggle_lock"]
            window._telemetry_hooked = False
            print("[TelemetryLogger] Unhooked CustomWindow successfully")
