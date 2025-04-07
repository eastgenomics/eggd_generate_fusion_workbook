"""
Module containing default constants for sheet configurations
Formulas adapted from demo WB provided by scientist
"""

FASTQC_SHEET_CONFIG = {
    "sheet_name": "FastQC",
    "tab_color": "008000",
    "extra_cols": {
        "SPECIMEN": "=MID(C{row},11,10)",
        "EPIC": "=VLOOKUP(A{row},'EPIC'!AJ:AK,2,0)",
    },
}

SF_SHEET_CONFIG = {
    "sheet_name": "STAR-Fusion",
    "tab_color": "800080",
    "extra_cols": {
        "SPECIMEN": "=MID(K{row},11,10)",
        "FNAME": "=LEFT(K{row},28)",
        "Count_predicted": "=VLOOKUP(L{row},'PC1_PC20_Predicted'!A:B,2,0)",
        "EPIC": "=VLOOKUP(A{row},'EPIC'!AJ:AK,2,0)",
        "DAYS COUNT": "=VLOOKUP(A{row},'EPIC'!AJ:AL,3,0)",
        "Unique Reads(M)": "=VLOOKUP(A{row},'FastQC_Pivot'!A:C,3,0)",
        "Duplicate Reads(M)": "=VLOOKUP(A{row},'FastQC_Pivot'!A:B,2,0)",
        "ID": '=CONCATENATE(A{row},"_",L{row})',
        "LEFTRIGHT": '=CONCATENATE(S{row},"_",U{row})',
        "FRAME": "=VLOOKUP(I{row},'Fusion_Inspector'!C:AM,32,0)",
    },
}

FI_SHEET_CONFIG = {
    "sheet_name": "Fusion_Inspector",
    "tab_color": "A52A2A",
    "extra_cols": {
        "SPECIMEN": "=MID(D{row},11,10)",
        "ID": '=CONCATENATE(A{row},"_",E{row})',
        "LEFTRIGHT": '=CONCATENATE(L{row},"_",O{row})',
    },
}

SF_PREVIOUS_RUNS_SHEET_CONFIG = {
    "sheet_name": "PC1_PC20_Predicted",
    "tab_color": "000000",
    "extra_cols": None,
}


EPIC_SHEET_CONFIG = {
    "sheet_name": "EPIC",
    "tab_color": "0000FF",
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
    "tab_color": "00FF00",
    "add_total_row": True,
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
        "RightBreakpoint"
    ],
    "aggfunc": {
        "#FusionName": "first",
        "FRAME": "first",
        "FFPM": "first",
        "Count_predicted": "first",
        "SpanningFragCount": "first",
        "JunctionReadCount": "first",
        "LeftBreakpoint": "first",
        "RightBreakpoint": "first"
    },
    "sheet_name": "Summary",
    "tab_color": "9400D3",
    "drop_downs": {
        "Reported": {
            "options": ["Yes", "No",],
            "prompt": "Choose Yes or No",
            "title": "Fusion reported or not?"
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
            "title": "Oncogenicity"
            
        }
        
    },
    "extra_cols":{
        "EPIC": "=VLOOKUP(B{row},'EPIC'!AJ:AK,2,0)",
        "DAYS COUNT": "=VLOOKUP(B{row},'EPIC'!AJ:AL,3,0)",
    },
}
