"""Validation tests comparing against original ROTCO rout output."""

import os
import pytest
from rotordyn.parser import parse_rin
from rotordyn.engine import find_critical_speeds, compute_mode_shape

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
RIN_PATH = os.path.join(FIXTURES, "rin")


@pytest.fixture
def rotor():
    return parse_rin(RIN_PATH)


@pytest.fixture
def mode1(rotor):
    crits = find_critical_speeds(rotor)
    return compute_mode_shape(rotor, crits[0])


class TestInputValidation:
    def test_section_count(self, rotor):
        assert len(rotor.sections) == 173

    def test_bearing_count(self, rotor):
        assert len(rotor.bearings) == 6

    def test_total_weight(self, rotor):
        """TOTALS: 2.036503E+05 WTOT"""
        assert abs(rotor.total_weight - 2.036503e5) < 1.0

    def test_total_length(self, rotor):
        """TOTALS: 940.5660 LTOT"""
        assert abs(rotor.total_length - 940.566) < 0.001


class TestCriticalSpeeds:
    def test_mode1_rpm(self, rotor):
        """RPM = 1102.502 (18.3750 HZ)"""
        crits = find_critical_speeds(rotor)
        assert abs(crits[0] - 1102.502) < 0.1

    def test_mode2_rpm(self, rotor):
        """RPM = 1693.218 (28.2203 HZ)"""
        crits = find_critical_speeds(rotor)
        assert abs(crits[1] - 1693.218) < 0.1


class TestMode1Shape:
    """Compare Mode 1 shape against rout values."""

    # Expected values from rout (section, length, slope, disp, moment, shear)
    EXPECTED_STATIONS = [
        (0,    0.0,    -0.013706,  1.000000,  0.0,           0.0),
        (1,    3.878,  -0.013706,  0.946849,  0.0,           2.916249e4),
        (2,    9.527,  -0.013705,  0.869419,  1.647535e5,    5.826944e4),
        (3,   15.433,  -0.013701,  0.788491,  5.088637e5,    8.339849e4),
        (10,  47.942,  -0.012617,  0.355722,  3.638940e6,    1.129025e5),
        (15,  79.054,  -0.010301, -0.003130,  7.374938e6,    1.237165e5),
    ]

    def test_station_values(self, mode1):
        """Verify displacement/slope/moment/shear at key stations."""
        station_map = {}
        for st in mode1.stations:
            if st['type'] == 'station':
                station_map[st['section']] = st

        for sec, length, slope, disp, moment, shear in self.EXPECTED_STATIONS:
            st = station_map[sec]
            assert abs(st['length'] - length) < 0.01, \
                f"Station {sec}: length {st['length']:.3f} != {length:.3f}"
            assert abs(st['slope'] - slope) < 1e-5, \
                f"Station {sec}: slope {st['slope']:.6f} != {slope:.6f}"
            assert abs(st['displacement'] - disp) < 1e-4, \
                f"Station {sec}: disp {st['displacement']:.6f} != {disp:.6f}"
            if abs(moment) > 0:
                assert abs(st['moment'] - moment) / abs(moment) < 0.001, \
                    f"Station {sec}: moment {st['moment']:.4e} != {moment:.4e}"
            if abs(shear) > 0:
                assert abs(st['shear'] - shear) / abs(shear) < 0.001, \
                    f"Station {sec}: shear {st['shear']:.4e} != {shear:.4e}"

    def test_generalized_mass(self, mode1):
        """GENERALIZED MASS = 1.66017E+04"""
        assert abs(mode1.generalized_mass - 1.66017e4) / 1.66017e4 < 0.01

    def test_effective_mass(self, mode1):
        """EFF.MASS = 4.57374E+04"""
        assert abs(mode1.effective_mass - 4.57374e4) / 4.57374e4 < 0.01

    def test_bearing_reaction(self, mode1):
        """JNL 1 reaction = 3.702765E+05"""
        jnl_stations = [st for st in mode1.stations if st['type'] == 'bearing_jnl']
        assert len(jnl_stations) == 6
        jnl1 = jnl_stations[0]
        assert jnl1['bearing_idx'] == 1
        assert abs(jnl1['reaction'] - 3.702765e5) / 3.702765e5 < 0.001
