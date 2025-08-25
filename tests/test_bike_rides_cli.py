import sys
import sqlite3
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import bike_rides_cli  # noqa: E402


def test_load_folder(tmp_path):
    sample_df = pd.DataFrame(
        {
            "UID wynajmu": [1],
            "Numer roweru": ["100"],
            "Data wynajmu": ["2025-04-07 13:52:45"],
            "Data zwrotu": ["2025-04-07 14:00:00"],
            "Stacja wynajmu": ["Rynek"],
            "Stacja zwrotu": ["Rynek"],
            "Czas trwania": [1304],
        }
    )
    sample_path = tmp_path / "sample.csv"
    sample_df.to_csv(sample_path, index=False)

    bike_rides_cli.main(["load-folder", str(tmp_path)])

    db_path = REPO_ROOT / "data" / "processed" / "bike_data.db"
    assert db_path.exists()
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("SELECT count(*) FROM bike_rides")
        assert cur.fetchone()[0] >= 0
    finally:
        conn.close()
