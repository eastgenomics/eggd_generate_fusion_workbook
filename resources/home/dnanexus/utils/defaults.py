"""
Module containing default constants for sheet configurations
Formulas adapted from demo WB provided by scientist
"""

FASTQC_SHEET_CONFIG = {
    "sheet_name": "FastQC",
    "tab_color": "C581F0",
    "extra_cols": {
        "SPECIMEN": "=MID(C{row},11,10)",
        "EPIC": "=VLOOKUP(A{row},'EPIC'!AJ:AK,2,0)",
    },
}

SF_SHEET_CONFIG = {
    "sheet_name": "STAR-Fusion",
    "tab_color": "CFBF30",
    "extra_cols": {
        "SPECIMEN": "=MID(K{row},11,10)",
        "FNAME": "=LEFT(K{row},28)",
        "Count_predicted": "=VLOOKUP(L{row},'SF_Previous_Runs'!A:B,2,0)",
        "EPIC": "=VLOOKUP(A{row},'EPIC'!AJ:AK,2,0)",
        "DAYS COUNT": "=VLOOKUP(A{row},'EPIC'!AJ:AL,3,0)",
        "Unique Reads(M)": "=VLOOKUP(A{row},'FastQC_Pivot'!A:C,3,0)",
        "Duplicate Reads(M)": "=VLOOKUP(A{row},'FastQC_Pivot'!A:B,2,0)",
        "ID": '=CONCATENATE(A{row},"_",L{row})',
        "LEFTRIGHT": '=CONCATENATE(S{row},"_",U{row})',
        "FRAME": "=VLOOKUP(I{row},'Fusion_Inspector'!C:AM,32,0)",
    },
    "col_widths": {"K": 10},
}

FI_SHEET_CONFIG = {
    "sheet_name": "Fusion_Inspector",
    "tab_color": "C93030",
    "extra_cols": {
        "SPECIMEN": "=MID(D{row},11,10)",
        "ID": '=CONCATENATE(A{row},"_",E{row})',
        "LEFTRIGHT": '=CONCATENATE(L{row},"_",O{row})',
    },
    "col_widths": {"D": 10},
}

ARRIBA_SHEET_CONFIG = {
    "sheet_name": "Arriba",
    "tab_color": "069a2e",
    "extra_cols": {
        "SPECIMEN": "=MID(B{row},11,10)",
    },
    "col_widths": {"B": 10},
}

SF_PREVIOUS_RUNS_SHEET_CONFIG = {
    "sheet_name": "SF_Previous_Runs",
    "tab_color": "17171A",
    "extra_cols": None,
}


EPIC_SHEET_CONFIG = {
    "sheet_name": "EPIC",
    "tab_color": "48B7D9",
    "extra_cols": {
        "Month_Received": '=TEXT(C{row},"mmmm")',
        "Specimen": "=MID(B{row},4,100)",
        "EPIC": '=CONCATENATE(H{row}," | ",I{row}," | ",E{row})',
        "Days": "=TODAY()-C{row}",
    },
    "start_col": 35,
    "end_row": 100000,
}

REF_SOURCES_SHEET_CONFIG = {
    "sheet_name": "ReferenceSources",
    "tab_color": "17171A",
    "extra_cols": None,
}

PREV_POS_SHEET_CONFIG = {
    "sheet_name": "PreviousPositives",
    "tab_color": "17171A",
    "extra_cols": None,
}


FASTQC_PIVOT_CONFIG = {
    "index": ["SPECIMEN"],
    "columns": None,
    "values": [
        "Duplicate Reads(M)",
        "Unique Reads(M)",
    ],
    "aggfunc": "sum",
    "sheet_name": "FastQC_Pivot",
    "tab_color": "C581F0",
    "add_total_row": True,
    "extra_cols": {
        "EPIC": "=VLOOKUP(A{row},'EPIC'!AJ:AK,2,0)",
        "DAYS COUNT": "=VLOOKUP(A{row},'EPIC'!AJ:AL,3,0)",
    },
    "start_col": 4,
}

SF_PIVOT_CONFIG = {
    "index": [
        "Filename",
        "SPECIMEN",
        "Unique Reads(M)",
        "Duplicate Reads(M)",
        "LEFTRIGHT",
    ],
    "columns": None,
    "values": [
        "FFPM",
        "FRAME",
        "Count_predicted",
        "SpanningFragCount",
        "JunctionReadCount",
        "#FusionName",
        "LeftBreakpoint",
        "RightBreakpoint",
        "ReferenceSources",
        "PreviousPositives",
    ],
    "aggfunc": {
        "#FusionName": "first",
        "FRAME": "first",
        "FFPM": "first",
        "Count_predicted": "first",
        "SpanningFragCount": "first",
        "JunctionReadCount": "first",
        "LeftBreakpoint": "first",
        "RightBreakpoint": "first",
        "ReferenceSources": "first",
        "PreviousPositives": "first",
    },
    "sheet_name": "Summary",
    "tab_color": "CFBF30",
    "drop_downs": {
        "Reported": {
            "options": [
                "Yes",
                "No",
            ],
            "prompt": "Choose Yes or No",
            "title": "Fusion reported or not?",
        },
        "Oncogenicity": {
            "options": [
                "Pathogenic",
                "Likely Pathogenic",
                "VUS",
                "Likely Benign",
                "Benign",
            ],
            "prompt": "Select from the list",
            "title": "Oncogenicity",
        },
    },
    "extra_cols": {
        "EPIC": "=VLOOKUP(B{row},'EPIC'!AJ:AK,2,0)",
        "DAYS COUNT": "=VLOOKUP(B{row},'EPIC'!AJ:AL,3,0)",
    },
    "col_widths": {"D": 6, "E": 10, "F": 10, "J": 6, "K": 6, "L": 6, "M": 24, "N": 24},
    "col_colors": {"L": "780373", "M": "01982f", "N": "01982f"}
}
