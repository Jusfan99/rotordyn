"""Tests for rin file parser."""

import os
import pytest
from rotordyn.parser import parse_rin

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
RIN_PATH = os.path.join(FIXTURES, "rin")


def test_parse_section_count():
    rotor = parse_rin(RIN_PATH)
    assert len(rotor.sections) == 173


def test_parse_bearing_count():
    rotor = parse_rin(RIN_PATH)
    assert len(rotor.bearings) == 6


def test_total_weight():
    rotor = parse_rin(RIN_PATH)
    assert abs(rotor.total_weight - 203650.3) < 1.0


def test_total_length():
    rotor = parse_rin(RIN_PATH)
    assert abs(rotor.total_length - 940.566) < 0.001


def test_bearing_stations():
    rotor = parse_rin(RIN_PATH)
    stations = [b.station for b in rotor.bearings]
    assert stations == [15, 40, 52, 114, 123, 170]


def test_bearing_stiffness():
    rotor = parse_rin(RIN_PATH)
    expected_KR = [8.33e6, 8.33e6, 3.92e6, 2.50e6, 6.88e6, 5.53e6]
    for brg, kr in zip(rotor.bearings, expected_KR):
        assert abs(brg.KR - kr) < 1e3


def test_options():
    rotor = parse_rin(RIN_PATH)
    opts = rotor.options
    assert opts.damp_flag == -1
    assert opts.rflex_flag == 1
    assert opts.stat_flag == -1
    assert opts.rpm_min == 0.0
    assert opts.rpm_max == 90000.0
    assert opts.rpm_incr == 50.0
    assert opts.n_crits == 15
    assert opts.youngs_mod == 29.0e6


def test_first_section():
    rotor = parse_rin(RIN_PATH)
    s = rotor.sections[0]
    assert s.index == 1
    assert abs(s.I - 3.58e4) < 1.0
    assert abs(s.W - 892.1) < 0.1
    assert abs(s.L - 7.756) < 0.001
    assert abs(s.D - 31.024) < 0.001


def test_last_section():
    rotor = parse_rin(RIN_PATH)
    s = rotor.sections[-1]
    assert s.index == 173
    assert abs(s.I - 2.80e3) < 1.0
    assert abs(s.W - 154.4) < 0.1
    assert abs(s.L - 2.913) < 0.001
    assert abs(s.D - 15.461) < 0.001
