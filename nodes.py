"""
LangGraph nodes — each function takes the shared AgentState,
calls DeepSeek / E2B sandbox as needed, and returns a partial state update.

Supports two task types:
  - tabular_ml:  explore dataset → code ML pipeline → run → evaluate → retry
  - debug_fix:   take buggy code + tests → fix → run tests → evaluate → retry
"""

from config import llm_client, MODEL
from state import AgentState
from sandbox import run_in_sandbox
from prompts import (
    build_coder_prompt_tabular,
    build_coder_prompt_debug,
    build_evaluator_prompt,
    get_pip_packages,
)


# ── helpers ──────────────────────────────────────────────────────────

def _ask_llm(system: str, user: str) -> str:
    """Call DeepSeek-V4-Flash and return the text response."""
    resp = llm_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
        max_tokens=4096,
    )
    return resp.choices[0].message.content


# ── 1. Explorer node (tabular_ml only) ──────────────────────────────

def explorer_node(state: AgentState) -> dict:
    """
    For tabular_ml: reads the CSV in the E2B sandbox and returns a summary.
    For debug_fix: skips exploration, just passes through.
    """
    if state["task_type"] == "debug_fix":
        return {
            "dataset_info": "N/A (debug_fix mode)",
            "attempts": 0,
            "history": [],
        }

    explore_code = """
import pandas as pd

df = pd.read_csv("/tmp/dataset.csv")
print("=== SHAPE ===")
print(df.shape)
print("\\n=== COLUMNS & DTYPES ===")
print(df.dtypes.to_string())
print("\\n=== MISSING VALUES ===")
print(df.isnull().sum().to_string())
print("\\n=== FIRST 5 ROWS ===")
print(df.head().to_string())
print("\\n=== BASIC STATS ===")
print(df.describe().to_string())
"""
    packages = get_pip_packages(state["task_type"])
    stdout, stderr = run_in_sandbox(
        explore_code,
        dataset_path=state["dataset_path"],
        pip_packages=packages,
    )

    dataset_info = stdout if stdout else f"Exploration failed: {stderr}"

    return {
        "dataset_info": dataset_info,
        "attempts": 0,
        "history": [],
    }


# ── 2. Coder node ───────────────────────────────────────────────────

def coder_node(state: AgentState) -> dict:
    """Generate code — ML pipeline (tabular_ml) or fixed code (debug_fix)."""

    if state["task_type"] == "debug_fix":
        system, user = build_coder_prompt_debug(state)
    else:
        system, user = build_coder_prompt_tabular(state)

    code = _ask_llm(system, user)

    # Strip markdown fences if the LLM wraps them
    code = code.replace("```python", "").replace("```", "").strip()

    return {"code": code}


# ── 3. Executor node ────────────────────────────────────────────────

def executor_node(state: AgentState) -> dict:
    """Run the code inside the E2B sandbox and capture real output."""

    packages = get_pip_packages(state["task_type"])

    if state["task_type"] == "debug_fix":
        # Run the fixed code + test cases together
        stdout, stderr = run_in_sandbox(
            code=state["code"],
            test_code=state["test_code"],
            pip_packages=packages,
        )

        # "passed" means no failures reported by pytest
        combined = (stdout + stderr).lower()
        all_passed = "failed" not in combined and "error" not in combined and "passed" in combined
        metrics_str = stdout  # the pytest -v output IS the metrics

    else:
        # tabular_ml: run the ML code with the dataset
        stdout, stderr = run_in_sandbox(
            code=state["code"],
            dataset_path=state["dataset_path"],
            pip_packages=packages,
        )

        # Extract METRIC lines
        metrics_lines = [
            line for line in (stdout or "").split("\n")
            if line.strip().startswith("METRIC:")
        ]
        metrics_str = "\n".join(metrics_lines) if metrics_lines else "No metrics found"
        all_passed = bool(stdout) and not bool(stderr)

    return {
        "execution_output": stdout or "",
        "execution_error": stderr or "",
        "metrics": metrics_str,
        "passed": all_passed,
    }


# ── 4. Evaluator node ──────────────────────────────────────────────

def evaluator_node(state: AgentState) -> dict:
    """Assess results and suggest improvement."""

    system, user = build_evaluator_prompt(state)
    feedback = _ask_llm(system, user)

    new_history = list(state.get("history", []))
    new_history.append({
        "attempt": state["attempts"] + 1,
        "metrics": state["metrics"],
        "feedback": feedback,
        "code": state["code"],
    })

    return {
        "feedback": feedback,
        "attempts": state["attempts"] + 1,
        "history": new_history,
    }
