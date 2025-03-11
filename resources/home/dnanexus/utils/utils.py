"""general and I/O utilities
"""

import pandas as pd
import openpyxl
from openpyxl.styles import PatternFill, Font
import dxpy
from typing import List


def read_dxfile(
    dxfile: dxpy.DXDataObject,
    sep :str = "\t",
    include_fname :bool = True
    ) -> pd.DataFrame:
    """reads a DNAnexus file object into a pandas dataframe

    Args:
        dxfile (dxpy.DXDataObject): An instance of DXDataObject; behaves like a
            python file object.
        sep (str): delimeter of data values in file. Defaults to "\t".
        include_fname (bool): Specifies whether to set file name as first column.

    Returns:
        pd.DataFrame: An instance of DataFrame with file content
    """

    df = pd.read_csv(dxfile, sep=sep)
    
    if include_fname:
        fname = dxfile.name
        df.insert(0, "file_name", fname)
    
    return df


def write_df_to_sheet(
    writer: pd.ExcelWriter, 
    df: pd.DataFrame, 
    sheet_name: str, 
    tab_color: str = "000000",
    extra_cols: dict[str, str] = None
) -> None:
    """
    Writes a Pandas DataFrame to an Excel sheet with formatting.

    Args:
        writer (pd.ExcelWriter): The Excel writer object to write the sheet into.
        df (pd.DataFrame): The DataFrame containing the data.
        sheet_name (str): Name of the Excel sheet.
        tab_color (str): Hex colour code for the sheet tab. Defaults to black ("000000").
        extra_cols (dict): Dictionary of new columns with formulas. Example: 
            {
                "Specimen": "=MID(C{row},11,10)", 
                "EPIC": "=VLOOKUP(A{row},EPIC!AJ:AK,2,0)"
            }

    """
    df.to_excel(writer, sheet_name=sheet_name, index=False)
    worksheet = writer.sheets[sheet_name]
    worksheet.sheet_properties.tabColor = tab_color
    
    # Apply formatting to headers
    header_font = Font(bold=True)
    for idx, col in enumerate(df.columns, start=1):
        cell = worksheet.cell(row=1, column=idx, value=col)
        cell.font = header_font
    
    # Insert formula-based columns at the beginning if provided
    if extra_cols:
        num_cols = len(extra_cols)
        worksheet.insert_cols(1, amount=num_cols)

        for i, (col, formula) in enumerate(extra_cols.items(), start=1):
            worksheet.cell(row=1, column=i, value=col).font = header_font

            for row in range(2, worksheet.max_row + 1):
                worksheet.cell(
                    row=row, column=i, value=formula.replace("{row}", str(row))
                )

    # Adjust column widths for visibility
    for cells in worksheet.iter_cols():
        max_length = max(
            len(str(cell.value)) if cell.value else 0 for cell in cells
        )
        column_letter = cells[0].column_letter
        worksheet.column_dimensions[column_letter].width = max(
            max_length + 2, 10
        )


def get_project_info() -> tuple[str, str]:
    """
    Get the project name for naming output file

    Returns:
        project_name (str): name of DNAnexus project
        project_id (str): ID of DNAnexus project
    """
    project_id = os.environ.get("DX_PROJECT_CONTEXT_ID")

    # Get name of project for output naming
    project_name = dxpy.describe(project_id)["name"]
    project_name = "_".join(project_name.split("_")[1:])

    return project_name, project_id
