# Technical Consulting Tool-Box

A Streamlit-based multi-page utility for:

* **Historical CSV Export**: Export employee history data into CSV files.
* **Folder Zipper**: Compress first-level numeric folders into ZIP archives.
* **Document Export**: Count and download employee documents (single, multiple, photo).

---

## Features

1. **Historical Export**

   * Connects to the CatalystOne Mono API.
   * Select domain, client credentials, output folder, and history start date.
   * Choose identifier field (Profile ID, Employee ID, or E-mail) and select custom fields to export.
   * Generates CSVs (semicolon-delimited) with timeline history and optional `Valid To` filtering.

2. **Folder Zipper**

   * Input a root folder containing subdirectories named by an unique identifier.
   * Creates ZIP archives for each numeric subfolder.
   * Outputs in a separate folder and shows a summary of processed, compressed, and failed operations.

3. **Document Export**

   * Load API fields of type `Photo`, `DocumentSingle`, and `DocumentMultiple`.
   * Select fields to process.
   * Choose an identifier (Username, Profile ID, Employee ID, E-mail) to name employee subfolders.
   * Count the number of documents per type, and download them into `output_folder/<FieldName>/<Identifier>/` subdirectories.
   * Supports Base64 decoding and dynamic progress counters.

---

## Prerequisites

* Python 3.11+
* Git

---

## Installation

1. **Clone the repo**

   ```bash
   git clone https://github.com/your-org/technical-consulting-multi-tool.git
   cd technical-consulting-multi-tool
   ```

2. **Create a virtual environment**

   ```bash
   python3.11 -m venv venv
   source venv/bin/activate   # macOS/Linux
   venv\\Scripts\\activate   # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## Running the App

```bash
streamlit run app.py
```

* Opens in your default browser at `http://localhost:8501`.
* Use the **Start** page to navigate between tools.

---

## Configuration

All API-related pages require:

* **Domain**: e.g., `reriksson.sb` to form `https://<domain>.catalystone.com/mono/api`.
* **Client ID** and **Client Secret**: Credentials for the CatalystOne Mono API.
* **Include inactive employees**: Toggle to include/exclude.

Supply the settings via the input fields on each page.

---

## Project Structure

```
STREAMLIT/
├── app.py                # Main app launcher and page router
├── requirements.txt      # Python dependencies
├── main/
│   ├── utils.py          # Shared helper functions (token, fetch, zip)
│   └── pages/
│       ├── start.py
│       ├── historical_export.py
│       ├── zipper.py
│       └── document_export.py
└── README.md             # This file
```

---

## License

MIT © reriksson
