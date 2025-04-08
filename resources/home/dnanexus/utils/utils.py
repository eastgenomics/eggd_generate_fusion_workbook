"""general and I/O utilities
"""

import re
import os
from urllib.parse import quote

import dxpy
import pandas as pd
from dxpy import DXDataObject


def read_dxfile(
    dxfile: DXDataObject,
    sep: str = "\t",
    include_fname: bool = True,
) -> pd.DataFrame:
    """reads a DNAnexus file object into a pandas dataframe

    Parameters
    ----------
    dxfile : DXDataObject
        An instance of DXDataObject; behaves like a python file object.
    sep : str
        Delimeter of data values in files. Defaults to  "\t"
    include_fname : bool
        Specifies whether to set file name as first column. Defaults to True

    Returns
    -------
    pd.DataFrame
        An instance of DataFrame with file content
    """

    df = pd.read_csv(dxfile, sep=sep)

    if include_fname:
        fname = dxfile.name
        df.insert(0, "file_name", fname)

    return df


def create_pivot_table(
    df: pd.DataFrame,
    pivot_config: dict,
) -> pd.DataFrame:
    """Creates pivot table from a dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        Source dataframe to create pivot from
    pivot_config : dict
        Dictionary defining pivot structure:
            - index: Columns to group by (list for MultiIndex)
            - columns: Columns for column grouping
            - values: Value columns to aggregate
            - aggfunc: Aggregation function
            - add_total_row: Whether to add totals (default False)

    Returns
    ------
    pd.DataFrame
        created pivot table
    """

    # Create pivot table
    pivot_df = df.pivot_table(
        index=pivot_config["index"],
        columns=pivot_config["columns"],
        values=pivot_config["values"],
        aggfunc=pivot_config["aggfunc"],
        margins=pivot_config.get("add_total_row", False),
        margins_name="Total",
    )

    return pivot_df


def get_project_info() -> tuple[str, str]:
    """Get the project name for naming output file

    Returns
    -------
    tuple[str, str]
        Name and ID of DNAnexus project
    """

    project_id = os.environ.get("DX_PROJECT_CONTEXT_ID")

    # Get name of project for output naming
    project_name = dxpy.describe(project_id)["name"]
    project_name = project_name.split("_", 1)[1]

    return project_name, project_id


def generate_varsome_url(breakpoint: str) -> str:
    """Generate VarSome URL from breakpoint string.

    Parameters
    ----------
    breakpoint : str
        Genomic coordinate in format "chr15:39594440:+" or "chr15:39594440:-"

    Returns
    -------
    str
        Enconded Varsome URL string
    """

    base_url = "https://varsome.com/position/hg38/"

    # remove ':' followed by '+' or '-' only at the end
    bp = re.sub(r"[:][+\-]$", "", breakpoint)
    encoded = quote(bp)

    return f"{base_url}{encoded}"


def validate_config(config: dict, expected_keys: list):
    """
    Validates that required keys exist in given config.

    Parameters
    ----------
    config : dict
        The config to validate.
    expected_keys : list
        List of expected keys to check in the config.

    Raises
    ------
    ValueError
        If any keys are missing.
    """
    missing_keys = [key for key in expected_keys if key not in config]
    if missing_keys:
        raise ValueError(f"Missing required config key(s): {', '.join(missing_keys)}")
