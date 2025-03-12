#!/usr/bin/env python3
# eggd_generate_fusion_workbook 1.0.0

import os
from glob import glob
from typing import List

import dxpy
import pip

pip.main(["install", "--no-index", "--no-deps", *glob("packages/*")])

import openpyxl
import pandas as pd
from utils.defaults import (
    EPIC_SHEET_CONFIG,
    FASTQC_SHEET_CONFIG,
    FI_PREVIOUS_RUNS_SHEET_CONFIG,
    FI_SHEET_CONFIG,
    SF_PREVIOUS_RUNS_SHEET_CONFIG,
    SF_SHEET_CONFIG,
)
from utils.parser import parse_fastqc, parse_fusion_inspector, parse_star_fusion
from utils.utils import get_project_info, read_dxfile, write_df_to_sheet


@dxpy.entry_point("main")
def main(
    starfusion_files: List,
    fusioninspector_files: List,
    fastqc_data: str,
    SF_previous_runs_data: str,
    FI_previous_runs_data: str,
):
    """_summary_

    Parameters
    ----------
    starfusion_files : List
        _description_
    fusioninspector_files : List
        _description_
    fastqc_data : str
        _description_
    SF_previous_runs_data : str
        _description_
    FI_previous_runs_data : str
        _description_

    Returns
    -------
    _type_
        _description_
    """
    # Initialize inputs into dxpy.DXDataObject instances
    starfusion_files = [dxpy.DXFile(item) for item in starfusion_files]
    fusioninspector_files = [dxpy.DXFile(item) for item in fusioninspector_files]
    fastqc_data = dxpy.DXFile(fastqc_data)
    sf_previous_data = dxpy.DXFile(SF_previous_runs_data)
    fi_previous_data = dxpy.DXFile(FI_previous_runs_data)

    df_starfusion = parse_star_fusion(starfusion_files)
    df_fusioninspector = parse_fusion_inspector(fusioninspector_files)
    df_fastqc = parse_fastqc(fastqc_data)

    df_sf_previous = read_dxfile(sf_previous_data)
    df_fi_previous = read_dxfile(fi_previous_data)

    project_name, _ = get_project_info()
    outfile = f"{project_name}_fusion_workbook.xlsx"

    with pd.ExcelWriter(outfile, engine="openpyxl") as writer:

        # Writes empty EPIC sheet
        write_df_to_sheet(writer, pd.DataFrame(), **EPIC_SHEET_CONFIG)

        # Add SF previous runs data
        write_df_to_sheet(writer, df_sf_previous, **SF_PREVIOUS_RUNS_SHEET_CONFIG)

        # Add FI previous runs data
        write_df_to_sheet(writer, df_fi_previous, **FI_PREVIOUS_RUNS_SHEET_CONFIG)

        # Add FastQC data
        write_df_to_sheet(writer, df_fastqc, **FASTQC_SHEET_CONFIG)

        # Add STAR-Fusion data
        write_df_to_sheet(writer, df_starfusion, **STAR_FUSION_SHEET_CONFIG)

        # Add Fusion Inspector data
        write_df_to_sheet(writer, df_fusioninspector, **FUSION_INSPECTOR_SHEET_CONFIG)

        ### to do
        # add pivots

    fusion_workbook = dxpy.upload_local_file(outfile)

    output = {}
    output["fusion_workbook"] = dxpy.dxlink(fusion_workbook)

    return output


if __name__ == "__main__":
    dxpy.run()
