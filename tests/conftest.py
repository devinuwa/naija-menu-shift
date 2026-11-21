import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def demo():
    from menushift.engine import load_dataset
    return load_dataset(ROOT / "data" / "demo", demo=True)
