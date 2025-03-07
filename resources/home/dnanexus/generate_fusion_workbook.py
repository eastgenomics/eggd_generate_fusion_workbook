#!/usr/bin/env python3
# eggd_generate_fusion_workbook 1.0.0


import os
import pip
from glob import glob
import dxpy

from typing import List


pip.main(["install", "--no-index", "--no-deps", *glob("packages/*")])

import pandas as pd
import openpyxl 

from utils.utils import write_df_to_sheet
from utils.fastqc import parse_fastqc
from utils.fusion_inspector import parse_fusion_inspector, FUSION_INSPECTOR_EXTRA_COLS
from utils.star_fusion import parse_star_fusion, STAR_FUSION_EXTRA_COLS

@dxpy.entry_point('main')
def main(
    starfusion_predictions,
    fusioninspector_predictions,
    fastqc_output,
    PC1_PC20_predicted_S,
    PC1_PC20_merged_S,
    epic=None
):
    """
    main
    """

    # Initialize inputs into dxpy.DXDataObject instances

    starfusion_predictions = [
        dxpy.DXFile(item) for item in starfusion_predictions
    ]
    fusioninspector_predictions = [
        dxpy.DXFile(item) for item in fusioninspector_predictions
    ]
    fastqc_output = dxpy.DXFile(fastqc_output)
    PC1_PC20_predicted_S = dxpy.DXFile(PC1_PC20_predicted_S)
    PC1_PC20_merged_S = dxpy.DXFile(PC1_PC20_merged_S)
    if epic is not None:
        epic = dxpy.DXFile(epic)

    
    df_star_fusion = parse_star_fusion(starfusion_predictions)
    
    outfile = "output.xlsx"
    

    with pd.ExcelWriter(outfile, engine="openpyxl") as writer:
        write_df_to_sheet(
            writer, 
            df_star_fusion, 
            sheet_name="STAR",
            tab_color="FF0000",
            extra_cols=STAR_FUSION_EXTRA_COLS
        )
        
        ### to do
        # add other sheets
        # add pivots
        # improve dxapp.json
        # add docstrings
        # change outputfile to project name

    fusion_workbook = dxpy.upload_local_file(outfile)

    output = {}
    output["fusion_workbook"] = dxpy.dxlink(fusion_workbook)

    return output


if __name__ == "__main__":
    dxpy.run()
