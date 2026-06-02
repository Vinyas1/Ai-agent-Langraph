from typing import TypedDict


class AgentState(TypedDict):
    # --- Task type ---
    task_type: str              # "tabular_ml" or "debug_fix"

    # --- User inputs ---
    dataset_path: str           # path to CSV (tabular_ml) or empty (debug_fix)
    goal: str                   # prediction goal OR description of what to fix
    user_code: str              # empty for tabular_ml, user's buggy code for debug_fix
    test_code: str              # empty for tabular_ml, test cases for debug_fix

    # --- Explorer output ---
    dataset_info: str           # columns, dtypes, nulls, sample rows (tabular_ml only)

    # --- Coder output ---
    code: str                   # current code (ML pipeline or fixed code)

    # --- Executor output ---
    execution_output: str       # stdout from sandbox
    execution_error: str        # stderr / traceback
    metrics: str                # METRIC lines (tabular_ml) or test results (debug_fix)
    passed: bool                # ran without error? / all tests passed?

    # --- Evaluator output ---
    feedback: str               # what to try next

    # --- Loop control ---
    attempts: int
    history: list               # list of {attempt, code, metrics, feedback}
