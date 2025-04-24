import os
import subprocess
from pathlib import Path

import pytest


# --- Discover run scripts ---
def find_run_files(base_dir):
    run_files = []
    for root, _, files in os.walk(base_dir):
        run_files.extend(
            Path(root) / file
            for file in files
            if file.startswith("run_") and file.endswith(".py") and "examples" in root
        )

    print("Found the following run scripts:")
    for run_file in run_files:
        print(run_file)

    return run_files


BASE_DIRECTORY = Path(__file__).resolve().parent.parent.parent / "h2i_examples/."
RUN_SCRIPTS = find_run_files(BASE_DIRECTORY)


# --- Test runner ---
@pytest.mark.parametrize("script_path", RUN_SCRIPTS)
def test_run_script(script_path):
    original_cwd = Path.cwd()
    os.chdir(script_path.parent)
    try:
        with Path(os.devnull).open("w") as devnull:
            proc = subprocess.Popen(
                ["python", script_path.name], stdout=devnull, stderr=subprocess.PIPE
            )
            proc.wait(timeout=500)
            _, stderr = proc.communicate()
    finally:
        os.chdir(original_cwd)

    if proc.returncode != 0:
        if b"ImportError" in stderr:
            pytest.skip(f"Skipped {script_path.name} due to ImportError")
        else:
            raise RuntimeError(f"Error running {script_path.name}:\n{stderr.decode('utf-8')}")
