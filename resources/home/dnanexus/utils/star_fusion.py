"""Module for parsing STAR-Fusion data from DNAnexus files.
"""
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from dxpy import DXDataObject
import dxpy
from typing import List

from .utils import read_dxfile


def parse_star_fusion(dxfiles: List[DXDataObject]) -> pd.DataFrame:
    """ Reads and concatenate an array DNAnexus STAR-Fusion files 
        into a single DataFrame.


    Args:
        dxfiles (List[DXDataObject]): A list of DNAnexus file objects

    Returns:
        pd.DataFrame:  A concatenated DataFrame containing the combined data 
            from all input files.
    """
    
    with ThreadPoolExecutor(max_workers=16) as executor:
        df = pd.concat(
            executor.map(read_dxfile, dxfiles)
        )
    return df


# formulas lifted from demo WB provided by scientist
STAR_FUSION_EXTRA_COLS = {
    "SPECIMEN": "=MID(K{row},11,10)",
    "FNAME": "=LEFT(K{row},28)",
    "Count_Run_1_Run_20_predicted": "=VLOOKUP(L{row},PC1_PC20_predicted_S!E:F,2,0)",
    "EPIC": "=VLOOKUP(A{row},EPIC!AJ:AK,2,0)",
    "DAYS COUNT": "=VLOOKUP(A{row},EPIC!AJ:AL,3,0)",
    "Unique Reads (M) PC3B": "=VLOOKUP(A{row},MultiQC_Pivot!A:C,3,0)",
    "Duplicate Reads (M) PC3B": "=VLOOKUP(A{row},MultiQC_Pivot!A:D,4,0)",
    "ID": '=CONCAT(A{row},"_",L{row})',
    "LEFTRIGHT": '=CONCATENATE(S{row},"_",U{row})',
    "FRAME": "=VLOOKUP(I{row},PC4_MERGED!C:AM,32,0)"
}
