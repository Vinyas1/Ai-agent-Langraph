"""
E2B sandbox wrapper — compatible with e2b-code-interpreter v2.x
"""

import os
from e2b_code_interpreter import Sandbox


def _collect(execution) -> tuple[str, str]:
    stdout = "\n".join(execution.logs.stdout) if execution.logs.stdout else ""
    stderr = "\n".join(execution.logs.stderr) if execution.logs.stderr else ""
    if execution.error:
        err = f"\n{execution.error.name}: {execution.error.value}"
        if hasattr(execution.error, "traceback") and execution.error.traceback:
            err += f"\n{execution.error.traceback}"
        stderr += err
    return stdout.strip(), stderr.strip()


def _install(sbx: Sandbox, packages: list[str]) -> None:
    if not packages:
        return
    code = "import subprocess, sys\n"
    for pkg in packages:
        code += f"subprocess.run([sys.executable, '-m', 'pip', 'install', '{pkg}', '-q'], capture_output=True)\n"
    code += "print('packages ready')\n"
    sbx.run_code(code)


def _fix_csv_path(code: str) -> str:
    """Normalise any CSV path the LLM may have used to /tmp/dataset.csv."""
    # Order matters: replace longer/more-specific strings first
    replacements = [
        ("/workspace/dataset.csv", "/tmp/dataset.csv"),
        ("./dataset.csv",          "/tmp/dataset.csv"),
        # bare 'dataset.csv' only when NOT already preceded by /tmp/
        # use a simple guard: only replace if not already correct
    ]
    for old, new in replacements:
        code = code.replace(old, new)

    # Replace bare dataset.csv but avoid double-patching /tmp/dataset.csv
    import re
    code = re.sub(r'(?<!/tmp/)dataset\.csv', '/tmp/dataset.csv', code)
    return code


def run_in_sandbox(
    code: str,
    dataset_path: str = "",
    test_code: str = "",
    pip_packages: list[str] | None = None,
) -> tuple[str, str]:
    sbx = None
    try:
        sbx = Sandbox.create()
        _install(sbx, pip_packages or [])

        # tabular_ml mode
        if not test_code:
            if dataset_path and os.path.exists(dataset_path):
                with open(dataset_path, "rb") as f:
                    sbx.files.write("/tmp/dataset.csv", f)

            patched = _fix_csv_path(code)
            execution = sbx.run_code(patched, timeout=90)
            return _collect(execution)

        # debug_fix mode
        sbx.files.write("/tmp/main.py", code)
        sbx.files.write("/tmp/test_code.py", test_code)
        _install(sbx, ["pytest"])

        run_pytest = (
            "import subprocess, sys\n"
            "result = subprocess.run(\n"
            "    [sys.executable, '-m', 'pytest', '/tmp/test_code.py',\n"
            "     '-v', '--tb=short', '--no-header'],\n"
            "    capture_output=True, text=True, cwd='/tmp'\n"
            ")\n"
            "print(result.stdout)\n"
            "if result.stderr:\n"
            "    print(result.stderr)\n"
        )
        execution = sbx.run_code(run_pytest, timeout=60)
        return _collect(execution)

    except Exception as e:
        return "", f"Sandbox error: {type(e).__name__}: {e}"

    finally:
        if sbx:
            try:
                sbx.kill()
            except Exception:
                pass