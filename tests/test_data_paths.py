import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

from data_paths import resolve_data_dir


class TestDataPaths(unittest.TestCase):
    def test_explicit_data_directory_wins(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"TVB_DATA_DIR": directory}):
                self.assertEqual(resolve_data_dir(), Path(directory))


if __name__ == "__main__":
    unittest.main(verbosity=2)
