"""CLI entry point: python -m rotordyn <input_file> [output_file]"""

import sys
import time

from .parser import parse_rin
from .engine import solve
from .formatter import format_output
from .ascii_plot import generate_ascii_plot


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m rotordyn <input_file> [output_file]", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    # Parse input
    print(f"Reading input: {input_path}")
    rotor = parse_rin(input_path)
    print(f"  {len(rotor.sections)} sections, {len(rotor.bearings)} bearings")
    print(f"  Total weight: {rotor.total_weight:.1f} lb")
    print(f"  Total length: {rotor.total_length:.4f} in")

    # Solve
    print(f"\nSolving for up to {rotor.options.n_crits} critical speeds...")
    print(f"  RPM range: {rotor.options.rpm_min:.0f} - {rotor.options.rpm_max:.0f},"
          f" increment: {rotor.options.rpm_incr:.1f}")

    t0 = time.time()
    modes = solve(rotor)
    elapsed = time.time() - t0

    print(f"  Found {len(modes)} critical speeds in {elapsed:.2f}s:")
    for m in modes:
        print(f"    Mode {m.mode_number:2d}: {m.rpm:10.3f} RPM  ({m.hz:8.4f} Hz)")

    # Format output
    output = format_output(rotor, modes)

    # Append ASCII plots
    for m in modes:
        plot = generate_ascii_plot(m, rotor.total_length)
        output += f"\n{plot}\n"
        output += f"                                   MODE SHAPE"
        output += f"          RPM= {m.rpm:9.3f}  ({m.hz:8.4f} HZ)\n"

    if output_path:
        with open(output_path, 'w') as f:
            f.write(output)
        print(f"\nOutput written to: {output_path}")
    else:
        print("\n" + "=" * 80)
        print(output)


if __name__ == "__main__":
    main()
