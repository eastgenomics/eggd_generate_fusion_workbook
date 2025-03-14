"""general and I/O utilities
"""

import os
import pandas as pd
import openpyxl
from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet
import dxpy
from dxpy import DXDataObject


def read_dxfile(
    dxfile: DXDataObject, sep: str = "\t", include_fname: bool = True
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


def _add_extra_columns(
    worksheet: Worksheet, extra_cols: dict[str, str]
) -> None:
    """
    Inserts additional columns with formulas at the beginning of a sheet

    Parameters
    ----------
    worksheet : Worksheet
        The worksheet where columns will be added.
    extra_cols : dict[str, str]
        A mapping of column names to Excel formulas

    Returns
    -------
    None
    """

    num_cols = len(extra_cols)
    worksheet.insert_cols(1, amount=num_cols)

    for i, (col, formula) in enumerate(extra_cols.items(), start=1):
        worksheet.cell(row=1, column=i, value=col)
        for row in range(2, worksheet.max_row + 1):
            worksheet.cell(row=row, column=i, value=formula.replace("{row}", str(row)))


def _apply_header_format(worksheet) -> None:
    """
    Applies bold formatting to all headers in the sheet.

    Parameters
    ----------
    worksheet : Worksheet
        The worksheet where header formatting will be applied.

    Returns
    -------
    None
    """
    header_font = Font(bold=True)
    for col in range(1, worksheet.max_column + 1):
        cell = worksheet.cell(row=1, column=col)
        cell.font = header_font


def _adjust_column_widths(worksheet):
    """
    Adjusts column widths for better visibility.

    Parameters
    ----------
    worksheet : Worksheet
        The worksheet where column widths will be adjusted.

    Returns
    -------
    None
    """
    for cell in worksheet[1]:  # Iterate over header row
        col_letter = cell.column_letter
        worksheet.column_dimensions[col_letter].width = max(
            len(str(cell.value)) + 2, 10
        )


def write_df_to_sheet(
    writer: pd.ExcelWriter,
    df: pd.DataFrame,
    sheet_name: str,
    tab_color: str = "000000",
    extra_cols: dict[str, str] = None,
) -> None:
    """Writes a Pandas DataFrame to an Excel sheet with formatting.

    Parameters
    ----------
    writer : pd.ExcelWriter
        The Excel writer object to write the sheet into
    df : pd.DataFrame
        The DataFrame containing the data.
    sheet_name : str
        Name of the Excel sheet
    tab_color : str, optional
        Hex colour code for the sheet tab. Defaults to black ("000000")
    extra_cols : dict[str, str], optional
        A mapping of new column names to excel formulas. Example:
            {
                "Specimen": "=MID(C{row},11,10)",
                "EPIC": "=VLOOKUP(A{row},EPIC!AJ:AK,2,0)"
            }
    """
    df.to_excel(writer, sheet_name=sheet_name, index=False)
    worksheet = writer.sheets[sheet_name]
    worksheet.sheet_properties.tabColor = tab_color

    # Add extra columns if provided
    if extra_cols:
        _add_extra_columns(worksheet, extra_cols)

    _apply_header_format(worksheet)
    _adjust_column_widths(worksheet)


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
    project_name = "_".join(project_name.split("_")[1:])

    return project_name, project_id
