"""Module for parsing fusion data from their respective DNAnexus files into a
pandas data frame
"""

import re
from concurrent.futures import ThreadPoolExecutor
from typing import List

import dxpy
import pandas as pd
from dxpy import DXDataObject

from .utils import create_pivot_table, read_dxfile


def parse_specimen_id(sample: str) -> str:
    """parse SP ID from sample name

    Parameters
    ----------
    sample : str
        sample name in format 12345678-2XXXXSXXX-25PCAN4-10011_S33_L001_R1

    Returns
    -------
    str
        extracted SP eg 2XXXXSXXX
    """
    return sample.split("-")[1]


def parse_igv_specimen_name(sample: str) -> str:
    """parse SP ID from sample name in IGV format

    Parameters
    ----------
    sample : str
        sample name in format 12345678-2XXXXSXXX-25PCAN4-10011_S33_L001_R1

    Returns
    -------
    str
        extracted SP eg 12345678-2XXXXSXXX-25PCAN4
    """
    return "-".join(sample.split("-")[:3])


def extract_fusions(text: str) -> list:
    """
    Processes free-text reports to identify gene fusion patterns
    (e.g., EML4::ALK, TPM3- ROS1, EWSR1-SMAD3-rearranged, ),
    filters out transcript IDs (NM_|NR_|ENST), and
    standardises gene pairs with '--' separator.

    Parameters
    ----------
    text : str
        Free-text input from scientist reports containing fusion genes

    Returns
    -------
    list
        Unique standardised fusion pairs in GENE1--GENE2 format,
        or empty list if no valid fusions found
    """
    if not text or pd.isna(text):
        return []

    # Accounts for accidental white space in sepators;
    # OK to capture some non-gene fusions here;
    # Only true fusions will be merged in summary sheet
    pattern = r"""
        \b
        (?!NM_|NR_|ENST)
        ([A-Z]{2,}[A-Za-z0-9_-]*)
        \s*
        (?: :: | -- | - )
        \s*
        (?!NM_|NR_|ENST)
        ([A-Z]{2,}[A-Za-z0-9_-]*)
        \b
    """
    matches = re.findall(pattern, text, re.VERBOSE)

    # Deduplicate and standardise format
    return list({f"{g1}--{g2}" for g1, g2 in matches if g1 and g2})


def parse_sf_previous(dxfile: DXDataObject) -> pd.DataFrame:
    """Parse the content of sf_previous_run_data file

    Parameters
    ----------
    dxfile : DXDataObject
        DNAnexus file object containing data to parse

    Returns
    -------
    pd.DataFrame
        pandas dataframe containing selected columns
    """

    df = read_dxfile(dxfile, include_fname=False)
    df = (
        df[["#FusionName", "Count_predicted"]]
        .drop_duplicates()
        .sort_values(by="#FusionName")
        .reset_index(drop=True)
    )

    return df


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
        raise ValueError(f"Required columns missing from FastQC data: {missing_cols}")

    df["Unique Reads"] = (
        (df["total_deduplicated_percentage"] / 100.0) * df["Total Sequences"]
    ).astype(int)
    df["Duplicate Reads"] = (df["Total Sequences"] - df["Unique Reads"]).astype(int)
    df["Unique Reads(M)"] = df["Unique Reads"] / 1_000_000
    df["Duplicate Reads(M)"] = df["Duplicate Reads"] / 1_000_000
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


def make_fastqc_pivot(df: pd.DataFrame, pivot_config: dict) -> pd.DataFrame:
    """generates FastQC pivot table

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe containing raw fastqc data
    pivot_config : dict
        Mapping defining pivot structure

    Returns
    -------
    pd.DataFrame
        created pivot table with computed columns
    """
    df["SPECIMEN"] = df["Sample"].apply(parse_specimen_id)

    pivot_df = create_pivot_table(df, pivot_config)
    pivot_df = pivot_df.reset_index(drop=False)

    return pivot_df


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
        futures = [executor.submit(read_dxfile, dxfile) for dxfile in dxfiles]
        results = []
        for future in futures:
            try:
                results.append(future.result())
            except Exception as e:
                # Log the error and continue with other files
                print(f"Error processing file: {e}")

        if not results:
            return pd.DataFrame()

        df = pd.concat(results)

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
    df = _parse_fusion_files(dxfiles)
    df["file_name"] = (
        df["file_name"].str.split("_").str[0]
        + "_FusionInspector.fusions.abridged.merged.tsv"
    )
    df = (
        df.sort_values(by=["JunctionReadCount", "SpanningFragCount"])
        .drop_duplicates()
        .reset_index(drop=True)
    )
    return df


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


def parse_prev_pos(dxfile: DXDataObject) -> pd.DataFrame:
    """Parse the content of previous_positives data and modify Fusion column

    Parameters
    ----------
    dxfile : DXDataObject
        DNAnexus file object containing previous_positives data

    Returns
    -------
    pd.DataFrame
        pandas dataframe containing modified data

    """
    df = read_dxfile(dxfile, sep=",", include_fname=False)
    df["#FusionName"] = df["Test Result"].apply(extract_fusions)

    return df


def make_sf_pivot(
    sf_df: pd.DataFrame,
    sf_runs_df: pd.DataFrame,
    fastqc_pivot_df: pd.DataFrame,
    fi_df: pd.DataFrame,
    prev_pos: pd.DataFrame,
    ref_sources: pd.DataFrame,
    pivot_config: dict,
) -> pd.DataFrame:
    """Generates STAR-Fusion pivot table with merged data

    Parameters
    ----------
    sf_df : pd.DataFrame
        Current STAR-Fusion data
    sf_runs_df : pd.DataFrame
        Historical STAR-Fusion data
    fastqc_pivot_df : pd.DataFrame
        FastQC summary data
    fi_df : pd.DataFrame
        Current Fusion Inspector data
    prev_pos : pd.DataFrame
        Previously reported Fusions
    ref_sources : pd.DataFrame
        Reference source of Fusions
    pivot_config : dict
        Pivot configuration parameters

    Returns
    -------
    pd.DataFrame
        Created Pivot table with merged data
    """

    df = sf_df.copy()

    if "file_name" in sf_df.columns:
        df["SPECIMEN"] = df["file_name"].apply(parse_specimen_id)

        df["Filename"] = df["file_name"].apply(parse_igv_specimen_name)

    df["ID"] = df["SPECIMEN"] + "_" + df["#FusionName"]

    df["LEFTRIGHT"] = df["LeftBreakpoint"] + "_" + df["RightBreakpoint"]

    # Merge previous runs data (VLOOKUP equivalent)
    if not sf_runs_df.empty:
        df = df.merge(
            sf_runs_df[["#FusionName", "Count_predicted"]],
            on="#FusionName",
            how="left",
        )
        df["Count_predicted"] = df["Count_predicted"].fillna(0).astype(int)

    # Merge FastQC metrics (VLOOKUP to FastQC_pivot)
    if not fastqc_pivot_df.empty:
        df = df.merge(fastqc_pivot_df, on="SPECIMEN", how="left")

    # Merge Fusion Inspector data
    if not fi_df.empty:
        fi_df["LEFTRIGHT"] = fi_df["LeftBreakpoint"] + "_" + fi_df["RightBreakpoint"]
        df = df.merge(
            fi_df[["LEFTRIGHT", "PROT_FUSION_TYPE"]], on="LEFTRIGHT", how="left"
        ).rename(columns={"PROT_FUSION_TYPE": "FRAME"})

    # add prev positives
    prev_pos = (
        prev_pos[["Specimen Identifier", "#FusionName"]]
        .rename(columns={"Specimen Identifier": "PreviousPositives"})
        .explode("#FusionName", ignore_index=True)
        .dropna(subset=["#FusionName"])
    )
    prev_pos_agg = (
        prev_pos.groupby("#FusionName")["PreviousPositives"]
        .apply(lambda x: ",".join(sorted(x)))
        .reset_index()
    )
    df = df.merge(prev_pos_agg, on="#FusionName", how="left")
    df["PreviousPositives"] = df["PreviousPositives"].fillna("")

    # add ref sources
    df = df.merge(
        ref_sources.rename(columns={"Fusion": "#FusionName"}),
        on="#FusionName",
        how="left",
    )
    df["ReferenceSources"] = df["ReferenceSources"].fillna("")

    # Create final pivot table
    df = df.sort_values(by=["FFPM"], na_position="first").reset_index(drop=True)
    pivot_df = (
        df.groupby(pivot_config["index"], dropna=False)[pivot_config["values"]]
        .first()
        .sort_values(by=["SPECIMEN", "LEFTRIGHT"], na_position="first")
    )

    pivot_df = pivot_df[
        [
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
        ]
    ]

    return pivot_df
