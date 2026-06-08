"""
Streamlit UI for the AI Data Scientist / Code Debugger agent (E2B backend).
Supports two modes: tabular_ml and debug_fix.
"""

import streamlit as st
import tempfile
import os

from graph import build_graph
from logger import save_run_log


# ── Page config ─────────────────────────────────────────────────────

st.set_page_config(page_title="AI Agent", page_icon="🔬", layout="wide")
st.title("🔬 AI Data Scientist & Code Debugger")
st.caption("Two modes: build ML models from data, or auto-fix buggy code using test cases. Sandboxed with E2B.")

# ── Sidebar ─────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Settings")
    task_type = st.radio("Task mode", ["tabular_ml", "debug_fix"], captions=[
        "Upload CSV → build ML model",
        "Paste buggy code + tests → auto-fix",
    ])
    max_retries = st.slider("Max retries", 1, 5, 3)
    target_accuracy = st.slider("Target accuracy (tabular_ml only)", 0.5, 0.99, 0.80, 0.01)
    st.divider()
    st.markdown("**Tech stack**")
    st.markdown("- LangGraph (orchestration)")
    st.markdown("- DeepSeek-V4-Flash (LLM)")
    st.markdown("- E2B (sandbox execution)")

# ── Main inputs ─────────────────────────────────────────────────────

if task_type == "tabular_ml":
    st.subheader("📊 Tabular ML mode")
    col1, col2 = st.columns([1, 2])
    with col1:
        uploaded_file = st.file_uploader("Upload a CSV dataset", type=["csv"])
    with col2:
        goal = st.text_input(
            "What should the model predict?",
            placeholder='e.g. "predict customer churn"',
        )
    can_run = uploaded_file is not None and bool(goal)

else:
    st.subheader("🐛 Debug Fix mode")
    col1, col2 = st.columns(2)
    with col1:
        user_code = st.text_area(
            "Paste buggy code",
            height=250,
            placeholder="def merge_sort(arr):\n    ...",
        )
    with col2:
        test_code = st.text_area(
            "Paste test cases (pytest style, `from main import ...`)",
            height=250,
            placeholder="from main import merge_sort\n\ndef test_merge_sort():\n    assert merge_sort([3,1,2]) == [1,2,3]",
        )
    goal = st.text_input(
        "Describe the issue (optional)",
        value="Fix all failing tests",
        placeholder="Fix the sorting function",
    )
    can_run = bool(user_code) and bool(test_code)

# ── Run ─────────────────────────────────────────────────────────────

if can_run:
    if st.button("🚀 Run agent", type="primary", use_container_width=True):

        import config
        config.MAX_RETRIES = max_retries
        config.TARGET_ACCURACY = target_accuracy

        tmp_path = None

        if task_type == "tabular_ml":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name

            initial_state = {
                "task_type": "tabular_ml",
                "dataset_path": tmp_path,
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
            }
        else:
            initial_state = {
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
            }

        app = build_graph()
        st.divider()

        for event in app.stream(initial_state, stream_mode="updates"):
            for node_name, node_output in event.items():

                if node_name == "explorer":
                    if task_type == "tabular_ml":
                        st.subheader("📊 Dataset overview")
                        st.code(node_output.get("dataset_info", ""), language="text")

                elif node_name == "coder":
                    label = "💻 Generated ML code" if task_type == "tabular_ml" else "🔧 Fixed code"
                    st.subheader(label)
                    st.code(node_output.get("code", ""), language="python")

                elif node_name == "executor":
                    st.subheader("⚡ Execution results")
                    out = node_output.get("execution_output", "")
                    err = node_output.get("execution_error", "")
                    if out:
                        st.code(out, language="text")
                    if err:
                        st.error(f"```\n{err}\n```")

                    if node_output.get("passed"):
                        st.success("✅ All checks passed!")
                    else:
                        metrics = node_output.get("metrics", "")
                        if metrics and metrics != "No metrics found":
                            st.warning(f"Metrics: {metrics}")
                        else:
                            st.warning("Tests failing or no metrics captured")

                elif node_name == "evaluator":
                    st.subheader("🧠 Evaluator feedback")
                    st.info(node_output.get("feedback", ""))
                    attempts_so_far = node_output.get("attempts", 0)
                    st.caption(f"Attempts: {attempts_so_far} / {max_retries}")

        # ── Final summary ───────────────────────────────────────
        final_state = app.invoke(initial_state)

        st.divider()
        st.header("🏁 Final result")

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Mode", final_state.get("task_type", "?"))
        with col_b:
            st.metric("Attempts", final_state.get("attempts", "?"))
        with col_c:
            status = "✅ Passed" if final_state.get("passed") else "❌ Not passed"
            st.metric("Status", status)

        st.subheader("Final code")
        st.code(final_state.get("code", ""), language="python")

        log_path = save_run_log(final_state)
        st.caption(f"Run log saved to `{log_path}`")

        if final_state.get("history"):
            st.subheader("📈 Iteration history")
            for h in final_state["history"]:
                with st.expander(f"Attempt {h['attempt']} — {h['metrics'][:80]}..."):
                    st.code(h["code"], language="python")
                    st.info(h["feedback"])

        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

else:
    if task_type == "tabular_ml":
        st.info("👆 Upload a CSV and enter a prediction goal to start.")
    else:
        st.info("👆 Paste your buggy code and test cases to start.")
