import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Make "import lab" and "import strategies" work when running pytest from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def demo_prices():
    from lab.synthetic import make_demo_prices
    return make_demo_prices()


def make_prices(values, start="2020-01-01"):
    """Tiny helper: a price DataFrame from a list of closing prices."""
    idx = pd.bdate_range(start, periods=len(values))
    return pd.DataFrame({"Close": np.asarray(values, dtype=float)}, index=idx)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Tests must never download anything (CI has to work offline). Any attempt fails loudly."""
    import socket

    def refuse(*args, **kwargs):
        raise RuntimeError("A test tried to use the network. Use committed data, demo data or a fake.")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
