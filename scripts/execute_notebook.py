"""Execute the saved notebook from top to bottom using this Python environment."""
import asyncio
import json
import os
from pathlib import Path
import sys
import nbformat
from nbclient import NotebookClient

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT / ".runtime"
spec = runtime / "kernels/sdd-analysis"
spec.mkdir(parents=True, exist_ok=True)
(spec / "kernel.json").write_text(json.dumps({"argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
    "display_name": "SDD analysis validation", "language": "python"}), encoding="utf-8")
os.environ["JUPYTER_PATH"] = str(runtime) + os.pathsep + os.environ.get("JUPYTER_PATH", "")
os.environ["JUPYTER_RUNTIME_DIR"] = str(runtime / "run")
os.environ["MPLCONFIGDIR"] = str(runtime / "matplotlib")
path = ROOT / "notebooks/sdd_analysis.ipynb"
nb = nbformat.read(path, as_version=4)
NotebookClient(nb, timeout=180, kernel_name="sdd-analysis", allow_errors=False,
               resources={"metadata": {"path": str(ROOT)}}).execute()
nbformat.validate(nb)
code_cells = [c for c in nb.cells if c.cell_type == "code"]
assert all(c.execution_count is not None for c in code_cells)
assert not any(o.output_type == "error" for c in code_cells for o in c.outputs)
nbformat.write(nb, path)
summary = {"notebook": "notebooks/sdd_analysis.ipynb", "executed_code_cells": len(code_cells),
           "errors": 0, "python_executable": sys.executable, "nbformat_valid": True}
(ROOT / "results/notebook_execution.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
