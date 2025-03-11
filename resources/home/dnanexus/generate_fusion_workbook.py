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

from utils.utils import write_df_to_sheet, get_project_info
from utils.fastqc import parse_fastqc
from utils.fusion_inspector import parse_fusion_inspector, FUSION_INSPECTOR_EXTRA_COLS
from utils.star_fusion import parse_star_fusion, STAR_FUSION_EXTRA_COLS


@dxpy.entry_point('main')
def main(
    starfusion_files: List,
    fusioninspector_files: List,
    fastqc_data: str,
    SF_previous_runs_data: str,
    FI_previous_runs_data: str,
):
    """
    main
    """

    # Initialize inputs into dxpy.DXDataObject instances

    starfusion_files = [
        dxpy.DXFile(item) for item in starfusion_files
    ]
    fusioninspector_files = [
        dxpy.DXFile(item) for item in fusioninspector_files
    ]
    fastqc_data = dxpy.DXFile(fastqc_data)
    SF_previous_data = dxpy.DXFile(SF_previous_runs_data)
    FI_previous_data = dxpy.DXFile(FI_previous_runs_data)

    df_starfusion = parse_star_fusion(starfusion_files)
    
    project_name, _ = get_project_info()
    outfile = f"{project_name}_fusion_workbook.xlsx"

    with pd.ExcelWriter(outfile, engine="openpyxl") as writer:
        write_df_to_sheet(
            writer, 
            df_starfusion,
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
