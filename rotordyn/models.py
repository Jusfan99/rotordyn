"""Data models for rotor dynamics."""

from dataclasses import dataclass, field


@dataclass
class ShaftSection:
    """A single shaft section (element)."""
    index: int       # 1-based section number
    I: float         # Area moment of inertia (in⁴)
    W: float         # Weight (lb)
    L: float         # Length (in)
    D: float         # Diameter (in)


@dataclass
class Bearing:
    """A bearing support."""
    index: int       # 1-based bearing number
    station: int     # Station number (end of preceding shaft section)
    W_brg: float     # Bearing weight (lb), usually 0
    KR: float        # Stiffness (lb/in)


@dataclass
class RotorOptions:
    """Calculation options parsed from input file."""
    damp_flag: int        # -1=no damping, +1=damped
    rflex_flag: int       # +1=include rotational flexibility
    stat_flag: int        # -1=no static
    rpm_min: float        # Starting RPM
    rpm_max: float        # Maximum RPM
    rpm_incr: float       # RPM increment for sweep
    damp_incr: float      # Damping increment
    n_crits: int          # Number of critical speeds to find
    global_damping: float # Global damping value
    youngs_mod: float     # Young's modulus (psi)


@dataclass
class Rotor:
    """Complete rotor model."""
    title: str
    description: str
    options: RotorOptions
    sections: list[ShaftSection] = field(default_factory=list)
    bearings: list[Bearing] = field(default_factory=list)

    @property
    def total_weight(self) -> float:
        return sum(s.W for s in self.sections)

    @property
    def total_length(self) -> float:
        return sum(s.L for s in self.sections)

    @property
    def n_stations(self) -> int:
        """Number of stations = number of sections (station 0 is left end)."""
        return len(self.sections)
