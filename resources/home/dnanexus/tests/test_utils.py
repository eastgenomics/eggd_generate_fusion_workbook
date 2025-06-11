"""
Tests for utils.py module
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from utils.utils import (
    create_pivot_table,
    generate_varsome_url,
    get_dxfile,
    get_project_info,
    read_dxfile,
    validate_config,
)


class TestReadDxFile:
    """Tests for reading DNAnexus files using read_dxfile"""

    def setup_method(self):
        self.mock_dxfile = MagicMock()
        self.mock_dxfile.name = "test_file.txt"
        self.test_data = pd.DataFrame({"col1": ["a", "b"], "col2": [1, 2]})

    def test_read_dxfile_with_filename(self):
        """Adds dummy row and file_name column when include_fname=True"""
        with patch("pandas.read_csv", return_value=self.test_data):
            result = read_dxfile(self.mock_dxfile, include_fname=True)

            # Check that file_name column was added
            assert "file_name" in result.columns
            assert result["file_name"].iloc[0] == "test_file.txt"

            # Check that dummy row was added (should have 3 rows total)
            assert len(result) == 3

            # Check that first row is the dummy row with filename and NAs
            assert result.iloc[0]["file_name"] == "test_file.txt"
            assert pd.isna(result.iloc[0]["col1"])
            assert pd.isna(result.iloc[0]["col2"])

    def test_read_dxfile_without_filename(self):
        """Returns unmodified DataFrame when include_fname=False"""
        with patch("pandas.read_csv", return_value=self.test_data):
            result = read_dxfile(self.mock_dxfile, include_fname=False)

            assert "file_name" not in result.columns
            pd.testing.assert_frame_equal(result, self.test_data)


class TestCreatePivotTable:
    """Tests for pivot table generation"""

    def test_valid_pivot_table(self):
        df = pd.DataFrame(
            {
                "Sample": ["A", "A", "B"],
                "Type": ["X", "Y", "X"],
                "Count": [1, 2, 3],
            }
        )

        config = {
            "index": ["Sample"],
            "columns": ["Type"],
            "values": ["Count"],
            "aggfunc": "sum",
            "add_total_row": False,
        }

        pivot = create_pivot_table(df, config)
        assert pivot.loc["A", ("Count", "X")] == 1
        assert pivot.loc["B", ("Count", "X")] == 3


class TestProjectUtils:
    """Tests for DNAnexus project info and file selection"""

    @patch("dxpy.describe")
    @patch("os.environ.get")
    def test_get_project_info(self, mock_env_get, mock_describe):
        mock_env_get.return_value = "project-1234"
        mock_describe.return_value = {"name": "002_test_project"}

        name, proj_id = get_project_info()
        assert name == "test_project"
        assert proj_id == "project-1234"
        mock_describe.assert_called_once_with("project-1234")

    def test_get_dxfile_success(self):
        file1 = MagicMock()
        file1.name = "file1.txt"
        file2 = MagicMock()
        file2.name = "target.txt"

        result = get_dxfile([file1, file2], "target.txt")
        assert result.name == "target.txt"

    def test_get_dxfile_not_found(self):
        file1 = MagicMock()
        file1.name = "file1.txt"
        with pytest.raises(ValueError, match="not found"):
            get_dxfile([file1], "nonexistent.txt")


class TestConfigValidation:
    """Tests for validating configuration dicts"""

    def test_validate_config_success(self):
        config = {"a": 1, "b": 2}
        expected_keys = ["a", "b"]
        validate_config(config, expected_keys)  # should not raise

    def test_validate_config_missing(self):
        config = {"a": 1}
        expected_keys = ["a", "b"]
        with pytest.raises(ValueError, match="Missing required config key"):
            validate_config(config, expected_keys)


class TestVarsomeURL:
    """Tests for generating Varsome URLs"""

    @pytest.mark.parametrize(
        "bp, expected_url",
        [
            ("chr15:39594440:+", "https://varsome.com/position/hg38/chr15%3A39594440"),
            ("chrX:12345678:-", "https://varsome.com/position/hg38/chrX%3A12345678"),
            ("chr1:123456:+", "https://varsome.com/position/hg38/chr1%3A123456"),
            ("invalid", "https://varsome.com/position/hg38/invalid"),
        ],
    )
    def test_generate_varsome_url(self, bp, expected_url):
        url = generate_varsome_url(bp)
        assert url == expected_url
