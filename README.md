# Technical Consulting Toolbox

A Streamlit-based multi-page utility for:

* **Historical Export**: Export employee history data into CSV files.
* **Zipper**: Compress folders and pictures into ZIP archives.
* **Document Export**: Count and download employee documents (single, multiple, photo).
* **Field Overview**: Export an Excel-file with fields from Employees, Lists and Organizations.

---

## Prerequisites

* Python 3.11+
* Git

---

## Installation

1. **Clone the repo**

   ```bash
   git clone https://github.com/your-org/tc-toolbox.git
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

## License

MIT © reriksson
