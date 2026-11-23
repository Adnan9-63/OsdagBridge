import subprocess
import os
import sys
from pathlib import Path

script_dir = Path(__file__).resolve().parent

pdflatex_bin = "pdflatex"
try:
    import importlib
    module = importlib.import_module("osdag_latex_env.__main__")
    latex_env = getattr(module, "OsdagLatexEnv")()
    if latex_env.pdflatex:
        pdflatex_bin = str(latex_env.pdflatex)
    if latex_env.bin_dir:
        os.environ["PATH"] = str(latex_env.bin_dir) + os.pathsep + os.environ.get("PATH", "")
except Exception:
    pass

env = os.environ.copy()
print(f"Using compiler: {pdflatex_bin}")
print("Starting Pass 1...")
res1 = subprocess.run(
    [pdflatex_bin, "-interaction=nonstopmode", "OsdagBridge_Testing_Report.tex"],
    cwd=script_dir,
    env=env,
    stdin=subprocess.DEVNULL,
    capture_output=True,
    text=True,
    errors="replace"
)
print("Pass 1 return code:", res1.returncode)

print("Starting Pass 2...")
res2 = subprocess.run(
    [pdflatex_bin, "-interaction=nonstopmode", "OsdagBridge_Testing_Report.tex"],
    cwd=script_dir,
    env=env,
    stdin=subprocess.DEVNULL,
    capture_output=True,
    text=True,
    errors="replace"
)
print("Pass 2 return code:", res2.returncode)

pdf_file = script_dir / "OsdagBridge_Testing_Report.pdf"
if pdf_file.exists():
    print(f"SUCCESS: PDF generated cleanly! Size: {pdf_file.stat().st_size} bytes")
else:
    print("FAILED: PDF not found.")
    print("STDERR snippet:", res2.stderr[-500:])
