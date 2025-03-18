"""Module for parsing fusion data from their respective DNAnexus files into a
pandas data frame
"""

from concurrent.futures import ThreadPoolExecutor
import dxpy
import pandas as pd
from dxpy import DXDataObject
from typing import List

from .utils import read_dxfile, create_pivot_table


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


def make_fastqc_pivot(df:pd.DataFrame, pivot_config:dict) -> pd.DataFrame:
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
    df["SPECIMEN"] = df["Sample"].astype(str).str[10:20]
    # omit EPIC col for now
    
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


def make_sf_pivot(
    sf_df: pd.DataFrame,
    sf_runs_df: pd.DataFrame,
    fastqc_pivot_df: pd.DataFrame,
    fi_df: pd.DataFrame,
    pivot_config: dict
) -> pd.DataFrame:
    """Generates STAR-Fusion pivot table with merged data
    
    Parameters
    ----------
    sf_df : pd.DataFrame
        Main STAR-Fusion data
    sf_runs_df : pd.DataFrame
        Historical STAR-Fusion data
    fastqc_pivot_df : pd.DataFrame
        FastQC summary data
    fi_df : pd.DataFrame
        Main Fusion Inspector data
    pivot_config : dict
        Pivot configuration parameters

    Returns
    -------
    pd.DataFrame
        Created Pivot table with merged data
    """
    
    df = sf_df.copy()
    
    # =MID(K{row},11,10)
    if 'file_name' in sf_df.columns:
        df['SPECIMEN'] = df['file_name'].astype(str).str[10:20]
    
        # =LEFT(K{row},28)
        df['FNAME'] = df['file_name'].astype(str).str[:28]
        
    # =CONCAT(A{row},"_",L{row})
    df['ID'] = df['SPECIMEN'] + "_" + df['#FusionName']
    
    # =CONCATENATE(S{row},"_",U{row})
    df['LEFTRIGHT'] = df['LeftBreakpoint'] + "_" + df['RightBreakpoint']

    # Merge previous runs data (VLOOKUP equivalent)
    if not sf_runs_df.empty:
        df = df.merge(
            sf_runs_df[['#FusionName', 'Count_Run_1_Run_20_predicted']],
            on='#FusionName',
            how='left'
        )
        df['Count_Run_1_Run_20_predicted'] = (
            df['Count_Run_1_Run_20_predicted']
            .fillna(0)
            .astype(int)
        )

    # Merge FastQC metrics (VLOOKUP to FastQC_pivot)
    if not fastqc_pivot_df.empty:
        df = df.merge(
            fastqc_pivot_df,
            on='SPECIMEN',
            how='left'
        )

    # Merge Fusion Inspector data
    if not fi_df.empty:
        df = df.merge(
            fi_df[['LEFTRIGHT','PROT_FUSION_TYPE']],
            on='LEFTRIGHT',
            how='left'
        ).rename(columns={'PROT_FUSION_TYPE': 'FRAME'})

    # Create final pivot table
    pivot_df = create_pivot_table(df, pivot_config)
    
    return pivot_df
