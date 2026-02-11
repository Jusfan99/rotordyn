"""Transfer matrix engine for lateral vibration analysis.

Implements the Myklestad-Prohl transfer matrix method (midpoint mass variant)
for undamped critical speed calculation of rotor-bearing systems.

Each shaft section is split into two half-segments with the lumped mass
concentrated at the midpoint:
  1. Field matrix for L/2
  2. Point mass W at midpoint
  3. Field matrix for L/2
  4. Bearing spring at section end (if present)
"""

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import brentq

from .config import G_ACCEL
from .models import Rotor


@dataclass
class ModeResult:
    """Results for a single critical speed mode."""
    mode_number: int
    rpm: float
    hz: float
    det: float
    # Per-station results
    stations: list[dict] = field(default_factory=list)
    generalized_mass: float = 0.0
    effective_mass: float = 0.0
    max_disp_length: float = 0.0


def _build_bearing_map(rotor: Rotor) -> dict[int, float]:
    """Map station number -> bearing stiffness."""
    return {b.station: b.KR for b in rotor.bearings}


def _field_matrix(L: float, EI: float) -> np.ndarray:
    """Field (beam segment) transfer matrix for state [y, theta, M, V]."""
    L2 = L * L
    L3 = L2 * L
    return np.array([
        [1.0,  L,    L2 / (2.0 * EI),  L3 / (6.0 * EI)],
        [0.0,  1.0,  L / EI,            L2 / (2.0 * EI)],
        [0.0,  0.0,  1.0,               L],
        [0.0,  0.0,  0.0,               1.0],
    ])


def _compute_overall_transfer(rotor: Rotor, omega: float) -> np.ndarray:
    """Compute the overall 4x4 transfer matrix U at given omega.

    Uses midpoint mass method: each section is split into two half-segments
    with the full section mass at the midpoint.
    """
    E = rotor.options.youngs_mod
    omega2 = omega * omega
    brg_map = _build_bearing_map(rotor)

    U = np.eye(4)

    for sec in rotor.sections:
        EI = E * sec.I
        half_L = sec.L / 2.0
        m_omega2 = (sec.W / G_ACCEL) * omega2

        # First half of section
        U = _field_matrix(half_L, EI) @ U

        # Point mass at midpoint
        P = np.eye(4)
        P[3, 0] = m_omega2
        U = P @ U

        # Second half of section
        U = _field_matrix(half_L, EI) @ U

        # Bearing at section end
        if sec.index in brg_map:
            B = np.eye(4)
            B[3, 0] = -brg_map[sec.index]
            U = B @ U

    return U


def _determinant(rotor: Rotor, omega: float) -> float:
    """Boundary condition determinant for free-free rotor.

    Left BC: M=0, V=0 -> state = [y0, theta0, 0, 0]
    Right BC: M=0, V=0 -> U20*y0 + U21*theta0 = 0, U30*y0 + U31*theta0 = 0
    det = U20*U31 - U21*U30 = 0 at critical speeds.
    """
    U = _compute_overall_transfer(rotor, omega)
    return U[2, 0] * U[3, 1] - U[2, 1] * U[3, 0]


def find_critical_speeds(rotor: Rotor) -> list[float]:
    """Find critical speeds by sweeping RPM and refining zero crossings."""
    rpm_min = rotor.options.rpm_min
    rpm_max = rotor.options.rpm_max
    rpm_incr = rotor.options.rpm_incr
    n_crits = rotor.options.n_crits

    if rpm_min < rpm_incr:
        rpm_min = rpm_incr

    def det_at_rpm(rpm):
        omega = rpm * 2.0 * math.pi / 60.0
        return _determinant(rotor, omega)

    crits: list[float] = []
    rpm_prev = rpm_min
    det_prev = det_at_rpm(rpm_prev)

    rpm = rpm_min + rpm_incr
    while rpm <= rpm_max and len(crits) < n_crits:
        det_cur = det_at_rpm(rpm)

        if det_prev * det_cur < 0:
            try:
                rpm_root = brentq(det_at_rpm, rpm_prev, rpm, rtol=1e-10)
                crits.append(rpm_root)
            except ValueError:
                pass

        rpm_prev = rpm
        det_prev = det_cur
        rpm += rpm_incr

    return crits


def compute_mode_shape(rotor: Rotor, rpm: float) -> ModeResult:
    """Compute mode shape at a given critical speed.

    Propagates state through all stations using midpoint mass method,
    normalizes by max displacement, and computes generalized/effective mass.
    """
    E = rotor.options.youngs_mod
    omega = rpm * 2.0 * math.pi / 60.0
    omega2 = omega * omega
    hz = rpm / 60.0
    brg_map = _build_bearing_map(rotor)

    # Compute overall transfer matrix for initial conditions
    U = _compute_overall_transfer(rotor, omega)
    det_val = U[2, 0] * U[3, 1] - U[2, 1] * U[3, 0]

    # Initial conditions: M=0, V=0, y0=1, theta0 from BC
    y0 = 1.0
    if abs(U[2, 1]) > 1e-30:
        theta0 = -U[2, 0] / U[2, 1] * y0
    else:
        theta0 = -U[3, 0] / U[3, 1] * y0

    state = np.array([y0, theta0, 0.0, 0.0])

    stations = []
    # Station 0 (left end)
    stations.append({
        'section': 0,
        'length': 0.0,
        'slope': state[1],
        'displacement': state[0],
        'moment': state[2],
        'shear': state[3],
        'type': 'station',  # 'station', 'bearing_pre', 'bearing_jnl'
        'bearing_idx': 0,
        'reaction': 0.0,
    })

    cumulative_length = 0.0

    for sec in rotor.sections:
        EI = E * sec.I
        half_L = sec.L / 2.0
        m_omega2 = (sec.W / G_ACCEL) * omega2
        station = sec.index

        # First half of section
        state = _field_matrix(half_L, EI) @ state
        cumulative_length += half_L

        # Point mass at midpoint
        P = np.eye(4)
        P[3, 0] = m_omega2
        state = P @ state

        # Record state at midpoint (this is the main station output)
        stations.append({
            'section': sec.index,
            'length': cumulative_length,
            'slope': state[1],
            'displacement': state[0],
            'moment': state[2],
            'shear': state[3],
            'type': 'station',
            'bearing_idx': 0,
            'reaction': 0.0,
        })

        # Second half of section
        state = _field_matrix(half_L, EI) @ state
        cumulative_length += half_L

        # Bearing at section end, or last section endpoint
        is_last = (sec.index == len(rotor.sections))
        if station in brg_map:
            # Record state at section end (before bearing)
            stations.append({
                'section': sec.index,
                'length': cumulative_length,
                'slope': state[1],
                'displacement': state[0],
                'moment': state[2],
                'shear': state[3],
                'type': 'bearing_pre',
                'bearing_idx': 0,
                'reaction': 0.0,
            })

            # Apply bearing spring
            K = brg_map[station]
            shear_before = state[3]
            B = np.eye(4)
            B[3, 0] = -K
            state = B @ state
            reaction = state[3] - shear_before

            # Record JNL line
            brg_idx = next(b.index for b in rotor.bearings if b.station == station)
            stations.append({
                'section': sec.index,
                'length': cumulative_length,
                'slope': state[1],
                'displacement': state[0],
                'moment': state[2],
                'shear': state[3],
                'type': 'bearing_jnl',
                'bearing_idx': brg_idx,
                'reaction': reaction,
            })
        elif is_last:
            # Last section: also record endpoint (right end of rotor)
            stations.append({
                'section': sec.index,
                'length': cumulative_length,
                'slope': state[1],
                'displacement': state[0],
                'moment': state[2],
                'shear': state[3],
                'type': 'endpoint',
                'bearing_idx': 0,
                'reaction': 0.0,
            })

    # Find max displacement for normalization
    max_disp = 0.0
    max_disp_idx = 0
    for i, st in enumerate(stations):
        if abs(st['displacement']) > abs(max_disp):
            max_disp = st['displacement']
            max_disp_idx = i

    # Normalize
    if abs(max_disp) > 0:
        norm = max_disp
        for st in stations:
            st['slope'] /= norm
            st['displacement'] /= norm
            st['moment'] /= norm
            st['shear'] /= norm
            st['reaction'] /= norm

    # Generalized and effective mass
    # Use midpoint displacements (type='station', section > 0)
    gen_mass = 0.0
    eff_mass_num = 0.0
    for st in stations:
        if st['type'] != 'station' or st['section'] == 0:
            continue
        sec = rotor.sections[st['section'] - 1]
        y_i = st['displacement']
        gen_mass += sec.W * y_i * y_i
        eff_mass_num += sec.W * y_i

    eff_mass = (eff_mass_num ** 2) / gen_mass if gen_mass != 0 else 0.0

    return ModeResult(
        mode_number=0,
        rpm=rpm,
        hz=hz,
        det=det_val,
        stations=stations,
        generalized_mass=gen_mass,
        effective_mass=eff_mass,
        max_disp_length=stations[max_disp_idx]['length'],
    )


def solve(rotor: Rotor) -> list[ModeResult]:
    """Full solve: find critical speeds and compute mode shapes."""
    crits = find_critical_speeds(rotor)
    modes = []
    for i, rpm in enumerate(crits):
        mode = compute_mode_shape(rotor, rpm)
        mode.mode_number = i + 1
        modes.append(mode)
    return modes
