"""Write the A2 software-verification fixture; the builder lives with the Lab tests."""
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parents[1] / 'labs/binding-pockets'
sys.path.insert(0, str(LAB / 'tests'))
from mapping_fixture import build  # noqa: E402

if __name__ == '__main__':
    target = LAB / 'fixtures/mapping-edge.cif'
    target.write_text(build())
    print(target, target.stat().st_size)
