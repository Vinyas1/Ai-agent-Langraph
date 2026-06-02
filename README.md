# 🔬 AI Data Scientist & Code Debugger Agent (E2B)

A multi-agent AI system with **two modes**, sandboxed via **E2B** (cloud, no local Docker needed):

1. **tabular_ml** — Upload a CSV, describe your goal, watch the agent build an
   ML model and iterate based on real metrics.
2. **debug_fix** — Paste buggy code + test cases, and the agent auto-fixes the
   code until all tests pass.

Both modes use the same LangGraph orchestration loop:
```
Explorer → Coder → Executor (E2B sandbox) → Evaluator → retry or done
```

## Tech stack

| Component       | Tool                                          |
|-----------------|-----------------------------------------------|
| Language        | Python                                        |
| Orchestration   | LangGraph (nodes, edges, conditional retry)   |
| LLM             | DeepSeek-V4-Flash (OpenAI-compatible API)     |
| Sandbox         | E2B (cloud sandbox, free Hobby tier)          |
| Frontend        | Streamlit                                     |

## Setup

### 1. Install

```bash
git clone <your-repo-url>
cd ai-agent-e2b
pip install -r requirements.txt
```

### 2. API keys

```bash
cp .env.example .env
```

Edit `.env`:
```
DEEPSEEK_API_KEY=your_deepseek_key
E2B_API_KEY=your_e2b_key
```

Get keys:
- DeepSeek: https://platform.deepseek.com/
- E2B: https://e2b.dev/ (free Hobby tier — $100 in credits)

### 3. Generate sample data

```bash
python sample_data/generate_churn.py
```

### 4. Run

**Streamlit UI (recommended):**
```bash
streamlit run app.py
```

**CLI — tabular ML:**
```bash
python graph.py tabular_ml sample_data/churn.csv "predict customer churn"
```

**CLI — debug fix:**
```bash
python graph.py debug_fix sample_data/buggy_code.py sample_data/test_buggy.py "fix all bugs"
```

## Project structure

```
ai-agent-e2b/
├── app.py                   # Streamlit frontend (both modes)
├── graph.py                 # LangGraph definition + CLI runner
├── nodes.py                 # Agent nodes (explorer, coder, executor, evaluator)
├── prompts.py                # System prompts for each task_type
├── sandbox.py                # E2B sandbox wrapper
├── state.py                  # Shared AgentState TypedDict
├── config.py                 # DeepSeek client, settings
├── logger.py                  # JSON run logger
├── requirements.txt
├── .env.example
├── sample_data/
│   ├── generate_churn.py    # Generate demo churn CSV
│   ├── churn.csv            # Sample dataset (1000 rows)
│   ├── buggy_code.py        # Sample buggy code (5 bugs)
│   └── test_buggy.py        # Test cases for buggy code
└── logs/                     # Auto-created, stores run transcripts
```

## How the modes work

### tabular_ml
1. **Explorer** uploads the CSV to E2B, reads it (columns, types, nulls, stats)
2. **Coder** writes a full sklearn pipeline (preprocessing → train → evaluate)
3. **Executor** runs it in E2B, captures real accuracy/F1 metrics
4. **Evaluator** checks: accuracy >= target? If not, suggests a specific change
5. Loop back to Coder with feedback, up to max_retries

### debug_fix
1. **Explorer** skips (no dataset to explore)
2. **Coder** reads the buggy code + test cases + any prior errors, writes a fix
3. **Executor** uploads the fixed code + tests to E2B, runs pytest, captures results
4. **Evaluator** checks: all tests pass? If not, hints at what's still wrong
5. Loop back to Coder with feedback, up to max_retries

## Demo tips

- **tabular_ml**: Use the churn dataset — the agent typically starts with
  LogisticRegression (~70%), then switches to RandomForest (~85%+).
- **debug_fix**: The bundled buggy_code.py has 5 deliberate bugs across 3
  functions. Watch the agent fix most of them on the first try, then close
  the gap on retry — a great demo of the fail → feedback → fix loop.
- Each E2B sandbox run costs a fraction of a cent — the free $100 credit
  will cover thousands of runs for a portfolio demo.

## License

MIT
