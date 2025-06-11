"""
Tests for parser.py module
"""
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from utils import parser


class TestParsingHelpers:
    """Unit tests for low-level parsing helper functions."""

    def test_parse_specimen_id(self):
        """Should correctly extract SP ID from sample name."""
        sample = "12345678-2XXXXSXXX-25PCAN4-10011_S33_L001_R1"
        assert parser.parse_specimen_id(sample) == "2XXXXSXXX"

    def test_parse_igv_specimen_name(self):
        """Should correctly extract IGV format SP name."""
        sample = "12345678-2XXXXSXXX-25PCAN4-10011_S33_L001_R1"
        assert parser.parse_igv_specimen_name(sample) == "12345678-2XXXXSXXX-25PCAN4"

    def test_extract_fusions_valid_cases(self):
        """Should identify valid fusion gene pairs and normalize to -- format."""
        text = "EML4::ALK, TPM3 - ROS1, EWSR1::SMAD3-rearranged"
        expected = {"EML4--ALK", "TPM3--ROS1", "EWSR1--SMAD3-rearranged"}
        result = set(parser.extract_fusions(text))
        assert expected.issubset(result)

    def test_extract_fusions_ignores_transcripts(self):
        """Should ignore transcript IDs like NM_ or ENST."""
        text = "ALK--NM_123456, ENST00005::ROS1"
        result = parser.extract_fusions(text)
        assert result == []


class TestFastQC:
    """Unit tests for parsing and processing FastQC data."""

    @pytest.fixture
    def mock_dxfile(self):
        return MagicMock()

    @pytest.fixture
    def example_fastqc_df(self):
        return pd.DataFrame({
            "Sample": ["S1"],
            "total_deduplicated_percentage": [75.0],
            "Total Sequences": [1_000_000],
        })

    def test_parse_fastqc(self, mock_dxfile, example_fastqc_df):
        """Should compute unique and duplicate reads and format output."""
        with patch("utils.parser.read_dxfile", return_value=example_fastqc_df):
            df = parser.parse_fastqc(mock_dxfile)
            assert df["Unique Reads"][0] == 750000
            assert df["Duplicate Reads"][0] == 250000
            assert df["Unique Reads(M)"][0] == 0.75
            assert df.columns.tolist() == [
                "Sample", "Unique Reads", "Duplicate Reads", "Unique Reads(M)", "Duplicate Reads(M)"
            ]

    def test_parse_fastqc_raises_for_missing_cols(self, mock_dxfile):
        """Should raise ValueError if required columns are missing."""
        bad_df = pd.DataFrame({"Sample": ["S1"]})
        with patch("utils.parser.read_dxfile", return_value=bad_df):
            with pytest.raises(ValueError):
                parser.parse_fastqc(mock_dxfile)

    def test_make_fastqc_pivot(self):
        """Should create pivot table using sample data."""
        df = pd.DataFrame({
            "Sample": ["123-2XXXXSXXX-ABC"],
            "Unique Reads": [100],
        })
        pivot_config = {
            "index": ["SPECIMEN"],
            "columns": None,
            "values": ["Unique Reads"],
            "aggfunc": "sum"
        }
        pivot_df = parser.make_fastqc_pivot(df, pivot_config)
        assert "SPECIMEN" in pivot_df.columns or pivot_df.index.name == "SPECIMEN"
        assert pivot_df["Unique Reads"].iloc[0] == 100


class TestParseFusion:
    """Unit tests for parsing STAR-Fusion and related files."""

    @pytest.fixture
    def mock_dxfile(self):
        return MagicMock()

    def test_parse_sf_previous(self, mock_dxfile):
        """Should select, deduplicate, and sort fusion name data."""
        df = pd.DataFrame({
            "#FusionName": ["A--B", "A--B", "C--D"],
            "Count_predicted": [1, 1, 2],
        })
        with patch("utils.parser.read_dxfile", return_value=df):
            result = parser.parse_sf_previous(mock_dxfile)
            assert list(result["#FusionName"]) == ["A--B", "C--D"]

    def test_parse_prev_pos(self, mock_dxfile):
        """Should parse previous positive results with fusions extracted."""
        df = pd.DataFrame({
            "Specimen Identifier": ["SP1", "SP2"],
            "Test Result": ["ALK--ROS1", "TPM3::NTRK1"],
        })
        with patch("utils.parser.read_dxfile", return_value=df):
            result = parser.parse_prev_pos(mock_dxfile)
            assert "#FusionName" in result.columns
            assert isinstance(result["#FusionName"].iloc[0], list)

    def test_parse_star_fusion_empty(self):
        """Should return empty DataFrame if no input files."""
        result = parser.parse_star_fusion([])
        assert result.empty

    def test_parse_fusion_inspector(self, mock_dxfile):
        """Should parse fusion inspector and adjust file name column."""
        df = pd.DataFrame({
            "file_name": ["12345678-S1"],
            "JunctionReadCount": [10],
            "SpanningFragCount": [5],
        })
        with patch("utils.parser.read_dxfile", return_value=df):
            result = parser.parse_fusion_inspector([mock_dxfile])
            assert result["file_name"].iloc[0].endswith("FusionInspector.fusions.abridged.merged.tsv")
            

class TestMakeSfPivot:
    """Unit tests for final pivot table from multiple data sources."""

    @classmethod
    def setup_class(cls):
        """Initialize shared test data for all test cases."""
        cls.sf_df = pd.DataFrame({
            "#FusionName": ["A--B"],
            "LeftBreakpoint": ["chr1:123"],
            "RightBreakpoint": ["chr2:456"],
            "file_name": ["123-2XX-ABC"],
            "JunctionReadCount": [100],
            "SpanningFragCount": [200],
            "FFPM": [10.5],
        })

        cls.sf_runs_df = pd.DataFrame({
            "#FusionName": ["A--B"],
            "Count_predicted": [5],
        })

        cls.fastqc_pivot_df = pd.DataFrame({
            "SPECIMEN": ["2XX"],
            "Unique Reads": [1_000_000],
        })

        cls.fi_df = pd.DataFrame({
            "LeftBreakpoint": ["chr1:123"],
            "RightBreakpoint": ["chr2:456"],
            "PROT_FUSION_TYPE": ["in-frame"],
        })

        cls.prev_pos = pd.DataFrame({
            "Specimen Identifier": ["SP1"],
            "#FusionName": [["A--B"]],
        })

        cls.ref_sources = pd.DataFrame({
            "Fusion": ["A--B"],
            "ReferenceSources": ["PubMed"],
        })

        cls.pivot_config = {
            "index": ["SPECIMEN", "LEFTRIGHT"],
            "columns": None,
            "values": [
                "LeftBreakpoint",
                "#FusionName",
                "RightBreakpoint",
                "JunctionReadCount",
                "SpanningFragCount",
                "Count_predicted",
                "ReferenceSources",
                "PreviousPositives",
                "FRAME",
                "FFPM",
            ],
        }

        cls.result = parser.make_sf_pivot(
            cls.sf_df, cls.sf_runs_df, cls.fastqc_pivot_df,
            cls.fi_df, cls.prev_pos, cls.ref_sources,
            cls.pivot_config
        )

    def test_pivot_is_not_empty(self):
        assert not self.result.empty, "Pivot result is empty"

    def test_pivot_has_correct_index(self):
        assert isinstance(self.result.index, pd.MultiIndex), "Index is not MultiIndex"
        assert list(self.result.index.names) == self.pivot_config["index"], "Index names mismatch"

    def test_pivot_has_all_expected_columns(self):
        for col in self.pivot_config["values"]:
            assert col in self.result.columns, f"Missing column: {col}"

    def test_pivot_shape_is_expected(self):
        assert self.result.shape == (1, len(self.pivot_config["values"])), f"Unexpected shape: {self.result.shape}"

    def test_pivot_contains_correct_values(self):
        row = self.result.iloc[0]
        assert row["#FusionName"] == "A--B"
        assert row["FRAME"] == "in-frame"
        assert row["ReferenceSources"] == "PubMed"
