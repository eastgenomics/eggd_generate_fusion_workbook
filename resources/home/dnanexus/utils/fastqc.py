"""collates total_deduplicated_percentage from multiqc_fastqc.txt
"""
import pandas as pd
from dxpy import DXDataObject
import dxpy
from .utils import read_dxfile


def parse_fastqc(dxfile: DXDataObject) -> pd.DataFrame:
    
    df = read_dxfile(dxfile, include_fname=False)
    
    df["Unique Reads"] = (
        (df["total_deduplicated_percentage"] / 100.0) * df["Total Sequences"]
    ).astype(int)
    df["Duplicate Reads"] = (
        df["Total Sequences"] - df["Unique Reads"]
    ).astype(int)
    df["Unique Reads(M)"] = df["Unique Reads"] / 1000000
    df["Duplicate Reads(M)"] = df["Duplicate Reads"] / 1000000
    df = df[[
        "Sample",
        "Unique Reads",
        "Duplicate Reads",
        "Unique Reads(M)",
        "Duplicate Reads(M)"
    ]]

    return df

# formulas lifted from demo WB provided by scientist
FASTQC_EXTRA_COLS = {
    "Specimen": "=MID(C{row},11,10)",
    "EPIC": "=VLOOKUP(A{row},EPIC!AJ:AK,2,0)"
}
