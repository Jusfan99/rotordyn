"""Reusable UI components for RotorDyn GUI."""

import plotly.graph_objects as go

from ..engine import ModeResult
from ..models import Rotor


def build_mode_shape_figure(
    modes: list[ModeResult],
    selected_indices: list[int],
    rotor: Rotor,
) -> go.Figure:
    """Build a Plotly figure showing mode shapes.

    Args:
        modes: All computed mode results.
        selected_indices: 0-based indices of modes to display.
        rotor: The rotor model (for bearing positions).
    """
    fig = go.Figure()

    colors = [
        "#2196F3", "#FF5722", "#4CAF50", "#FFC107", "#9C27B0",
        "#00BCD4", "#E91E63", "#8BC34A", "#FF9800", "#673AB7",
        "#009688", "#F44336", "#3F51B5", "#CDDC39", "#795548",
    ]

    for idx in selected_indices:
        if idx >= len(modes):
            continue
        mode = modes[idx]
        # Filter to station-type points for smooth curve (skip bearing_pre/bearing_jnl duplicates)
        lengths = []
        disps = []
        for st in mode.stations:
            if st["type"] in ("station", "endpoint"):
                lengths.append(st["length"])
                disps.append(st["displacement"])

        color = colors[idx % len(colors)]
        fig.add_trace(go.Scatter(
            x=lengths,
            y=disps,
            mode="lines+markers",
            name=f"Mode {mode.mode_number}: {mode.rpm:.1f} RPM",
            line=dict(color=color, width=2),
            marker=dict(size=4),
            hovertemplate=(
                "Length: %{x:.3f} in<br>"
                "Disp: %{y:.6f}<br>"
                "<extra>Mode %{fullData.name}</extra>"
            ),
        ))

    # Bearing position vertical lines
    brg_positions = set()
    for brg in rotor.bearings:
        pos = sum(s.L for s in rotor.sections[:brg.station])
        brg_positions.add((brg.index, pos))

    for brg_idx, pos in sorted(brg_positions):
        fig.add_vline(
            x=pos,
            line_dash="dash",
            line_color="rgba(255,255,255,0.4)",
            annotation_text=f"Brg {brg_idx}",
            annotation_position="top",
            annotation_font_color="rgba(255,255,255,0.7)",
        )

    # Zero line
    fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.2)")

    fig.update_layout(
        title="Mode Shape (Normalized Displacement)",
        xaxis_title="Rotor Length (in)",
        yaxis_title="Normalized Displacement",
        template="plotly_dark",
        paper_bgcolor="rgba(30,30,30,1)",
        plot_bgcolor="rgba(40,40,40,1)",
        legend=dict(
            yanchor="top", y=0.99,
            xanchor="right", x=0.99,
        ),
        margin=dict(l=60, r=20, t=50, b=50),
        height=400,
    )

    return fig


def sections_grid_data(rotor: Rotor) -> list[dict]:
    """Convert rotor sections to AG Grid row data."""
    rows = []
    for s in rotor.sections:
        rows.append({
            "#": s.index,
            "I (in⁴)": s.I,
            "W (lb)": s.W,
            "L (in)": s.L,
            "D (in)": s.D,
        })
    return rows


def bearings_grid_data(rotor: Rotor) -> list[dict]:
    """Convert rotor bearings to AG Grid row data."""
    rows = []
    for b in rotor.bearings:
        rows.append({
            "#": b.index,
            "Station": b.station,
            "KR (lb/in)": b.KR,
        })
    return rows


def results_grid_data(mode: ModeResult) -> list[dict]:
    """Convert mode stations to AG Grid row data."""
    rows = []
    for st in mode.stations:
        rows.append({
            "Section": st["section"],
            "Length": round(st["length"], 3),
            "Slope": f"{st['slope']:.6E}",
            "Displacement": f"{st['displacement']:.6f}",
            "Moment": f"{st['moment']:.6E}",
            "Shear": f"{st['shear']:.6E}",
            "Type": st["type"],
            "Reaction": f"{st['reaction']:.6E}" if st["reaction"] != 0 else "",
        })
    return rows
