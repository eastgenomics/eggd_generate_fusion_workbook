"""
Generates a static file input for eggd_generate_fusion_workbook;
Resulting file contains a mapping of fusion name to the number of times it has 
been called in all PANCAN runs
"""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import dxpy
import pandas as pd


def parse_arguments():
    """
    Parses command-line arguments
    """
    parser = argparse.ArgumentParser(
        description="generate and upload SF previous data."
    )
    parser.add_argument(
        "--project_id", required=True, help="DNAnexus project ID to upload the file to."
    )

    return parser.parse_args()


def get_project_ids(pattern: str = "002_.*_PCAN") -> list:
    """
    Retrieves all projects matching pattern

    Parameters
    ----------
    pattern : str
        regex pattern of project name to search for

    Returns
    -------
    list[str]
        A list of DNAnexus project ids
    """
    res = list(dxpy.find_projects(level="VIEW", name=pattern, name_mode="regexp"))
    return [x["id"] for x in res]


def find_sf_files(project_id: str) -> pd.DataFrame:
    """
    find file_names that matches "*star-fusion.fusion_predictions.abridged.tsv"
    (output from eggd_star_fusion containing called fusions) in given project

    Parameters
    ----------
    project_id : str
        DNAnexus project id to search for sf files

    Returns
    -------
    pd.DataFrame
        pandas dataframe containing file names, file ids and archival state
    """
    res = list(
        dxpy.find_data_objects(
            project=project_id,
            folder="/output/",
            recurse=True,
            name="star-fusion.fusion_predictions.abridged.tsv$",
            classname="file",
            name_mode="regexp",
            describe={"fields": {"name": True, "archivalState": True}},
        )
    )
    if not res:
        print(f"match not found in {project_id}")
        return pd.DataFrame()

    print(f"found {len(res)} matches in {project_id}")
    res = [
        {
            "project_id": x["project"],
            "file_id": x["id"],
            "name": x["describe"]["name"],
            "archival_state": x["describe"]["archivalState"],
        }
        for x in res
    ]

    return pd.DataFrame(res)


def check_archival_state(df: pd.DataFrame) -> None:
    """check archival state and unarchive if any

    Parameters
    ----------
    df : pd.Dataframe
        Pandas df containing DNAnexus project ids and file ids
    """
    # Subset df to unarchived
    df_archived = df[df["archival_state"].isin(["archived", "archival"])]

    if not df_archived.empty:
        print(f"{len(df_archived)}/{len(df)} files found are archived")

        # Group by 'project_id' to send unarchive request per project
        grouped = df_archived.groupby("project_id")["file_id"]

        for project_id, file_ids in grouped:

            response = dxpy.api.project_unarchive(project_id, {"files": list(file_ids)})
            print(response)

        print(f"\nUnarchive Request sent for {len(df_archived)} files")
        print("Please rerun script after a few hours. Exiting!...")
        sys.exit()

    # check for files still unarchiving
    df_unarchiving = df[df.archival_state == "unarchiving"]
    if not df_unarchiving.empty:
        print(f"{len(df_unarchiving)} files are still unarchiving")
        print("Please rerun script after a few hours. Exiting!...")
        sys.exit()


def read_sf_file(file_id: str, project: str) -> pd.DataFrame:
    """reads the content of DNAnexus file to a pandas df

    Parameters
    ----------
    file_id : str
        DNAnexus file ID
    project : str
        DNAnexus project containing file

    Returns
    -------
    pd.DataFrame
        pandas dataframe containing file content
    """
    with dxpy.open_dxfile(file_id, project) as dx_file:
        df = pd.read_csv(dx_file, sep="\t")
        df.insert(0, "file_name", dx_file.name)

    return df


def parse_fusion_files(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reads and concatenates a list of DNAnexus fusion-related files
    into a single DataFrame.

    Parameters
    ----------
    dxfiles : List[DXDataObject]
        A list of DNAnexus file objects.

    Returns
    -------
    pd.DataFrame
        A concatenated DataFrame containing the combined data
        from all input files.
    """
    # all files should be live at this point
    df = df[(df.archival_state == "live")]

    files = list(df.file_id)
    projects = list(df.project_id)
    args = zip(files, projects)

    with ThreadPoolExecutor(max_workers=32) as executor:
        df = pd.concat(
            list(executor.map(lambda x: read_sf_file(*x), args)), ignore_index=True
        )
    # save intermediate file for reference
    df.to_csv("pancan_sf_data.csv", index=False)
    return df


def upload_static_file(data: pd.DataFrame, project_id: str) -> None:
    """
     uploads file to DNAnexus.

    Parameters
    ----------
    data : pd.DataFrame
        File content to upload.
    project_id : str
        Destination to upload file to
    """
    date_str = datetime.now().strftime("%y%m%d")
    file_name = f"SF_Previous_Runs_{date_str}.tsv"

    data.to_csv(file_name, sep="\t", index=False)

    # uploaod to DNAnexus
    res = dxpy.upload_local_file(
        filename=file_name,
        project=project_id,
    )
    if res.id:
        print(f"Successfully uploaded {file_name} ({res.id}) to {project_id}")
    else:
        print("Error uploading file")


def generate_static_file() -> pd.DataFrame:
    """
    Generates SF static input from all eunomia runs

    Returns
    -------
    pd.DataFrame
        A pandas DataFrame containing fusion name and number of times it has
        been called
    """
    project_ids = get_project_ids()
    print(f"Total PCAN Projects: {len(project_ids)}")

    df = pd.concat([find_sf_files(proj) for proj in project_ids], ignore_index=True)

    check_archival_state(df)
    df = parse_fusion_files(df)

    # drop controls
    pattern = r"^\d+-\d+Q\d+-|RNA"
    df = df[~df["file_name"].str.contains(pattern)]

    # Count each unique fusion
    df_counts = df["#FusionName"].value_counts().reset_index()
    df_counts.columns = ["#FusionName", "Count_predicted"]

    # Add a special row for the number of samples used to generate this file
    # This is same as n unique file names;
    n_samples = df["file_name"].nunique()
    df_counts.loc[len(df_counts.index)] = ["#Samples", n_samples]

    # Sort alphabetically by Fusion, this ensure # comes first
    df_counts = df_counts.sort_values(by="#FusionName").reset_index(drop=True)

    return df_counts


def main():
    """Entry point to script"""
    args = parse_arguments()

    static_data = generate_static_file()

    upload_static_file(static_data, args.project_id)

    print("DONE.")


if __name__ == "__main__":
    main()
