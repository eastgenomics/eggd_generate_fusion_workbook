"""
Module containing default constants for sheet configurations
Formulas adapted from demo WB provided by scientist
"""

FASTQC_SHEET_CONFIG = {
    "sheet_name": "FastQC",
    "tab_color": "008000",  # Green
    "extra_cols": {
        "Specimen": "=MID(C{row},11,10)",
        "EPIC": "=VLOOKUP(A{row},EPIC!AJ:AK,2,0)",
    },
}

SF_SHEET_CONFIG = {
    "sheet_name": "STAR-Fusion",
    "tab_color": "9400D3",  # Red
    "extra_cols": {
        "SPECIMEN": "=MID(K{row},11,10)",
        "FNAME": "=LEFT(K{row},28)",
        "Count_Run_1_Run_20_predicted": "=VLOOKUP(L{row},PC1_PC20_predicted_S!E:F,2,0)",
        "EPIC": "=VLOOKUP(A{row},EPIC!AJ:AK,2,0)",
        "DAYS COUNT": "=VLOOKUP(A{row},EPIC!AJ:AL,3,0)",
        "Unique Reads (M) PC3B": "=VLOOKUP(A{row},MultiQC_Pivot!A:C,3,0)",
        "Duplicate Reads (M) PC3B": "=VLOOKUP(A{row},MultiQC_Pivot!A:D,4,0)",
        "ID": '=CONCAT(A{row},"_",L{row})',
        "LEFTRIGHT": '=CONCATENATE(S{row},"_",U{row})',
        "FRAME": "=VLOOKUP(I{row},PC4_MERGED!C:AM,32,0)",
    },
}

FI_SHEET_CONFIG = {
    "sheet_name": "Fusion Inspector",
    "tab_color": "800080",  # Purple
    "extra_cols": {
        "SPECIMEN": "=MID(D{row},11,10)",
        "ID": '=CONCAT(A{row},"_",E{row})',
        "LEFTRIGHT": '=CONCAT(L{row},"_",O{row})',
    },
}

SF_PREVIOUS_RUNS_SHEET_CONFIG = {
    "sheet_name": "SF Previous Runs",
    "tab_color": "FFA500",  # Orange
    "extra_cols": None,
}

FI_PREVIOUS_RUNS_SHEET_CONFIG = {
    "sheet_name": "FI Previous Runs",
    "tab_color": "A52A2A",  # Brown
    "extra_cols": None,
}

EPIC_SHEET_CONFIG = {
    "sheet_name": "EPIC",
    "tab_color": "0000FF",  # Blue
    "extra_cols": None,
}
