# MoM Automation Pipeline POC

## Architecture
A Python-based data pipeline that isolates unstructured NLP parsing from tabular data operations. The system joins MS Teams attendance logs (via Pandas) with LLM-generated structured meeting data (JSON), injecting the merged payload into `.docx` files via XML node patching (`docxtpl`).

## 1. Functional Requirements

### 1.1 Tabular Data Operations (Attendance)
* **Data Truncation:** MS Teams UTF-16 CSV exports append irregular tables (e.g., "In-Meeting Activities") below the primary participant list. The parser truncates the dataframe at the first `NaN` instance in the `Email` column to drop all trailing artifact data.
* **Relational Joins:** Attendance mapping executes a Left Join on the `Email` column against a static Master Directory. String matching on `Name` is strictly avoided to prevent mismatch errors. Strings are normalized (`.str.strip().str.lower()`) prior to joining.
* **Null Handling:** Unmatched participant records default to `Designation: External / Unknown` and `Abbreviation: EXT`.

### 1.2 Unstructured Data Ingestion (LLM)
* **Payload Constraints:** LLM output is restricted to strictly formatted JSON. The output keys (e.g., `matters`, `scorecards`) must exactly map to the Jinja2 variables defined in the target `.docx` templates.

### 1.3 XML Templating
* **View/Logic Separation:** All styling, branding, and layout are maintained within the `.docx` file. The Python script handles zero formatting.
* **Node Manipulation:** `docxtpl` processes Jinja2 control structures to duplicate Word XML elements. Table loops rely on exact regex matching (`{%tr ... %}`) to duplicate `<w:tr>` (table row) nodes safely without fracturing the surrounding document schema.

## 2. Execution Guide

### Dependencies
Ensure the environment contains the required packages:
```bash
pip install -r requirements.txt
```

### Required File Structure
├── Input/
│   ├── directory.csv                 # Master directory (Name, Email, Designation, Abbrev)
│   ├── Teams_Attendance.csv          # Raw UTF-16 export from MS Teams
│   └── transcript_data.json          # Mocked LLM JSON payload containing meeting metadata
├── MoM_Template.docx                 # Target Word document mapped with Jinja2 tags
├── debug.py                          # XML artifact cleanup functions
└── pipeline.py                       # Main orchestration script

### Process Flow
Execute the POC script:
```bash
python PSC.py
```
1. **Extract & Join**: Isolates the active attendance block and merges it with the Master Directory.
2. **Aggregate Payload**: Appends the verified attendance dictionary to the JSON context payload.
3. **Render & Clean**: Opens the `.docx`, executes a backward-iterating cleanup of fractured XML text runs (via `debug.py`), and renders the variables.
4. **Output**: The final synthesized document is generated at `Output/Final_MoM_Document.docx`.

## Strategic Roadmap

To transition this POC into a production-grade enterprise application, the following modules must be engineered:

* **Schema Validation Layer**: Implement `Pydantic` or `Instructor` to enforce strict type checking on the raw LLM JSON output. This layer will catch malformed schemas or markdown artifacts (e.g., ```json) and trigger an automated API retry.

* **Absence Flagging** (`Attended: N`): MS Teams CSV logs only capture active participants. Integrate the MS Graph API to extract the original calendar invite manifest. Executing an Outer Join against the Teams CSV will allow the system to dynamically flag invited but absent personnel.

* **Enterprise LLM Endpoint Integration**: Replace the local `transcript_data.json` mock with an authenticated REST call to a secure enterprise LLM endpoint, ensuring zero-retention policies for sensitive meeting transcripts.

* **Dynamic Template Selector**: Implement conditional routing logic that parses the `TYPE_OF_MEETING` variable from the initial JSON payload and dynamically loads the corresponding `.docx` governance template.