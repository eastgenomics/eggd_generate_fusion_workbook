#!/usr/bin/env python3
# eggd_generate_fusion_workbook 1.0.0

import os
from glob import glob
import subprocess
from typing import List

if os.path.exists("/home/dnanexus"):
    # running in DNAnexus
    subprocess.check_call(
        ["pip", "install", "--no-index", "--no-deps"] + glob("packages/*")
    )

import dxpy
import openpyxl
import pandas as pd
from utils.defaults import (
    EPIC_SHEET_CONFIG,
    FASTQC_SHEET_CONFIG,
    FI_PREVIOUS_RUNS_SHEET_CONFIG,
    FI_SHEET_CONFIG,
    SF_PREVIOUS_RUNS_SHEET_CONFIG,
    SF_SHEET_CONFIG,
    FASTQC_PIVOT_CONFIG,
    SF_PIVOT_CONFIG,
)
from utils.parser import (
    parse_fastqc,
    parse_fusion_inspector,
    parse_star_fusion,
    make_fastqc_pivot,
    make_sf_pivot,
)
from utils.utils import (
    get_project_info,
    read_dxfile,
    write_df_to_sheet,
    highlight_max_ffpm,
)


@dxpy.entry_point("main")
def main(
    starfusion_files: List[dict],
    fusioninspector_files: List[dict],
    fastqc_data: dict,
    SF_previous_runs_data: dict,
    FI_previous_runs_data: dict,
):
    """Generates a fusion workbook with data from
    STAR-Fusion, FusionInspector, and FastQC

    Parameters
    ----------
    starfusion_files : List[dict]
        List of dictionaries containing DXLinks to STAR-Fusion output files
    fusioninspector_files : List[dict]
        List of dictionaries containing DXLinks to FusionInspector output files
    fastqc_data : dict
        Mapping of DXLink to FastQC data file
    SF_previous_runs_data : str
       Mapping of DXLink to STAR-Fusion previous runs data file
    FI_previous_runs_data : str
        Mapping of DXLink to FusionInspector previous runs data file

    Returns
    -------
    dict
        Dictionary containing DXLink to the generated fusion workbook
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

    df_sf_previous = read_dxfile(sf_previous_data, include_fname=False)
    df_fi_previous = read_dxfile(fi_previous_data, sep=",", include_fname=False)

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
        fastqc_pivot = make_fastqc_pivot(df_fastqc, FASTQC_PIVOT_CONFIG)
        write_df_to_sheet(
            writer,
            fastqc_pivot,
            sheet_name=FASTQC_PIVOT_CONFIG["sheet_name"],
            tab_color=FASTQC_PIVOT_CONFIG["tab_color"],
        )

        # Add Fusion Inspector data
        write_df_to_sheet(writer, df_fusioninspector, **FI_SHEET_CONFIG)

        # Add STAR-Fusion data
        write_df_to_sheet(writer, df_starfusion, **SF_SHEET_CONFIG)
        sf_pivot = make_sf_pivot(
            df_starfusion,
            df_sf_previous,
            fastqc_pivot,
            df_fusioninspector,
            SF_PIVOT_CONFIG,
        )
        write_df_to_sheet(
            writer,
            sf_pivot,
            sheet_name=SF_PIVOT_CONFIG["sheet_name"],
            tab_color=SF_PIVOT_CONFIG["tab_color"],
            include_index=True,
        )
        summary_sheet = writer.sheets[SF_PIVOT_CONFIG["sheet_name"]]
        highlight_max_ffpm(summary_sheet, sf_pivot)

    fusion_workbook = dxpy.upload_local_file(outfile)

    output = {}
    output["fusion_workbook"] = dxpy.dxlink(fusion_workbook)

    return output


if __name__ == "__main__":
    dxpy.run()
