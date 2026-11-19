# Resume Extraction System

A Python command-line pipeline that extracts structured candidate information from plain-text resumes using OpenAI. It validates model responses with a Pydantic schema and exports individual JSON files, consolidated Excel workbooks, and a Markdown run summary.

## Features

- Batch processing of UTF-8 `.txt` resumes from a configured folder.
- Structured extraction with an evidence explanation for each field.
- Separate raw API responses and parsed candidate records.
- Excel exports for successful records and per-candidate errors.
- Timestamped output folders and run statistics.
- YAML configuration for input, output, model, and retry settings.
- Retry handling for selected transient API errors (see [Known limitations](#known-limitations) before use).

## Extracted information

| Field | Description |
| --- | --- |
| `name` | Candidate name |
| `email` | Email address |
| `phone` | Phone number |
| `current_location` | Current location |
| `total_experience` | Total experience, excluding gaps |
| `releant_experience` | Experience related to technical fields, as defined in the schema |
| `current_job_title` | Current or most recent job title |
| `current_company` | Current or most recent employer |
| `highest_education` | Bachelor's Degree, Master's Degree, Doctorate, Diploma, Other, or Not Specified |
| `notice_period` | Notice period in days |

Each field has a corresponding reasoning field. The relevant-experience value is currently spelled `releant_experience` in the schema; its explanation is named `relevant_experience_reasoning`. The consolidated results workbook also includes `cand_id`, derived from the input filename.

## How it works

```text
Text resumes -> Load and validate text -> Build prompt -> OpenAI structured response
                                                        |
                                                        v
                              Raw JSON + Parsed JSON + Excel + Run summary
```

Files are processed sequentially. A failure for one candidate is recorded, and processing continues with the remaining resumes.

## Setup

### 1. Prepare Python

Use Python 3.12 or later: the current logging code uses f-string syntax introduced in Python 3.12. Open a terminal in the repository root and create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or on macOS/Linux:

```bash
source .venv/bin/activate
```

### 2. Install runtime dependencies

```bash
python -m pip install openai "pydantic>=2" PyYAML pandas openpyxl
```

The checked-in `requirements.txt` is a full environment export containing machine-specific `file:///` paths and unrelated packages. Use the runtime dependency command above for a fresh environment; a portable, pinned dependency file is still needed for reproducible installs.

### 3. Set the API key

Set the environment variable in the terminal where you will run the pipeline.

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY = "your-api-key"
```

macOS/Linux:

```bash
export OPENAI_API_KEY="your-api-key"
```

The application reads the process environment with `os.getenv()`. It does **not** load `.env` files automatically.

### 4. Configure paths and model

Edit [`config/config.yaml`](config/config.yaml). For example:

```yaml
project_name: resume_extraction

input:
  source_path: data/new_resumes

output:
  output_path: output

llm:
  api_key: OPENAI_API_KEY
  provider: openai
  model: gpt-5.4-mini

retry:
  max_attempts: 3
  initial_delay: 2
  max_delay: 30
```

Replace the checked-in absolute Windows output path with a location on your machine, such as `output`. Relative paths resolve from the current working directory. `llm.api_key` names the environment variable, rather than containing the key itself. The model above matches the checked-in configuration; select a model available to your account that supports the structured-response call used in `src/llm_client.py`.

`main.py` loads `config/config.yaml`; the duplicate `src/config.yaml` is not used by the entry point. The client is currently hardcoded to OpenAI, so changing `provider` only changes the value recorded in the run summary.

### 5. Prepare resumes and address the startup issue

Place one resume per UTF-8 `.txt` file directly inside the configured input folder. For example, `CAND001.txt` becomes candidate ID `CAND001`. Subfolders are not scanned. PDF and DOCX inputs must first be converted to text outside this application.

Before the first run, remove the module-level sample `load_data(...)` call and `print(text)` at the bottom of [`src/data_loader.py`](src/data_loader.py), or move them under an `if __name__ == "__main__":` guard. They currently execute during import and attempt to read a file from the original developer's Desktop, which can prevent startup on other machines.

## Run

After completing setup and the startup correction above, run from the repository root:

```bash
python main.py
```

The console reports candidate IDs, API attempts, errors, and final processing counts. API calls require network access and may incur usage charges. Resume text is sent to OpenAI for extraction.

## Output

With `output_path: output` and `project_name: resume_extraction`, each run creates:

```text
output/
└── resume_extraction_<YYYYMMDD_HHMMSS>/
    ├── raw/
    │   └── CAND001_raw.json
    ├── parsed/
    │   └── CAND001_parsed.json
    ├── results_<YYYYMMDD_HHMMSS>.xlsx
    ├── errors_<YYYYMMDD_HHMMSS>.xlsx
    └── logs/
        └── logs.md
```

- **Raw JSON:** Full serialized API response for each successful response saved by the pipeline.
- **Parsed JSON:** Extracted fields and explanations for each successfully parsed resume.
- **Results workbook:** Consolidated successful records, including `cand_id`.
- **Errors workbook:** Candidate IDs and error messages for failed records.
- **Run summary:** Provider, model, totals, successful and failed counts, elapsed time, and export status.

## Project structure

```text
Resume-Extraction-System/
├── config/config.yaml      # Configuration loaded by main.py
├── data/
│   ├── new_resumes/         # Default input folder
│   └── resumes/             # Additional resume files
├── src/
│   ├── config.yaml         # Duplicate configuration; unused by main.py
│   ├── config_loader.py    # YAML loading
│   ├── data_loader.py      # Text-file loading and validation
│   ├── data_saver.py       # JSON, Excel, and Markdown output
│   ├── llm_client.py       # OpenAI structured-response call
│   ├── models.py           # Pydantic extraction schema
│   ├── processor.py        # Batch processing and output orchestration
│   ├── prompt_builder.py   # System and resume prompts
│   └── retry_handler.py    # API retry handling
├── main.py                 # Entry point
├── requirements.txt        # Existing full environment export
├── LICENSE
└── README.md
```

## Known limitations

- **Retry calculation:** `src/retry_handler.py` currently passes a tuple into the delay calculation, causing a `TypeError` when a retryable error occurs before the final attempt. The intended expression is `min(initial_delay * (2 ** (attempt - 1)), max_delay)`.
- **Missing values:** The prompt requests `Not Available` for absent information, but numeric fields and the education enum cannot accept that string. Incomplete resumes may therefore cause validation failures or unreliable extracted values.
- **Run status:** The summary's `status` reflects Excel export success; candidate failures are reported separately. Check the failed count and errors workbook even when the status is `successful`.
- **Exit status:** `main.py` catches exceptions and prints `Pipeline Failed: ...` without explicitly returning a nonzero exit code. Automated workflows should not rely on the process exit code alone.
- **Accuracy:** Schema validation checks response structure, not factual correctness. Review extracted information before using it.

## Publishing and contributing

Use synthetic or anonymized resumes in public examples. Review the files already tracked under `data/` before publishing, and keep API credentials and generated candidate outputs out of version control.

Contributions can be proposed through issues and pull requests. Useful improvements include portable dependency pins, fixes for the limitations above, automated tests, and additional input formats.

## License

This project is licensed under the [MIT License](LICENSE).
