"""Parser for ROTCO rin input files."""

from .config import E_DEFAULT
from .models import Bearing, Rotor, RotorOptions, ShaftSection


def parse_rin(path: str) -> Rotor:
    """Parse a rin input file and return a Rotor model.

    File format:
      Line 1: title (cols 1-70), flags at right
      Line 2: description (cols 1-70), termination code at right
      Line 3: 10 space-separated option values
      Remaining lines:
        - Section data: I  W  L  [gap]  D  (D at ~col 58+)
        - Bearing data: 0.0  KR  (two values, first is 0.0)
        - End marker: last section line has '1' after D field
    """
    with open(path) as f:
        lines = f.readlines()

    # Line 1: title
    title = lines[0][:70].strip()

    # Line 2: description
    description = lines[1][:70].strip()

    # Line 3: options
    opts_line = lines[2].strip()
    opts_parts = opts_line.split()
    # Last value may be -1 (use default E) or a positive value (custom E)
    damp_flag = int(float(opts_parts[0]))
    rflex_flag = int(float(opts_parts[1]))
    stat_flag = int(float(opts_parts[2]))
    rpm_min = float(opts_parts[3])
    rpm_max = float(opts_parts[4])
    rpm_incr = float(opts_parts[5])
    damp_incr = float(opts_parts[6])
    n_crits = int(float(opts_parts[7]))
    global_damping = float(opts_parts[8])
    youngs_raw = float(opts_parts[9])
    youngs_mod = E_DEFAULT if youngs_raw < 0 else youngs_raw

    options = RotorOptions(
        damp_flag=damp_flag,
        rflex_flag=rflex_flag,
        stat_flag=stat_flag,
        rpm_min=rpm_min,
        rpm_max=rpm_max,
        rpm_incr=rpm_incr,
        damp_incr=damp_incr,
        n_crits=n_crits,
        global_damping=global_damping,
        youngs_mod=youngs_mod,
    )

    sections: list[ShaftSection] = []
    bearings: list[Bearing] = []
    section_idx = 0
    bearing_idx = 0

    for line in lines[3:]:
        stripped = line.strip()
        if not stripped:
            continue

        parts = stripped.split()
        if not parts:
            continue

        first_val = float(parts[0])

        if first_val == 0.0 and len(parts) == 2:
            # Bearing line: 0.0  KR
            bearing_idx += 1
            bearings.append(Bearing(
                index=bearing_idx,
                station=section_idx,
                W_brg=0.0,
                KR=float(parts[1]),
            ))
        elif first_val > 0:
            # Shaft section line: I  W  L  [gap]  D  [end_marker]
            # D is always the 4th token (index 3).
            # The last line may have an extra '1' end marker as 5th token.
            section_idx += 1
            I_val = float(parts[0])
            W_val = float(parts[1])
            L_val = float(parts[2])
            D_val = float(parts[3])
            sections.append(ShaftSection(
                index=section_idx,
                I=I_val,
                W=W_val,
                L=L_val,
                D=D_val,
            ))

    return Rotor(
        title=title,
        description=description,
        options=options,
        sections=sections,
        bearings=bearings,
    )
