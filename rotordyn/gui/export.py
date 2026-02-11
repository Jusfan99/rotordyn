"""Export functionality for Excel/CSV/rout formats."""

import csv
import io
from pathlib import Path

from openpyxl import Workbook

from ..engine import ModeResult
from ..formatter import format_output
from ..models import Rotor


def export_excel(rotor: Rotor, modes: list[ModeResult]) -> bytes:
    """Export all mode results to Excel (.xlsx) and return bytes."""
    wb = Workbook()

    # Summary sheet
    ws_summary = wb.active
    ws_summary.title = "Summary"
    ws_summary.append(["Mode", "RPM", "Hz", "Gen. Mass", "Eff. Mass"])
    for m in modes:
        ws_summary.append([
            m.mode_number, m.rpm, m.hz,
            m.generalized_mass, m.effective_mass,
        ])
    # Auto-width
    for col in ws_summary.columns:
        max_len = max(len(str(c.value or "")) for c in col)
        ws_summary.column_dimensions[col[0].column_letter].width = max_len + 2

    # One sheet per mode
    for m in modes:
        ws = wb.create_sheet(f"Mode {m.mode_number}")
        ws.append(["Section", "Length", "Slope", "Displacement",
                   "Moment", "Shear", "Type", "Reaction"])
        for st in m.stations:
            ws.append([
                st["section"], st["length"], st["slope"],
                st["displacement"], st["moment"], st["shear"],
                st["type"], st["reaction"],
            ])
        for col in ws.columns:
            max_len = max(len(str(c.value or "")) for c in col)
            ws.column_dimensions[col[0].column_letter].width = max_len + 2

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def export_csv(mode: ModeResult) -> str:
    """Export a single mode result to CSV string."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Section", "Length", "Slope", "Displacement",
                     "Moment", "Shear", "Type", "Reaction"])
    for st in mode.stations:
        writer.writerow([
            st["section"], st["length"], st["slope"],
            st["displacement"], st["moment"], st["shear"],
            st["type"], st["reaction"],
        ])
    return buf.getvalue()


def export_rout(rotor: Rotor, modes: list[ModeResult]) -> str:
    """Export in original rout text format."""
    return format_output(rotor, modes)
