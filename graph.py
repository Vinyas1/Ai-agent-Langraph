"""
LangGraph definition for the AI Data Scientist / Code Debugger agent (E2B backend).

Two modes:
  tabular_ml:  Explorer → Coder → Executor → Evaluator → retry/end
  debug_fix:   Explorer(skip) → Coder → Executor → Evaluator → retry/end
"""

from langgraph.graph import StateGraph, END
from state import AgentState
from nodes import explorer_node, coder_node, executor_node, evaluator_node
from config import MAX_RETRIES, TARGET_ACCURACY


# ── Conditional edge: should we retry? ──────────────────────────────

def should_retry(state: AgentState) -> str:
    """Decide whether to loop back to the Coder or stop."""

    if state["attempts"] >= MAX_RETRIES:
        return "end"

    task_type = state.get("task_type", "tabular_ml")

    if task_type == "debug_fix":
        if state["passed"]:
            return "end"
        return "retry"

    else:
        try:
            for line in state["metrics"].split("\n"):
                if "accuracy" in line.lower():
                    parts = line.strip().split(":")
                    accuracy = float(parts[-1])
                    if accuracy >= TARGET_ACCURACY:
                        return "end"
        except (ValueError, IndexError):
            pass

        if not state["passed"]:
            return "retry"

        return "retry"


# ── Build the graph ─────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("explorer", explorer_node)
    graph.add_node("coder", coder_node)
    graph.add_node("executor", executor_node)
    graph.add_node("evaluator", evaluator_node)

    graph.set_entry_point("explorer")

    graph.add_edge("explorer", "coder")
    graph.add_edge("coder", "executor")
    graph.add_edge("executor", "evaluator")

    graph.add_conditional_edges(
        "evaluator",
        should_retry,
        {"retry": "coder", "end": END},
    )

    return graph.compile()


# ── Run helpers ─────────────────────────────────────────────────────

def run_tabular_ml(dataset_path: str, goal: str) -> dict:
    app = build_graph()
    return app.invoke({
        "task_type": "tabular_ml",
        "dataset_path": dataset_path,
        "goal": goal,
        "user_code": "",
        "test_code": "",
        "dataset_info": "",
        "code": "",
        "execution_output": "",
        "execution_error": "",
        "metrics": "",
        "passed": False,
        "feedback": "",
        "attempts": 0,
        "history": [],
    })


def run_debug_fix(user_code: str, test_code: str, goal: str = "Fix all failing tests") -> dict:
    app = build_graph()
    return app.invoke({
        "task_type": "debug_fix",
        "dataset_path": "",
        "goal": goal,
        "user_code": user_code,
        "test_code": test_code,
        "dataset_info": "",
        "code": "",
        "execution_output": "",
        "execution_error": "",
        "metrics": "",
        "passed": False,
        "feedback": "",
        "attempts": 0,
        "history": [],
    })


# ── CLI ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage:")
        print('  Tabular ML:  python graph.py tabular_ml path/to/data.csv "predict churn"')
        print('  Debug Fix:   python graph.py debug_fix path/to/buggy.py path/to/tests.py "fix the sorting function"')
        sys.exit(1)

    task_type = sys.argv[1]

    if task_type == "tabular_ml":
        if len(sys.argv) < 4:
            print('Usage: python graph.py tabular_ml path/to/data.csv "predict churn"')
            sys.exit(1)
        dataset_path = sys.argv[2]
        goal = sys.argv[3]
        print(f"Mode: tabular_ml")
        print(f"Dataset: {dataset_path}")
        print(f"Goal: {goal}")
        print("=" * 60)
        result = run_tabular_ml(dataset_path, goal)

    elif task_type == "debug_fix":
        if len(sys.argv) < 4:
            print('Usage: python graph.py debug_fix path/to/buggy.py path/to/tests.py "fix description"')
            sys.exit(1)
        buggy_path = sys.argv[2]
        test_path = sys.argv[3]
        goal = sys.argv[4] if len(sys.argv) > 4 else "Fix all failing tests"

        with open(buggy_path) as f:
            user_code = f.read()
        with open(test_path) as f:
            test_code = f.read()

        print(f"Mode: debug_fix")
        print(f"Buggy code: {buggy_path}")
        print(f"Tests: {test_path}")
        print(f"Goal: {goal}")
        print("=" * 60)
        result = run_debug_fix(user_code, test_code, goal)

    else:
        print(f"Unknown task type: {task_type}")
        print("Use 'tabular_ml' or 'debug_fix'")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Attempts: {result['attempts']}")
    print(f"Passed: {result['passed']}")
    print(f"Metrics: {result['metrics']}")
    print(f"\nFinal code:\n{result['code']}")
