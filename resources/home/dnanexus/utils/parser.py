"""Module for parsing fusion data from their respective DNAnexus files into a
pandas data frame
"""

from concurrent.futures import ThreadPoolExecutor
import dxpy
import pandas as pd
from dxpy import DXDataObject
from typing import List

from .utils import read_dxfile


def parse_fastqc(dxfile: DXDataObject) -> pd.DataFrame:
    """Parse the content of fastqc multiqc output and compute required 
    metrics from deduplicated_percentage

    Parameters
    ----------
    dxfile : DXDataObject
        DNAnexus file object containing fastqc data to parse

    Returns
    -------
    pd.DataFrame
        pandas dataframe containing selected and computed fastqc metrics

    Raises
    ------
    ValueError
        if columns needed to compute extra metrics are absent.
    """

    df = read_dxfile(dxfile, include_fname=False)

    # Verify required columns exist
    required_cols = ["total_deduplicated_percentage", "Total Sequences"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Required columns missing from FastQC data: {missing_cols}"
        )

    df["Unique Reads"] = (
        (df["total_deduplicated_percentage"] / 100.0) * df["Total Sequences"]
        ).astype(int)
    df["Duplicate Reads"] = (
        df["Total Sequences"] - df["Unique Reads"]
        ).astype(int)
    df["Unique Reads(M)"] = df["Unique Reads"] / 1000000
    df["Duplicate Reads(M)"] = df["Duplicate Reads"] / 1000000
    df = df[
        [
            "Sample",
            "Unique Reads",
            "Duplicate Reads",
            "Unique Reads(M)",
            "Duplicate Reads(M)",
        ]
    ]

    return df


def _parse_fusion_files(dxfiles: List[DXDataObject]) -> pd.DataFrame:
    """
    Reads and concatenates a list of DNAnexus fusion-related files
    into a single DataFrame.

    Parameters
    ----------
    dxfiles : List[DXDataObject]
        A list of DNAnexus file objects.

    Returns
    -------
    pd.DataFrame
        A concatenated DataFrame containing the combined data
        from all input files.
    """
    if not dxfiles:
        return pd.DataFrame()

    max_workers = min(16, len(dxfiles))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        df = pd.concat(executor.map(read_dxfile, dxfiles))

    return df


def parse_fusion_inspector(dxfiles: List[DXDataObject]) -> pd.DataFrame:
    """
    Reads and concatenates an array of DNAnexus Fusion Inspector files.

    Parameters
    ----------
    dxfiles : List[DXDataObject]
        A list of DNAnexus file objects.

    Returns
    -------
    pd.DataFrame
        A concatenated DataFrame containing the combined data
        from all input files.
    """
    # simply calls _parse_fusion_files for now
    # can be easily extended if additional logic needed for tool
    return _parse_fusion_files(dxfiles)


def parse_star_fusion(dxfiles: List[DXDataObject]) -> pd.DataFrame:
    """
    Reads and concatenates an array of DNAnexus STAR-Fusion files.

    Parameters
    ----------
    dxfiles : List[DXDataObject]
        A list of DNAnexus file objects.

    Returns
    -------
    pd.DataFrame
        A concatenated DataFrame containing the combined data
        from all input files.
    """
    # same as above; to allow further customisation per tool as needed.
    return _parse_fusion_files(dxfiles)
