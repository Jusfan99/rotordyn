"""NiceGUI main application for RotorDyn Calculator."""

import tempfile
import time
from pathlib import Path

from nicegui import ui

from ..config import E_DEFAULT
from ..engine import ModeResult, solve
from ..models import Bearing, Rotor, RotorOptions, ShaftSection
from ..parser import parse_rin
from .components import (
    bearings_grid_data,
    build_mode_shape_figure,
    results_grid_data,
    sections_grid_data,
)
from .export import export_csv, export_excel, export_rout


class RotorDynApp:
    """Main application state and UI."""

    def __init__(self):
        self.rotor: Rotor | None = None
        self.modes: list[ModeResult] = []
        self.dark_mode = True
        self.selected_mode_idx: int = 0
        self.selected_plot_indices: list[int] = [0]
        # UI references
        self.sections_grid = None
        self.bearings_grid = None
        self.results_grid = None
        self.plot_container = None
        self.results_panel = None
        self.status_label = None
        self.mode_select = None
        self.plot_mode_select = None
        # Input fields
        self.rpm_min_input = None
        self.rpm_max_input = None
        self.rpm_incr_input = None
        self.n_crits_input = None
        self.youngs_input = None
        self.title_input = None

    def build_ui(self):
        """Build the complete UI layout."""
        self.dark = ui.dark_mode(self.dark_mode)

        # Force full-viewport layout — bypass Quasar QLayout height chain
        ui.add_head_html("""<style>
            .q-layout, .q-page-container, .q-page {
                height: 100vh !important;
                min-height: 100vh !important;
                max-height: 100vh !important;
            }
            .nicegui-content {
                height: 100vh !important;
                min-height: 100vh !important;
                max-height: 100vh !important;
                padding: 0 !important;
                display: flex !important;
                flex-direction: column !important;
                overflow: hidden !important;
            }
            .mode-card { transition: all 0.2s; cursor: pointer; }
            .mode-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
            .summary-value { font-size: 1.1em; font-weight: 500; }
            .empty-state { opacity: 0.6; }
        </style>""")

        # ── Top bar (plain row, NOT ui.header) ──
        with ui.row().classes(
            "w-full items-center justify-between px-4 text-white"
        ).style("background:#1a1a2e; min-height:48px; flex-shrink:0"):
            ui.label("RotorDyn Calculator").classes("text-xl font-bold")
            with ui.row().classes("items-center gap-2"):
                ui.button(icon="dark_mode", on_click=self._toggle_dark).props(
                    "flat round dense color=white"
                )
                ui.button(icon="info", on_click=self._show_about).props(
                    "flat round dense color=white"
                )

        # ── Main body: two-column layout ──
        with ui.row().classes("w-full items-stretch").style(
            "flex:1 1 0; min-height:0; overflow:hidden; flex-wrap:nowrap"
        ):
            # Left panel — input (scrollable)
            with ui.element("div").style(
                "width:480px; min-width:480px; overflow-y:auto; padding:16px; "
                "border-right:1px solid rgba(128,128,128,0.3)"
            ):
                self._build_input_panel()

            # Right panel — results (scrollable)
            self.right_panel = ui.element("div").style("flex:1; overflow-y:auto")
            with self.right_panel:
                self._build_results_panel()

        # ── Bottom status bar (plain row, NOT ui.footer) ──
        with ui.row().classes("w-full items-center px-4").style(
            "min-height:28px; flex-shrink:0; "
            "border-top:1px solid rgba(128,128,128,0.3)"
        ):
            self.status_label = ui.label(
                "Ready — Upload a .rin file or enter data manually"
            ).classes("text-sm")

    def _build_input_panel(self):
        """Build the left input panel (inside drawer)."""
        with ui.column().classes("w-full gap-4"):
            ui.label("Input Data").classes("text-lg font-bold")

            with ui.card().classes("w-full p-4 items-center"):
                ui.icon("upload_file", size="32px").classes("text-primary")
                ui.upload(
                    label="Click to browse or drag file here",
                    on_upload=self._handle_upload,
                    auto_upload=True,
                ).props('flat bordered color=primary').classes("w-full")

            self.title_input = ui.input(
                label="Title", value=""
            ).classes("w-full")

            ui.separator()
            ui.label("Calculation Options").classes("text-md font-bold")

            with ui.row().classes("w-full gap-2").style("flex-wrap:nowrap"):
                self.rpm_min_input = ui.number(
                    label="RPM Min", value=0, format="%.1f"
                ).style("flex:1")
                self.rpm_max_input = ui.number(
                    label="RPM Max", value=90000, format="%.1f"
                ).style("flex:1")

            with ui.row().classes("w-full gap-2").style("flex-wrap:nowrap"):
                self.rpm_incr_input = ui.number(
                    label="RPM Increment", value=50, format="%.1f"
                ).style("flex:1")
                self.n_crits_input = ui.number(
                    label="Critical Speeds", value=15, format="%.0f"
                ).style("flex:1")

            self.youngs_input = ui.number(
                label="Young's Modulus (psi)",
                value=E_DEFAULT,
                format="%.2E",
            ).classes("w-full")

            ui.separator()
            ui.label("Shaft Sections").classes("text-md font-bold")

            self.sections_grid = ui.aggrid({
                "columnDefs": [
                    {"headerName": "#", "field": "#", "width": 60,
                     "editable": False},
                    {"headerName": "I (in⁴)", "field": "I (in⁴)", "width": 110,
                     "editable": True, "type": "numericColumn",
                     "valueFormatter": "x.value?.toExponential(2)"},
                    {"headerName": "W (lb)", "field": "W (lb)", "width": 90,
                     "editable": True, "type": "numericColumn",
                     "valueFormatter": "x.value?.toFixed(1)"},
                    {"headerName": "L (in)", "field": "L (in)", "width": 90,
                     "editable": True, "type": "numericColumn",
                     "valueFormatter": "x.value?.toFixed(3)"},
                    {"headerName": "D (in)", "field": "D (in)", "width": 90,
                     "editable": True, "type": "numericColumn",
                     "valueFormatter": "x.value?.toFixed(3)"},
                ],
                "rowData": [],
                "defaultColDef": {"sortable": True, "resizable": True},
                "domLayout": "autoHeight",
            }).classes("w-full")

            with ui.row().classes("gap-2"):
                ui.button("Add Row", icon="add",
                          on_click=self._add_section_row).props("flat dense")
                ui.button("Delete Last", icon="remove",
                          on_click=self._del_section_row).props("flat dense")

            ui.separator()
            ui.label("Bearings").classes("text-md font-bold")

            self.bearings_grid = ui.aggrid({
                "columnDefs": [
                    {"headerName": "#", "field": "#", "width": 60,
                     "editable": False},
                    {"headerName": "Station", "field": "Station", "width": 100,
                     "editable": True, "type": "numericColumn"},
                    {"headerName": "KR (lb/in)", "field": "KR (lb/in)", "width": 140,
                     "editable": True, "type": "numericColumn",
                     "valueFormatter": "x.value?.toExponential(2)"},
                ],
                "rowData": [],
                "defaultColDef": {"sortable": True, "resizable": True},
                "domLayout": "autoHeight",
            }).classes("w-full")

            with ui.row().classes("gap-2"):
                ui.button("Add Bearing", icon="add",
                          on_click=self._add_bearing_row).props("flat dense")
                ui.button("Delete Last", icon="remove",
                          on_click=self._del_bearing_row).props("flat dense")

            ui.separator()
            ui.button(
                "Start Calculation",
                icon="play_arrow",
                on_click=self._run_calculation,
            ).props("color=primary unelevated").classes("w-full text-lg")

    def _build_results_panel(self):
        """Build the main results area."""
        self.results_panel = ui.column().classes("w-full p-4 gap-4")
        with self.results_panel:
            ui.label("Calculation Results").classes("text-lg font-bold")

            # Empty state
            self.empty_state = ui.column().classes("w-full items-center py-12 empty-state")
            with self.empty_state:
                ui.icon("analytics", size="64px").classes("mb-4")
                ui.label("Upload a .rin file or enter data manually,").classes("text-md")
                ui.label("then click 'Start Calculation'").classes("text-md")

            # Mode cards container — horizontal scroll, no wrap
            self.mode_cards_container = ui.row().classes("w-full gap-2").style(
                "overflow-x:auto; flex-wrap:nowrap; padding-bottom:4px"
            )
            self.mode_cards_container.set_visibility(False)

            # Plot mode selector + plot
            self.plot_section = ui.column().classes("w-full gap-2")
            self.plot_section.set_visibility(False)
            with self.plot_section:
                self.plot_mode_select = ui.select(
                    options=[],
                    label="Overlay modes on plot",
                    multiple=True,
                    value=[],
                    on_change=self._on_plot_modes_change,
                ).classes("w-full")

                self.plot_container = ui.column().classes("w-full")

            # Results detail section
            self.detail_section = ui.column().classes("w-full gap-2")
            self.detail_section.set_visibility(False)
            with self.detail_section:
                ui.separator()
                with ui.row().classes("items-center gap-4"):
                    ui.label("Detail Data").classes("text-md font-bold")
                    self.mode_select = ui.select(
                        options=[],
                        label="Select Mode",
                        value=None,
                        on_change=self._on_mode_select_change,
                    ).classes("min-w-[200px]")

                self.results_grid = ui.aggrid({
                    "columnDefs": [
                        {"headerName": "Section", "field": "Section", "width": 80},
                        {"headerName": "Length", "field": "Length", "width": 100},
                        {"headerName": "Slope", "field": "Slope", "width": 130},
                        {"headerName": "Displacement", "field": "Displacement", "width": 130},
                        {"headerName": "Moment", "field": "Moment", "width": 130},
                        {"headerName": "Shear", "field": "Shear", "width": 130},
                        {"headerName": "Type", "field": "Type", "width": 100},
                        {"headerName": "Reaction", "field": "Reaction", "width": 130},
                    ],
                    "rowData": [],
                    "defaultColDef": {
                        "sortable": True, "resizable": True, "filter": True,
                    },
                    "domLayout": "autoHeight",
                }).classes("w-full")

                # Export buttons
                with ui.row().classes("gap-2"):
                    ui.button("Export Excel", icon="table_chart",
                              on_click=self._export_excel).props("flat")
                    ui.button("Export CSV", icon="description",
                              on_click=self._export_csv).props("flat")
                    ui.button("Export rout", icon="text_snippet",
                              on_click=self._export_rout).props("flat")

    # ── Event handlers ──────────────────────────────────────────

    async def _handle_upload(self, e):
        """Handle .rin file upload."""
        try:
            # NiceGUI 3.x: e.file is a FileUpload with async read()/text()
            text = await e.file.text()
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".rin", delete=False
            ) as tmp:
                tmp.write(text)
                tmp_path = tmp.name

            self.rotor = parse_rin(tmp_path)
            Path(tmp_path).unlink(missing_ok=True)

            # Populate UI from parsed rotor
            self._populate_from_rotor()
            self.status_label.text = (
                f"Loaded: {len(self.rotor.sections)} sections, "
                f"{len(self.rotor.bearings)} bearings, "
                f"Total: {self.rotor.total_weight:.1f} lb, "
                f"{self.rotor.total_length:.3f} in"
            )
            ui.notify("File loaded successfully!", type="positive")
        except Exception as ex:
            ui.notify(f"Error parsing file: {ex}", type="negative")
            self.status_label.text = f"Error: {ex}"

    def _populate_from_rotor(self):
        """Fill UI fields from self.rotor."""
        r = self.rotor
        self.title_input.value = r.title
        self.rpm_min_input.value = r.options.rpm_min
        self.rpm_max_input.value = r.options.rpm_max
        self.rpm_incr_input.value = r.options.rpm_incr
        self.n_crits_input.value = r.options.n_crits
        self.youngs_input.value = r.options.youngs_mod

        self.sections_grid.options["rowData"] = sections_grid_data(r)
        self.sections_grid.update()

        self.bearings_grid.options["rowData"] = bearings_grid_data(r)
        self.bearings_grid.update()

    def _build_rotor_from_ui(self) -> Rotor:
        """Build a Rotor object from current UI state."""
        sec_rows = self.sections_grid.options["rowData"]
        brg_rows = self.bearings_grid.options["rowData"]

        sections = []
        for row in sec_rows:
            sections.append(ShaftSection(
                index=int(row["#"]),
                I=float(row["I (in⁴)"]),
                W=float(row["W (lb)"]),
                L=float(row["L (in)"]),
                D=float(row["D (in)"]),
            ))

        bearings = []
        for row in brg_rows:
            bearings.append(Bearing(
                index=int(row["#"]),
                station=int(row["Station"]),
                W_brg=0.0,
                KR=float(row["KR (lb/in)"]),
            ))

        options = RotorOptions(
            damp_flag=-1,
            rflex_flag=1,
            stat_flag=-1,
            rpm_min=float(self.rpm_min_input.value or 0),
            rpm_max=float(self.rpm_max_input.value or 90000),
            rpm_incr=float(self.rpm_incr_input.value or 50),
            damp_incr=5.0,
            n_crits=int(self.n_crits_input.value or 15),
            global_damping=0.0,
            youngs_mod=float(self.youngs_input.value or E_DEFAULT),
        )

        return Rotor(
            title=self.title_input.value or "Untitled",
            description="",
            options=options,
            sections=sections,
            bearings=bearings,
        )

    async def _run_calculation(self):
        """Execute the solver and display results."""
        # Validate
        sec_rows = self.sections_grid.options["rowData"]
        if not sec_rows:
            ui.notify("No shaft sections defined!", type="warning")
            return

        try:
            self.status_label.text = "Computing critical speeds..."
            self.rotor = self._build_rotor_from_ui()

            t0 = time.time()
            self.modes = solve(self.rotor)
            elapsed = time.time() - t0

            if not self.modes:
                ui.notify("No critical speeds found in RPM range.", type="warning")
                self.status_label.text = "No critical speeds found."
                return

            self._display_results()
            self.status_label.text = (
                f"Done: {len(self.modes)} critical speeds found, "
                f"elapsed {elapsed:.2f}s"
            )
            ui.notify(
                f"Found {len(self.modes)} critical speeds!",
                type="positive",
            )
        except Exception as ex:
            ui.notify(f"Calculation error: {ex}", type="negative")
            self.status_label.text = f"Error: {ex}"

    def _display_results(self):
        """Show results after calculation."""
        self.empty_state.set_visibility(False)
        self.mode_cards_container.set_visibility(True)
        self.plot_section.set_visibility(True)
        self.detail_section.set_visibility(True)

        # Mode cards — compact horizontal strip
        self.mode_cards_container.clear()
        with self.mode_cards_container:
            for i, m in enumerate(self.modes):
                with ui.card().classes("mode-card p-2").style(
                    "min-width:130px; flex-shrink:0"
                ).on("click", lambda _, idx=i: self._select_mode(idx)):
                    ui.label(
                        f"Mode {m.mode_number}"
                    ).classes("text-xs font-bold text-primary")
                    ui.label(
                        f"{m.rpm:.0f} RPM"
                    ).classes("text-xs")
                    ui.label(
                        f"{m.hz:.2f} Hz"
                    ).classes("text-xs opacity-70")

        # Plot mode selector
        mode_options = {
            i: f"Mode {m.mode_number}: {m.rpm:.1f} RPM"
            for i, m in enumerate(self.modes)
        }
        self.plot_mode_select.options = mode_options
        self.plot_mode_select.value = [0]
        self.selected_plot_indices = [0]

        # Detail mode selector
        detail_options = {
            i: f"Mode {m.mode_number}: {m.rpm:.1f} RPM ({m.hz:.2f} Hz)"
            for i, m in enumerate(self.modes)
        }
        self.mode_select.options = detail_options
        self.mode_select.value = 0

        # Render plot and table for first mode
        self._update_plot()
        self._update_results_table(0)

        # Scroll right panel to top
        ui.run_javascript(
            f'document.getElementById("c{self.right_panel.id}").scrollTop = 0;'
        )

    def _select_mode(self, idx: int):
        """Handle mode card click."""
        self.selected_mode_idx = idx
        self.mode_select.value = idx
        # Also update plot to show this mode
        if idx not in self.selected_plot_indices:
            self.selected_plot_indices.append(idx)
            self.plot_mode_select.value = self.selected_plot_indices
        self._update_plot()
        self._update_results_table(idx)

    def _on_mode_select_change(self, e):
        """Handle detail mode dropdown change."""
        if e.value is not None:
            self._update_results_table(e.value)

    def _on_plot_modes_change(self, e):
        """Handle plot mode multi-select change."""
        self.selected_plot_indices = e.value if e.value else []
        self._update_plot()

    def _update_plot(self):
        """Redraw the Plotly mode shape chart."""
        self.plot_container.clear()
        if not self.modes or not self.selected_plot_indices:
            return

        fig = build_mode_shape_figure(
            self.modes, self.selected_plot_indices, self.rotor
        )
        with self.plot_container:
            ui.plotly(fig).classes("w-full")

    def _update_results_table(self, mode_idx: int):
        """Update the detail results AG Grid for selected mode."""
        if mode_idx < 0 or mode_idx >= len(self.modes):
            return
        mode = self.modes[mode_idx]
        self.results_grid.options["rowData"] = results_grid_data(mode)
        self.results_grid.update()

    # ── Grid row operations ──────────────────────────────────────

    def _add_section_row(self):
        rows = self.sections_grid.options["rowData"]
        new_idx = (rows[-1]["#"] + 1) if rows else 1
        rows.append({"#": new_idx, "I (in⁴)": 0, "W (lb)": 0, "L (in)": 0, "D (in)": 0})
        self.sections_grid.update()

    def _del_section_row(self):
        rows = self.sections_grid.options["rowData"]
        if rows:
            rows.pop()
            self.sections_grid.update()

    def _add_bearing_row(self):
        rows = self.bearings_grid.options["rowData"]
        new_idx = (rows[-1]["#"] + 1) if rows else 1
        rows.append({"#": new_idx, "Station": 0, "KR (lb/in)": 0})
        self.bearings_grid.update()

    def _del_bearing_row(self):
        rows = self.bearings_grid.options["rowData"]
        if rows:
            rows.pop()
            self.bearings_grid.update()

    # ── Export handlers ──────────────────────────────────────────

    async def _export_excel(self):
        if not self.modes:
            ui.notify("No results to export.", type="warning")
            return
        try:
            data = export_excel(self.rotor, self.modes)
            ui.download(data, "rotordyn_results.xlsx")
            ui.notify("Excel exported!", type="positive")
        except Exception as ex:
            ui.notify(f"Export error: {ex}", type="negative")

    async def _export_csv(self):
        if not self.modes:
            ui.notify("No results to export.", type="warning")
            return
        idx = self.mode_select.value
        if idx is None:
            idx = 0
        try:
            data = export_csv(self.modes[idx])
            ui.download(
                data.encode("utf-8"),
                f"mode_{self.modes[idx].mode_number}.csv",
            )
            ui.notify("CSV exported!", type="positive")
        except Exception as ex:
            ui.notify(f"Export error: {ex}", type="negative")

    async def _export_rout(self):
        if not self.modes:
            ui.notify("No results to export.", type="warning")
            return
        try:
            data = export_rout(self.rotor, self.modes)
            ui.download(data.encode("utf-8"), "rotordyn_output.rout")
            ui.notify("rout file exported!", type="positive")
        except Exception as ex:
            ui.notify(f"Export error: {ex}", type="negative")

    # ── Misc ─────────────────────────────────────────────────────

    def _toggle_dark(self):
        self.dark_mode = not self.dark_mode
        self.dark.value = self.dark_mode

    def _show_about(self):
        with ui.dialog() as dialog, ui.card():
            ui.label("RotorDyn Calculator").classes("text-xl font-bold")
            ui.label("Lateral vibration analysis using Myklestad-Prohl transfer matrix method.")
            ui.label("Version 0.1.0")
            ui.separator()
            ui.label("Based on PH0127 / ROTCO methodology.")
            ui.button("Close", on_click=dialog.close).props("flat")
        dialog.open()


def run():
    """Launch the NiceGUI application in the default browser."""

    @ui.page("/")
    def main_page():
        application = RotorDynApp()
        application.build_ui()

    ui.run(
        title="RotorDyn Calculator",
        host="127.0.0.1",
        port=0,
        reload=False,
        show=True,
    )
