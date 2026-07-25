"""Entry point so `python -m cimf` works (README quickstart previously failed:
the demo lived in __init__.py where it could not be executed as a module)."""

import json
import logging

from cimf import HPMv5


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    hpm = HPMv5()
    for i in range(3):
        report = hpm.run_cycle(write_data=f"Cosmic observation epoch {i+1}".encode())
        print(f"Cycle {report['cycle']}: Phi={report.get('phi', 0.0):.4f}  R={report['r_value']:.4f}")
    print("\nFull system status:")
    print(json.dumps(hpm.status(), indent=2, default=str))


if __name__ == "__main__":
    main()
