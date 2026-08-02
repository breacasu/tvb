import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

from config.config_loader import TVBConfig


class TestFormatConfigDefaults(unittest.TestCase):
    def make_config(self, content):
        file = tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False)
        file.write(content)
        file.close()
        self.addCleanup(lambda: Path(file.name).unlink(missing_ok=True))
        return TVBConfig(file.name)

    def test_empty_mode_parameters_return_empty_strings(self):
        config = self.make_config(
            "[movie]\nparameter =\n[tvshow]\nparameter =\n[custom]\nparameter =\n"
        )
        self.assertEqual(config.get_format_params("movie"), "")
        self.assertEqual(config.get_format_params("tvshow"), "")
        self.assertEqual(config.get_format_params("custom"), "")

    def test_missing_mode_does_not_inherit_default_encoding(self):
        config = self.make_config(
            "[default]\nparameter = --mode av1 --quality 30\n"
        )
        self.assertEqual(config.get_format_params("movie"), "")
        self.assertEqual(config.get_format_params("tvshow"), "")
        self.assertEqual(config.get_format_params("custom"), "")

    def test_nonempty_mode_parameter_is_preserved(self):
        config = self.make_config(
            "[movie]\nparameter = --mode hevc --quality 24\n"
        )
        self.assertEqual(config.get_format_params("movie"), "--mode hevc --quality 24")


if __name__ == "__main__":
    unittest.main(verbosity=2)
