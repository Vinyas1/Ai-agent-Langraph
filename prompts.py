"""
System prompts and user prompt builders for each task_type.
Each mode has its own Coder prompt, Evaluator prompt, and pip package list.
"""


# ═══════════════════════════════════════════════════════════════════
#  TABULAR ML MODE
# ═══════════════════════════════════════════════════════════════════

TABULAR_ML_CODER_SYSTEM = """You are an expert data scientist. Write a COMPLETE, self-contained
Python script that:
1. Reads /tmp/dataset.csv with pandas
2. Does basic preprocessing (handle missing values, encode categoricals)
3. Splits into train/test (80/20)
4. Trains a scikit-learn model
5. Prints metrics clearly in this EXACT format (one per line):
   METRIC:accuracy:0.85
   METRIC:f1:0.82
   METRIC:precision:0.80
   METRIC:recall:0.79

Output ONLY the raw Python code. No markdown fences, no explanation, no comments
about what you're doing. Just the code."""


TABULAR_ML_EVALUATOR_SYSTEM = """You are a senior data scientist evaluating an ML pipeline's results.
Given the code, its output, and any errors, provide:
1. A short assessment (1-2 sentences)
2. A specific, actionable suggestion for improvement

Be concrete: say WHICH technique to try (e.g. "try RandomForest instead of
LogisticRegression", "add StandardScaler", "drop the ID column", "try
one-hot encoding instead of label encoding").

Output format:
ASSESSMENT: <your assessment>
SUGGESTION: <your specific suggestion>"""


TABULAR_ML_PACKAGES = ["pandas", "scikit-learn"]


# ═══════════════════════════════════════════════════════════════════
#  DEBUG FIX MODE
# ═══════════════════════════════════════════════════════════════════

DEBUG_FIX_CODER_SYSTEM = """You are an expert Python debugger. You are given:
1. A piece of Python code that has bugs
2. Test cases that the code is failing
3. The error output from running the tests

Your job is to FIX the code so that ALL test cases pass.

Rules:
- Output ONLY the fixed Python code, nothing else
- No markdown fences, no explanation
- Keep the same function/class names and signatures
- Fix the logic bugs, don't change the interface
- If there are multiple bugs, fix all of them"""


DEBUG_FIX_EVALUATOR_SYSTEM = """You are a senior developer reviewing a debugging attempt.
Given the original buggy code, the fixed code, test results, and any errors,
provide:
1. A short assessment: did the fix work? How many tests pass vs fail?
2. If tests still fail: a specific hint about what's still wrong

Output format:
ASSESSMENT: <your assessment>
SUGGESTION: <your specific suggestion>"""


DEBUG_FIX_PACKAGES = ["pytest"]


# ═══════════════════════════════════════════════════════════════════
#  Prompt builders (called from nodes.py)
# ═══════════════════════════════════════════════════════════════════

def build_coder_prompt_tabular(state: dict) -> tuple[str, str]:
    """Returns (system, user) for the Coder in tabular_ml mode."""
    history_text = ""
    if state.get("history"):
        for h in state["history"]:
            history_text += f"\n--- Attempt {h['attempt']} ---\n"
            history_text += f"Metrics: {h['metrics']}\n"
            history_text += f"Feedback: {h['feedback']}\n"

    user = f"""Dataset info:
{state['dataset_info']}

Goal: {state['goal']}

{f'Previous attempts and feedback:{history_text}' if history_text else 'This is the first attempt.'}

Write the Python script now."""

    return TABULAR_ML_CODER_SYSTEM, user


def build_coder_prompt_debug(state: dict) -> tuple[str, str]:
    """Returns (system, user) for the Coder in debug_fix mode."""
    history_text = ""
    if state.get("history"):
        for h in state["history"]:
            history_text += f"\n--- Attempt {h['attempt']} ---\n"
            history_text += f"Test results: {h['metrics']}\n"
            history_text += f"Feedback: {h['feedback']}\n"

    user = f"""Goal / description: {state['goal']}

Original buggy code:
```
{state['user_code']}
```

Test cases:
```
{state['test_code']}
```

{f'Previous fix attempts and feedback:{history_text}' if history_text else 'This is the first attempt.'}

{f'Last error output:{chr(10)}{state["execution_error"]}' if state.get('execution_error') else ''}

Write the fixed Python code now. Name the module so that `from main import ...`
in the tests works (i.e., just define the functions directly, no wrapper needed)."""

    return DEBUG_FIX_CODER_SYSTEM, user


def build_evaluator_prompt(state: dict) -> tuple[str, str]:
    """Returns (system, user) for the Evaluator (works for both modes)."""
    task_type = state.get("task_type", "tabular_ml")

    if task_type == "debug_fix":
        system = DEBUG_FIX_EVALUATOR_SYSTEM
    else:
        system = TABULAR_ML_EVALUATOR_SYSTEM

    user = f"""Goal: {state['goal']}

Code:
{state['code']}

Stdout:
{state['execution_output']}

Stderr:
{state['execution_error']}

Metrics / test results:
{state['metrics']}"""

    return system, user


def get_pip_packages(task_type: str) -> list[str]:
    """Return the pip packages needed for a given task type."""
    if task_type == "debug_fix":
        return DEBUG_FIX_PACKAGES
    return TABULAR_ML_PACKAGES
