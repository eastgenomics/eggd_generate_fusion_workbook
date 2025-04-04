"""utilities for formating summary sheet
"""
import openpyxl
import pandas as pd
from openpyxl.styles import (
    PatternFill,
    Border,
    Side, 
    Alignment, 
    DEFAULT_FONT,
    Font
)
from openpyxl.worksheet.datavalidation import DataValidation

from .utils import generate_varsome_url

DEFAULT_FONT.name = 'Calibri'


def alternate_specimen_colors(worksheet, df, index_col):
    """Apply alternate row colors between specimen groups.

    Parameters
    ----------
    worksheet : Worksheet
        The sheet where formating will be applied
    df : pd.DataFrame
        Data frame containing original summary data
    index_col : str
        Column to use for grouping
    """
    blue_fill = PatternFill(start_color='FFB4C6E7', end_color='FFB4C6E7', fill_type='solid')
    green_fill = PatternFill(start_color='FFC6E0B4', end_color='FFC6E0B4', fill_type='solid')
    
    colors = [blue_fill, green_fill]
    
    for i, (specimen, group) in enumerate(df.groupby(index_col)):
        # alternate colors
        fill = colors[i % len(colors)]
    
        # Apply fill to all rows in this group
        for row in group.index:
            excel_row = row + 2  
            for col in range(1, worksheet.max_column + 1):
                worksheet.cell(row=excel_row, column=col).fill = fill


def highlight_borders(worksheet, df, index_col):
    """Adds thick borders between specimen groups.

    Parameters
    ----------
    worksheet : Worksheet
        The sheet where formating will be applied
    df : pd.DataFrame
        Data frame containing original summary data
    index_col : str
        Column to use for grouping"
    """
    thick_border = Border(bottom=Side(style='thick'))
    
    # Find last row of each specimen group
    last_rows = df.groupby(index_col).tail(1).index
    
    # Apply border to last row of each group
    for row in last_rows:
        excel_row = row + 2 
        for col in range(1, worksheet.max_column + 1):
            worksheet.cell(row=excel_row, column=col).border = thick_border


def align_column_cells(worksheet, col_letter: str, direction: str = 'left'):
    """
    Align all cells in a specified column to a given horizontal alignment.
    
    Parameters
    ----------
    worksheet : openpyxl.worksheet.worksheet.Worksheet
        The target Excel worksheet
    col_letter : str
        Column letter to format (e.g., 'A', 'D')
    direction : str, optional
        Horizontal alignment direction. Valid values:
        - 'left' (default)
        - 'center'
        - 'right'
        - 'justify'
        - 'distributed'
    """
    valid_directions = ['left', 'center', 'right', 'justify', 'distributed']
    if direction.lower() not in valid_directions:
        raise ValueError(f"Invalid direction. Choose from: {valid_directions}")

    col_idx = openpyxl.utils.column_index_from_string(col_letter)
    alignment = Alignment(horizontal=direction.lower())

    for row in worksheet.iter_rows(min_col=col_idx, max_col=col_idx):
        for cell in row:
            cell.alignment = alignment


def set_column_width(worksheet, col_letter: str, width: float):
    """
    Set fixed width for a specified column.
    For columns needing specific adjustment.
    
    Parameters
    ----------
    worksheet : openpyxl.worksheet.worksheet.Worksheet
        The target Excel worksheet
    col_letter : str
        Column letter to format (e.g., 'B', 'AA')
    width : float
        Column width in character units (Excel's standard measurement)
    """
    worksheet.column_dimensions[col_letter].width = width


def colour_hyperlinks(worksheet) -> None:
    
    """
    Set text colour to blue if text contains hyperlink

    Parameters
    ----------
    worksheet : openpyxl.worksheet.worksheet.Worksheet
        The target Excel worksheet
    """
    for cells in worksheet.rows:
        for cell in cells:
            if 'HYPERLINK' in str(cell.value):
                cell.font = Font(color='00007f', name=DEFAULT_FONT.name)
                
                
def add_drop_down_col(
    sheet,
    header_name,
    dropdown_options,
    prompt, 
    title,
    start=1,
    position=None
):
    """
    Creates a dropdown column at at the specified position.

    Parameters
    ----------
    sheet : openpyxl.worksheet.worksheet.Worksheet
        current worksheet
    header_name : str
        Name of the new dropdown column
    dropdown_options : List[str]
        List containing drop-down items
    prompt: str
            prompt message for drop-down
    title: str
            title message for drop-down
    start : int
        Row index where sheets starts, defaults to 1
    position : int|None
        Column index to add dropdown or at the end if not given
    """
    ws = sheet
    last_col = ws.max_column

    # Insert at specific position or at the end
    col_idx = position if position else last_col + 1
    ws.insert_cols(col_idx)
    col_letter = openpyxl.utils.get_column_letter(col_idx)
    ws[f"{col_letter}{start}"] = header_name

    # Create data validation for dropdown
    dv = DataValidation(
        type="list",
        formula1=f'"{",".join(dropdown_options)}"',
        showDropDown=True,
        allow_blank=True,
    )
    dv.prompt = prompt
    dv.promptTitle = title
    ws.add_data_validation(dv)

    # Apply dropdown to all rows
    for row in range(start + 1, ws.max_row + 1):
        dv.add(ws[f"{col_letter}{row}"])
        
    dv.showInputMessage = True
    dv.showErrorMessage = True
    
    # adjust column width to accommodate longest string in dropdown items 
    col_width = max(len(x) for x in dropdown_options + [header_name])
    set_column_width(ws, col_letter, width=col_width + 2)
    
    
def add_hyperlink(cell, url: str, text: str = None) -> None:
    """
    Add Excel hyperlink formula to cell

    Parameters
    ----------
    cell : openpyxl.cell.cell.Cell
        The target cell.
    url : str
        The URL to link to.
    text : str
        Text to display in the cell. Defaults to the cell value.
    """
    
    value = text if text else cell.value
    
    if url:
        cell.value = f'=HYPERLINK("{url}", "{value}")'
        

def add_breakpoint_hyperlinks(
    writer,
    breakpoint_columns=("leftbreakpoint", "rightbreakpoint"), 
    header_row=1
):
    """
    Apply VarSome hyperlinks to breakpoint columns across all sheets in the workbook.

    Parameters
    ----------
    writer : pd.ExcelWriter
        The pandas openpyxl ExcelWriter
    breakpoint_columns : tuple
        Column names to check for breakpoints.
    header_row : int
        Row number where headers are located (1-based).
    """

    for sheet_name, worksheet in writer.sheets.items():
        max_col = worksheet.max_column
        max_row = worksheet.max_row

        # Get header row values
        headers = [
            worksheet.cell(row=header_row, column=col).value
            for col in range(1, max_col + 1)
        ]
        headers = [
            col.strip().lower() if isinstance(col, str) else ""
            for col in headers
        ]

        for bp_col in breakpoint_columns:
            if bp_col not in headers:
                continue

            col_idx = headers.index(bp_col) + 1  # 1-based
            col_letter = openpyxl.utils.get_column_letter(col_idx)

            for row in range(header_row + 1, max_row + 1):
                cell = worksheet[f"{col_letter}{row}"]
                value = cell.value
                if value and isinstance(value, str):
                    try:
                        url = generate_varsome_url(value)
                        add_hyperlink(cell, url, value)
                    except Exception as e:
                        print(
                            f"Could not process {value} at {sheet_name}!{col_letter}{row}: {e}"
                        )

def get_col_letter(worksheet, col_name) -> str:
    """
    Getting the column letter with specific col name

    Parameters
    ----------
    worksheet: openpyxl.Writer
            writer object of current sheet
    col_name: str
            name of column to get col letter
    Return
    -------
    str
        column letter for specific column name
    """
    col_letter = None
    for column_cell in worksheet.iter_cols(1, worksheet.max_column):
        if column_cell[0].value == col_name:
            col_letter = column_cell[0].column_letter

    return col_letter


def format_workbook(writer) -> None:
    """apply formatting to entire workbook

    Parameters
    ----------
    writer : pd.ExcelWriter
    The pandas openpyxl ExcelWriter
    """
    
    workbook = writer.book
    
    add_breakpoint_hyperlinks(writer)
    
    for sheet in workbook.worksheets:
        colour_hyperlinks(sheet)
        
        # other general formating to follow here ...