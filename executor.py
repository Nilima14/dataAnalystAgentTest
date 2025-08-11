# executor.py
import subprocess
import tempfile
import os
import shlex
from typing import Tuple

PYTHON_BIN = os.environ.get("PYTHON_BIN", "python3")

def run_python_script(script: str, files: dict, timeout_seconds: int = 120) -> Tuple[int, str, str]:
    """
    script: python code string
    files: dict mapping filename -> bytes content (these will be written in a temp dir)
    returns: (returncode, stdout, stderr)
    """
    with tempfile.TemporaryDirectory() as td:
        # write files
        for fname, content in files.items():
            dest = os.path.join(td, fname)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            mode = "wb"
            if isinstance(content, str):
                content = content.encode("utf-8")
            with open(dest, mode) as f:
                f.write(content)
        # write script
        script_path = os.path.join(td, "job.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)

        # run subprocess with limited environment
        env = {
            "PYTHONPATH": "",
            # pass minimal env; add others if needed
        }
        try:
            proc = subprocess.run(
                [PYTHON_BIN, script_path],
                cwd=td,
                capture_output=True,
                env=env,
                timeout=timeout_seconds,
                check=False,
            )
            return proc.returncode, proc.stdout.decode("utf-8", errors="replace"), proc.stderr.decode("utf-8", errors="replace")
        except subprocess.TimeoutExpired as e:
            return -1, "", f"Timeout after {timeout_seconds} seconds"
