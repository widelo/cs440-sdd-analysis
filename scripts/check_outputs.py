"""Check saved analysis artifacts and create a figure contact sheet for visual QA."""
from hashlib import sha256
import json
from pathlib import Path

import nbformat
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
results = ROOT / "results"
manifest = json.loads((results / "figure_manifest.json").read_text(encoding="utf-8"))
audit = json.loads((results / "validation_report.json").read_text(encoding="utf-8"))
assert len(manifest) == 14
assert {str(p.relative_to(ROOT)).replace("\\", "/") for p in (ROOT / "figures").glob("*.png")} == {
    row["figure"].replace("\\", "/") for row in manifest}
sheet = Image.new("RGB", (1680, 5 * 440), "#eeeeee")
draw = ImageDraw.Draw(sheet)
for i, row in enumerate(manifest):
    path = ROOT / row["figure"]
    with Image.open(path) as im:
        assert min(im.size) >= 1400, (path, im.size)
        assert all(abs(dpi - 300) < 1 for dpi in im.info["dpi"]), (path, im.info)
        im = im.convert("RGB")
        im.thumbnail((550, 405))
        x, y = (i % 3) * 560, (i // 3) * 440
        draw.text((x + 5, y + 3), path.stem, fill="black")
        sheet.paste(im, (x + (560 - im.width) // 2, y + 25))
for filename, digest in audit["input_sha256"].items():
    assert sha256((ROOT / "data" / filename).read_bytes()).hexdigest() == digest, filename
nb = nbformat.read(ROOT / "notebooks/sdd_analysis.ipynb", as_version=4)
nbformat.validate(nb)
code = [c for c in nb.cells if c.cell_type == "code"]
assert all(c.execution_count is not None for c in code)
assert [c.execution_count for c in code] == list(range(1, len(code) + 1))
assert not any(o.output_type == "error" for c in code for o in c.outputs)
images = sum("image/png" in o.get("data", {}) for c in code for o in c.outputs)
assert images == 14, images
interpretations = sum("**Interpretation.**" in o.get("data", {}).get("text/markdown", "")
                      for c in code for o in c.outputs)
assert interpretations == 14, interpretations
(ROOT / ".runtime").mkdir(exist_ok=True)
sheet.save(ROOT / ".runtime/figure_contact_sheet.png")
report = {"figures": len(manifest), "png_dpi": 300, "executed_notebook_cells": len(code),
          "embedded_figures": images, "markdown_interpretations": interpretations,
          "notebook_errors": 0, "input_fingerprints_unchanged": True, "status": "passed"}
(results / "output_checks.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
