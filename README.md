# eggd_generate_fusion_workbook (DNAnexus Platform App)

## What does this app do?
Collates Fusion candidates and associated metadata from STAR-Fusion, FusionInspector and FastQC per run, then formats and generate a fusion workbook with collated data

## What inputs are required for this app to run?
- `-istarfusion_files` : An array of DNAnexus file IDs of STAR-Fusion's prediction files
- `-ifusioninspector_files` : An array of DNAnexus file IDs of FusionInspector's output files
- `-fi_testdir_cosmic_files` : (optional) An array of DNAnexus file IDs of FusionInspector's output (testdir_cosmic) files
- `-ifi_rna_opa_files` : (optional) An array of DNAnexus file IDs of FusionInspector's output (rna_opa) files
- `-imultiqc_files`: An array of DNAnexus file IDs of MultiQC output metrics file
- `-iSF_previous_runs_data` : The DNAnexus file ID of a static file containing historical STAR-Fusion data
- `ireference_sources` : The DNAnexus file ID of a static file containing aggregated data source from COSMIC, FusionDGB2 and ChimerDB
- `iprevious_positives`: The DNAnexus file ID of a static file containing previously reported fusions

## How does this app work?
- Parses all inputs and format data according to structure of source data
- Writes formated data into a worksheet for each data source
- Writes a summary sheet using selected data from the different sources

## What does this app output?
- A Fusion Workbook named as `{project_name}_fusion_workbook.xlsx`

#### TODO
- Add unit tests
- Add scripts to generate static inputs
- Add more validations to parser module