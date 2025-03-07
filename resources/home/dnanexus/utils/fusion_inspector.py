"""Module for parsing fusion inspector data from DNAnexus files and 
adding computed columns using formulas.
"""
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from dxpy import DXDataObject
import dxpy
from typing import List

from .utils import read_dxfile


def parse_fusion_inspector(dxfiles: List[DXDataObject]) -> pd.DataFrame:
    """ Reads and concatenate an array DNAnexus fusion inspector files 
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


FUSION_INSPECTOR_EXTRA_COLS = {
    "SPECIMEN": "=MID(D{row},11,10)",
    "ID": '=CONCAT(A{row},"_",E{row})',
    "LEFTRIGHT": '=CONCAT(L{row},"_",O{row})'

}
