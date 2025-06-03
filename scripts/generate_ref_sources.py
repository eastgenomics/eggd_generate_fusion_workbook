"""
Generate and upload a `ReferenceSources.tsv` file by aggregating fusion data
from multiple reference databases: COSMIC, FusionGDB2, and ChimerKB4.

This script reads fusion data from:
- A COSMIC `.tar` file Cosmic_Fusion_Tsv_v101_GRCh37.tar (file-GzvQx8j433Gz5Pj32jP17pzj),
- A FusionGDB2 `.txt` file (https://compbio.uth.edu/FusionGDB2/combined_tables/combinedFGDB2genes_genes_ID_04302024.txt), 
- A ChimerKB4 `.xlsx` file (https://www.kobic.re.kr/chimerdb/downloads?name=ChimerKB4.xlsx).

It standardizes the fusion identifiers, aggregates their source annotations, 
writes the result to a `.tsv` file, and uploads the file to DNAnexus.
"""

import argparse
import tarfile

import dxpy
import pandas as pd


def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments

    Returns
    -------
    argparse.Namespace
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="generate and upload ReferenceSource data."
    )
    parser.add_argument(
        "--project_id", required=True, help="DNAnexus project ID to upload the file to."
    )
    parser.add_argument(
        "--cosmic", required=True, help="Path to COSMIC source file (.tar)"
    )
    parser.add_argument(
        "--chimerkb4", required=True, help="Path to ChimerKB4 source file (.xlsx)"
    )
    parser.add_argument(
        "--fusiongdb2", required=True, help="Path to FusionGDB2 source file (.txt)"
    )
    return parser.parse_args()


def read_cosmic(tar_path: str) -> pd.DataFrame:
    """
    Extracts and reads the COSMIC fusion data from a .tar archive.

    Parameters
    ----------
    tar_path : str
        Path to the COSMIC .tar file containing a gzipped TSV.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ['Fusion', 'ReferenceSources']
    """

    with tarfile.open(tar_path, "r") as tar:
        fname = "Cosmic_Fusion_v101_GRCh37.tsv.gz"
        req_cols = ["FIVE_PRIME_GENE_SYMBOL", "THREE_PRIME_GENE_SYMBOL"]
        
        try:
            member = tar.getmember(fname)
            f = tar.extractfile(member)
        except KeyError:
            raise ValueError(f"Expected {fname} not in COSMIC tar")

        df = pd.read_csv(f, sep="\t", compression="gzip")
        missing_cols = [col for col in req_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        fusions = df.FIVE_PRIME_GENE_SYMBOL + "--" + df.THREE_PRIME_GENE_SYMBOL
        print(f"COSMIC: {len(set(fusions))} unique fusions")

        return pd.DataFrame({"Fusion": fusions, "ReferenceSources": "COSMIC"})


def read_chimerkb4(file_path: str) -> pd.DataFrame:
    """
    Reads fusion data from the ChimerKB4 Excel file.

    Parameters
    ----------
    file_path : str
        Path to the ChimerKB4 Excel file.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ['Fusion', 'ReferenceSources'].
    """

    df = pd.read_excel(file_path)

    # Replace '-' with '--' in fusion column
    if "Fusion_pair" not in df.columns:
        raise ValueError(f"Missing 'Fusion_pair' col in ChimerKB4 data")
    
    fusions = df["Fusion_pair"].str.replace("-", "--")
    print(f"ChimerKB4: {len(set(fusions))} unique fusions")

    return pd.DataFrame({"Fusion": fusions, "ReferenceSources": "ChimerKB4"})


def read_fusiongdb2(file_path: str) -> pd.DataFrame:
    """
    Reads fusion data from FusionGDB2 tab-delimited text file.

    Parameters
    ----------
    file_path : str
        Path to the FusionGDB2 file.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ['Fusion', 'ReferenceSources'].
    """
    df = pd.read_csv(file_path, sep="\t", header=None)

    # Extract the second column (fusion names)
     if len(df.columns) < 2:
         raise ValueError("FusionGDB2 file must have at least 2 columns")
     
    fusions = df[1].str.replace("-", "--")
    print(f"FusionGDB2: {len(set(fusions))} unique fusions")

    return pd.DataFrame({"Fusion": fusions, "ReferenceSources": "FusionGDB2"})


def generate_ref_source(cosmic: str, fusiongdb2: str, chimerkb4: str) -> str:
    """
    Aggregates fusions from their sources and saves to a TSV file.

    Parameters
    ----------
    cosmic : str
        Path to the COSMIC .tar file.
    fusiongdb2 : str
        Path to the FusionGDB2 .txt file.
    chimerkb4 : str
        Path to the ChimerKB4 .xlsx file.

    Returns
    -------
    str
        Path to the output TSV file.
    """

    # Combine all into one DataFrame
    df = pd.concat(
        [read_cosmic(cosmic), read_fusiongdb2(fusiongdb2), read_chimerkb4(chimerkb4)]
    )

    # Group by Fusion and aggregate sources
    fusion_sources = (
        df.groupby("Fusion")["ReferenceSources"]
        .apply(lambda x: ",".join(sorted(set(x))))
        .reset_index()
    )
    outfile = "ReferenceSources.tsv"
    fusion_sources.to_csv(outfile, sep="\t", index=False)
    print(f"Combined: {len(fusion_sources)} unique fusions saved to {outfile}")

    return outfile


def main():
    """Entry point"""

    args = parse_arguments()

    static_file = generate_ref_source(args.cosmic, args.fusiongdb2, args.chimerkb4)

    res = dxpy.upload_local_file(
        filename=static_file,
        project=args.project_id,
    )
    print(f"Successfully uploaded {static_file} ({res.id}) to {args.project_id}")


if __name__ == "__main__":
    main()
