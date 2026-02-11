"""Output formatter matching ROTCO rout format."""

from io import StringIO

from .models import Rotor
from .engine import ModeResult


def _fmt_exp(val: float, width: int = 14) -> str:
    """Format a value in Fortran-style exponential notation."""
    if val == 0.0:
        return f"{'0.000000E+00':>{width}}"
    s = f"{val:.6E}"
    return f"{s:>{width}}"


def _fmt_disp(val: float) -> str:
    """Format displacement value (leading space for positive, no leading zero)."""
    if abs(val) >= 1.0:
        return f"{val:12.6f}"
    # Fortran style: no leading zero for |val| < 1
    if val >= 0:
        return f"    {val:8.6f}"
    else:
        return f"   {val:9.6f}"


def _fmt_slope(val: float) -> str:
    """Format slope value."""
    if abs(val) >= 1.0:
        return f"{val:12.6f}"
    if val >= 0:
        return f"    {val:8.6f}"
    else:
        return f"   {val:9.6f}"


def format_input_echo(rotor: Rotor) -> str:
    """Format the input data echo section."""
    out = StringIO()
    page = 1

    def page_header():
        nonlocal page
        if page > 1:
            out.write("1\n")
        out.write(f"0    INPUT DATA       *    {rotor.title:<60s}   PAGE {page:2d}\n")
        out.write("\n")
        page += 1

    # First page header
    out.write("1\n")
    out.write(f" CRITICAL SPEED INPUT DATA  *    {rotor.title:<60s}   PAGE  1\n")
    out.write(f"                                {rotor.description}\n")
    out.write("+\n")
    out.write("\n")

    # Options line
    opts = rotor.options
    out.write("     OPTIONS        FREQS(RPM)        DAMP    R-FLX\n")
    out.write(" DAMP  R-FLX STAT  INITIAL   FINAL    INCR.   INCR.   CRITS\n")
    out.write(f"  {opts.damp_flag:2d}     {opts.rflex_flag:1d}    {opts.stat_flag:2d}"
              f"      {opts.rpm_min:.3f} {opts.rpm_max:.3f}   {opts.rpm_incr:.2f}"
              f"    {opts.damp_incr:.2f}   {opts.n_crits:.0f}."
              f"     {opts.youngs_mod:.2E}\n")

    # Section and bearing data
    brg_stations = {b.station: b for b in rotor.bearings}
    line_count = 0
    lines_per_page = 30

    for sec in rotor.sections:
        if line_count >= lines_per_page:
            page_header()
            line_count = 0

        prefix = "0" if sec.index == 1 or (sec.index > 1 and rotor.sections[sec.index - 2].index in brg_stations) else " "
        out.write(f"{prefix}         {sec.index:4d}   {sec.I:.6E} I"
                  f"     {sec.W:.6E} W"
                  f"      {sec.L:7.4f}    L"
                  f"                                               {sec.D:.3f}\n")
        line_count += 1

        if sec.index in brg_stations:
            brg = brg_stations[sec.index]
            out.write(f"         \n")
            out.write(f"      BRG  {brg.index:2d}   {brg.W_brg:.6E} WBR"
                      f"   {brg.KR:.6E} KR\n")
            line_count += 2

    return out.getvalue()


def format_totals(rotor: Rotor) -> str:
    """Format the TOTALS line."""
    total_w = rotor.total_weight
    total_l = rotor.total_length

    # Compute total I about left end and CG
    # I_total(0) = sum(I_i * L_i) integrated over length
    # For output purposes, compute total static moment for CG
    cumL = 0.0
    moment_sum = 0.0
    I_total_0 = 0.0
    for sec in rotor.sections:
        mid = cumL + sec.L / 2.0
        moment_sum += sec.W * mid
        I_total_0 += sec.W * mid * mid
        cumL += sec.L

    cg = moment_sum / total_w if total_w > 0 else 0.0
    I_total_cg = I_total_0 - total_w * cg * cg

    out = StringIO()
    out.write(f"  TOTALS - - - - - - - - - - - -   {total_w:.6E} WTOT"
              f"  {total_l:.4f}  LTOT"
              f"                                            {I_total_0:.4E} IT(0)\n")
    out.write(f"                                                      "
              f" {cg:.3f}  C.G."
              f"                                            {I_total_cg:.4E} IT(C.G.)\n")
    return out.getvalue()


def format_mode(mode: ModeResult, rotor: Rotor) -> str:
    """Format a single mode result."""
    out = StringIO()

    # Mode header
    out.write(f"          MODE {mode.mode_number:2d}"
              f"                        MODE SHAPE"
              f"            MAX DISP = 1.0 AT {mode.max_disp_length:8.3f}\n")
    out.write(f"          RPM = {mode.rpm:9.3f}    ({mode.hz:8.4f} HZ)"
              f"                              DET= {mode.det:13.5E}\n")

    # Column headers
    out.write("0     SECT NO      LENGTH        SLOPE      DISPLACEMENT"
              "     MOMENT         SHEAR         REACTION OR\n")
    out.write("                                                        "
              "                                  HINGE ANGLE\n")

    # Station data
    for st in mode.stations:
        sec_no = st['section']
        length = st['length']
        slope = st['slope']
        disp = st['displacement']
        moment = st['moment']
        shear = st['shear']

        if st['type'] == 'bearing_jnl':
            # JNL line
            brg_idx = st['bearing_idx']
            reaction = st['reaction']
            out.write(f"       JNL {brg_idx:2d}"
                      f"                  {_fmt_slope(slope)}"
                      f"  {_fmt_disp(disp)}"
                      f"  {_fmt_exp(moment)}"
                      f"  {_fmt_exp(shear)}"
                      f"  {_fmt_exp(reaction)}\n")
        else:
            out.write(f"         {sec_no:4d}"
                      f"  {length:10.3f}"
                      f"    {_fmt_slope(slope)}"
                      f"  {_fmt_disp(disp)}"
                      f"  {_fmt_exp(moment)}"
                      f"  {_fmt_exp(shear)}\n")

    # Generalized and effective mass
    out.write("                                                        "
              "                                    EFF.MASS=\n")
    out.write(f"                    GENERALIZED MASS = {mode.generalized_mass:.5E}"
              f"                                                {mode.effective_mass:.5E}\n")

    return out.getvalue()


def format_output(rotor: Rotor, modes: list[ModeResult]) -> str:
    """Format the complete output matching rout format."""
    out = StringIO()

    # Title pages (simplified)
    for _ in range(4):
        out.write(f"0ROTCO           {rotor.title}\n")
        out.write(f"                {rotor.description}\n")
        out.write("0\n0\n0\n\n")

    # Input echo
    out.write(format_input_echo(rotor))

    # Totals
    out.write(format_totals(rotor))
    out.write("\n")

    # Mode results
    for mode in modes:
        out.write(f"0 RIGID CALCULATIONS  *    {rotor.title}\n\n")
        out.write(format_mode(mode, rotor))
        out.write("\n")

    return out.getvalue()
