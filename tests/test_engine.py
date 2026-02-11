"""Tests for transfer matrix engine."""

import os
import math
import pytest
from rotordyn.parser import parse_rin
from rotordyn.engine import find_critical_speeds, compute_mode_shape, solve

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
RIN_PATH = os.path.join(FIXTURES, "rin")


@pytest.fixture
def rotor():
    return parse_rin(RIN_PATH)


def test_critical_speed_count(rotor):
    crits = find_critical_speeds(rotor)
    assert len(crits) == 15


def test_mode1_rpm(rotor):
    crits = find_critical_speeds(rotor)
    assert abs(crits[0] - 1102.502) < 0.1


def test_mode2_rpm(rotor):
    crits = find_critical_speeds(rotor)
    assert abs(crits[1] - 1693.218) < 0.1


def test_mode1_shape(rotor):
    crits = find_critical_speeds(rotor)
    mode = compute_mode_shape(rotor, crits[0])

    # Check station 0
    st0 = mode.stations[0]
    assert st0['section'] == 0
    assert abs(st0['displacement'] - 1.0) < 1e-6
    assert abs(st0['moment']) < 1e-6
    assert abs(st0['shear']) < 1e-6

    # Check station 1
    st1 = mode.stations[1]
    assert abs(st1['slope'] - (-0.013706)) < 1e-5
    assert abs(st1['displacement'] - 0.946849) < 1e-4
    assert abs(st1['length'] - 3.878) < 0.01


def test_mode1_generalized_mass(rotor):
    crits = find_critical_speeds(rotor)
    mode = compute_mode_shape(rotor, crits[0])
    # Expected: 1.66017E+04
    assert abs(mode.generalized_mass - 1.66017e4) / 1.66017e4 < 0.001


def test_mode1_effective_mass(rotor):
    crits = find_critical_speeds(rotor)
    mode = compute_mode_shape(rotor, crits[0])
    # Expected: 4.57374E+04
    assert abs(mode.effective_mass - 4.57374e4) / 4.57374e4 < 0.001


def test_solve_returns_modes(rotor):
    modes = solve(rotor)
    assert len(modes) == 15
    assert modes[0].mode_number == 1
    assert modes[14].mode_number == 15
