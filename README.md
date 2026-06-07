
# Nueva SE Swiss Knife (PyQt6 Edition)

Nueva SE Swiss Knife is a cross-platform desktop developer utility suite rebuilt on top of **Python 3** and the **PyQt6** framework. It bridges robust, multi-threaded background processing engines with an industrial, operating-system-native GUI workspace.

The application uses Qt's underlying hardware abstraction layers, ensuring stable initialization across all graphics architectures (including discrete AMD Radeon setups) without driver timing conflicts.

---

## 🛠️ Features

* **Folder Comparator:** High-speed parallel workspace layout diffing engine showing comparative structural trees, line changes, structural exclusion filters, and exact hash matching.
* **Text Searcher:** Multi-threaded regular expression index engine scanning deep filesystems with real-time UI text streaming and cancellation safety hooks.
* **Code Formatter:** Direct code snippet stream buffer formatting with syntax configuration parsing supporting languages like Python, JS, HTML, JSON, and SQL.

---

## 📂 Project Architecture

To ensure your utilities are discovered correctly by PyQt6's module resolution system, structure your workspace layout as follows:

```text
nueva-se-swiss-knife/
│
├── utils/
│   ├── __init__.py
│   └── logger.py          # Centralized tracking & rotating log engine
│
├── comparator.py          # Logical directory comparison matrix
├── formatter.py           # Auto-detection syntax configuration parser
├── searcher.py            # Deep-scanning regex index engine
├── main.py                # PyQt6 Desktop Application & Worker Thread UI
└── requirements.txt       # Dependency manifest file

```

---

## 🚀 Setting Up the Environment

### 1. Prerequisites

Ensure you have **Python 3.9 through 3.12** installed on your desktop workstation.

### 2. Isolate with a Virtual Environment

Navigate to your project root folder and build an isolated sandbox environment:

```bash
# Enter the project root
cd nueva-se-swiss-knife

# Initialize virtual environment
python -m venv venv

# Activate the environment:
# On Windows (Command Prompt):
venv\Scripts\activate
# On Windows (PowerShell):
.\venv\Scripts\activate
# On macOS / Linux:
source venv/bin/activate

```

### 3. Install Required Dependencies

PyQt6 bundles its window manager and graphics bindings securely. Run the following command to update your package pipeline and pull down PyQt6:

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install PyQt6

```

*(Note: If your underlying backend scripts rely on command-line utility formatters such as `black`, `jsbeautifier`, or `sqlparse`, ensure they are installed via pip into this exact virtual environment as well.)*

---

## 💻 Running the Application

With your Python virtual environment active, spin up the main desktop controller:

```bash
python main.py

```

---

## 📦 Building Standalone Executables (.exe / .app)

To compile the PyQt6 application into a unified standalone distribution binary that users can launch without installing Python, leverage **PyInstaller**.

### 1. Install PyInstaller

```bash
pip install pyinstaller

```

### 2. Run the Compilation Pipeline

Because PyQt6 natively maps system windows instead of injecting custom raw canvas render pipelines (like Kivy), compilation requires fewer explicit runtime hooks:

```bash
pyinstaller --noconsole --onefile --name="Nueva_SE_Swiss_Knife" main.py

```

* **`--noconsole`**: Suppresses the background terminal command prompt window when the GUI fires up.
* **`--onefile`**: Bundles your scripts, resources, and binary assets into a single cohesive execution asset.

Once PyInstaller finishes:

* The deployment-ready executable can be grabbed immediately inside the **`dist/`** directory.
* The matching `build/` folder and `.spec` files can safely be removed.

```

