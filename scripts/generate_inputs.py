"""generates json inputs for eggd_fusion_workbook from given project
"""
import argparse
import json

import dxpy

SF_PATTERN = "*star-fusion.fusion_predictions.abridged.tsv"
FI_PATTERN = "*FusionInspector*.coding_effect*"
ARRIBA_PATTERN = "*_fusions.tsv"
MQC_PATTERN = "multiqc_*"


def parse_arguments() -> argparse.Namespace:
    """parses command line arguments"""
    parser = argparse.ArgumentParser(
        description="Generate input.json from DNAnexus project."
    )
    parser.add_argument("--project", "-p", required=True, help="DNAnexus project ID")

    return parser.parse_args()


def find_files(project_id: str, pattern: str) -> list:
    """finds files in given project matching pattern and retruns a list of dxlinks"""
    res = list(
        dxpy.find_data_objects(
            name=pattern,
            project=project_id,
            recurse=True,
            classname="file",
            name_mode="glob",
            describe={"fields": {"archivalState": True}},
        )
    )

    if not res:
        raise ValueError(
            f"No match found for {pattern} in {project_id}. "
            "Inputs can't be generated. Is this a PCAN project?"
        )

    print(f"Found {len(res)} {pattern} in {project_id}")
    assert all(
        x["describe"]["archivalState"] == "live" for x in res
    ), "Not all files are in 'live' state"

    return [{"$dnanexus_link": x["id"]} for x in res]


def main() -> None:
    """entry point"""
    args = parse_arguments()
    project_id = args.project

    inputs = {
        "starfusion_files": find_files(project_id, SF_PATTERN),
        "fusioninspector_files": find_files(project_id, FI_PATTERN),
        "arriba_files": find_files(project_id, ARRIBA_PATTERN),
        "multiqc_files": find_files(project_id, MQC_PATTERN),
        "SF_previous_runs_data": {"$dnanexus_link": "file-J18X5qj48F3V951v176vBq90"},
        "reference_sources": {"$dnanexus_link": "file-J18490j48F3b2zB4Z27KJJk4"},
        "previous_positives": {"$dnanexus_link": "file-J0fqQ8848F3bfj1XjfBQbx8x"},
    }

    with open("input.json", "w") as file:
        json.dump(inputs, file, indent=4)

    print("DONE")


if __name__ == "__main__":
    main()
