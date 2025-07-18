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
    FI_SHEET_CONFIG,
    ARRIBA_SHEET_CONFIG,
    SF_PREVIOUS_RUNS_SHEET_CONFIG,
    SF_SHEET_CONFIG,
    FASTQC_PIVOT_CONFIG,
    SF_PIVOT_CONFIG,
    PREV_POS_SHEET_CONFIG,
    REF_SOURCES_SHEET_CONFIG,
)
from utils.excel import format_workbook, write_df_to_sheet, add_extra_columns
from utils.parser import (
    parse_fastqc,
    parse_fusion_inspector,
    parse_star_fusion,
    parse_arriba,
    make_fastqc_pivot,
    make_sf_pivot,
    parse_sf_previous,
    parse_prev_pos,
)
from utils.summary_sheet import write_summary
from utils.utils import (
    get_project_info,
    read_dxfile,
    get_dxfile,
)


@dxpy.entry_point("main")
def main(
    starfusion_files: List[dict],
    fusioninspector_files: List[dict],
    arriba_files: List[dict],
    multiqc_files: List[dict],
    SF_previous_runs_data: dict,
    reference_sources: dict,
    previous_positives: dict,
):
    """Generates a fusion workbook with data from
    STAR-Fusion, FusionInspector, Arriba, and FastQC

    Parameters
    ----------
    starfusion_files : List[dict]
        List of dictionaries containing DXLinks to STAR-Fusion output files
    fusioninspector_files : List[dict]
        List of dictionaries containing DXLinks to FusionInspector output files
    arriba_files : List[dict]
        List of dictionaries containing DXLinks to Arriba output files
    multiqc_files : List[dict]
        List of dictionaries containing DXLinks to MultiQC output files
    SF_previous_runs_data : dict
       Mapping of DXLink to STAR-Fusion previous runs data file
    reference_sources : dict
       Mapping of DXLink to ReferenceSources file
    previous_positives : dict
       Mapping of DXLink to PreviousPositives file

    Returns
    -------
    dict
        Dictionary containing DXLink to the generated fusion workbook
    """
    # Initialize inputs into dxpy.DXDataObject instances
    starfusion_files = [dxpy.DXFile(item) for item in starfusion_files]
    fusioninspector_files = [dxpy.DXFile(item) for item in fusioninspector_files]
    arriba_files = [dxpy.DXFile(item) for item in arriba_files]
    multiqc_files = [dxpy.DXFile(item) for item in multiqc_files]
    fastqc_data = get_dxfile(multiqc_files, "multiqc_fastqc.txt")
    sf_previous_data = dxpy.DXFile(SF_previous_runs_data)
    ref_sources = dxpy.DXFile(reference_sources)
    previous_positives = dxpy.DXFile(previous_positives)

    df_starfusion = parse_star_fusion(starfusion_files)
    df_fusioninspector = parse_fusion_inspector(fusioninspector_files)
    df_arriba = parse_arriba(arriba_files)
    df_fastqc = parse_fastqc(fastqc_data)
    df_sf_previous = parse_sf_previous(sf_previous_data)
    df_ref_sources = read_dxfile(ref_sources, include_fname=False)
    df_prev_pos = parse_prev_pos(previous_positives)

    project_name, _ = get_project_info()
    outfile = f"{project_name}_fusion_workbook.xlsx"

    with pd.ExcelWriter(outfile, engine="openpyxl") as writer:

        # Writes empty EPIC sheet
        write_df_to_sheet(writer, pd.DataFrame(), **EPIC_SHEET_CONFIG)

        # Writes RefSources sheet
        write_df_to_sheet(writer, df_ref_sources, **REF_SOURCES_SHEET_CONFIG)

        # Writes PreviousPositives sheet
        write_df_to_sheet(writer, df_prev_pos, **PREV_POS_SHEET_CONFIG)

        # Add SF previous runs data
        write_df_to_sheet(writer, df_sf_previous, **SF_PREVIOUS_RUNS_SHEET_CONFIG)

        # Add FastQC data
        write_df_to_sheet(writer, df_fastqc, **FASTQC_SHEET_CONFIG)
        fastqc_pivot = make_fastqc_pivot(df_fastqc, FASTQC_PIVOT_CONFIG)
        write_df_to_sheet(
            writer,
            fastqc_pivot,
            sheet_name=FASTQC_PIVOT_CONFIG["sheet_name"],
            tab_color=FASTQC_PIVOT_CONFIG["tab_color"],
            extra_cols=FASTQC_PIVOT_CONFIG["extra_cols"],
            start_col=FASTQC_PIVOT_CONFIG["start_col"],
        )
        # Add Fusion Inspector data
        write_df_to_sheet(writer, df_fusioninspector, **FI_SHEET_CONFIG)

        # Add Arriba data
        write_df_to_sheet(writer, df_arriba, **ARRIBA_SHEET_CONFIG)

        # Add STAR-Fusion data
        write_df_to_sheet(writer, df_starfusion, **SF_SHEET_CONFIG)
        sf_pivot = make_sf_pivot(
            df_starfusion,
            df_sf_previous,
            fastqc_pivot,
            df_fusioninspector,
            df_prev_pos,
            df_ref_sources,
            SF_PIVOT_CONFIG,
        )
        write_summary(writer, sf_pivot, SF_PIVOT_CONFIG)
        format_workbook(writer)

    fusion_workbook = dxpy.upload_local_file(outfile)

    output = {}
    output["fusion_workbook"] = dxpy.dxlink(fusion_workbook)

    return output


if __name__ == "__main__":
    dxpy.run()
