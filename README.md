# eggd_generate_fusion_workbook (DNAnexus Platform App)

## What does this app do?
Collates Fusion candidates and associated metadata from STAR-Fusion, FusionInspector and FastQC per run, then formats and generate a fusion workbook with collated data

## What inputs are required for this app to run?
- `-istarfusion_files` : An array of DNAnexus file IDs of STAR-Fusion's prediction files
- `-ifusioninspector_files` : An array of DNAnexus file IDs of FusionInspector's output files
- `-ifi_testdir_cosmic_files` : (optional) An array of DNAnexus file IDs of FusionInspector's output (testdir_cosmic) files
- `-ifi_rna_opa_files` : (optional) An array of DNAnexus file IDs of FusionInspector's output (rna_opa) files
- `-imultiqc_files`: An array of DNAnexus file IDs of MultiQC output metrics file
- `-iSF_previous_runs_data` : The DNAnexus file ID of a static file containing historical STAR-Fusion data
- `ireference_sources` : The DNAnexus file ID of a static file containing aggregated data source from COSMIC, FusionDGB2 and ChimerDB
- `iprevious_positives`: The DNAnexus file ID of a static file containing previously reported fusions

> [!NOTE]
> Currently, the `eggd_fusioninspector/1.1.0` app  produces three separate outputs: scientists, testdir_cosmic and rnaopa. The input field `fusioninspector_files` corresponds to the scientists output, while `fi_testdir_cosmic_files` and `fi_rna_opa_files` correspond to the latter two. However, in a future version of `eggd_fusioninspector`, these outputs will be merged into a single output, which will be used as the input for `fusioninspector_files`. As a result, the `fi_testdir_cosmic_files` and `fi_rna_opa_files` inputs are optional for now and will be deprecated once the update is released.

## How does this app work?
- Parses all inputs and format data according to structure of source data
- Writes formated data into a worksheet for each data source
- Writes a summary sheet using selected data from the different sources

## What does this app output?
- A Fusion Workbook named as `{project_name}_fusion_workbook.xlsx`

## Unit Testing
Unit tests are located in `resources/home/dnanexus/tests/`

Test modules include:
- `test_excel.py` – Excel utility formatting and helpers
- `test_parser.py` – Data parsing and transformation
- `test_utils.py` – Generic helpers and validation logic

### Run Tests Locally
It is recommended to use a virtual environment to manage dependencies:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

```

Then to run all tests in verbose mode:

```
pytest -v
```
Or to run a specific test file:

```
pytest -v resources/home/dnanexus/tests/test_parser.py
```