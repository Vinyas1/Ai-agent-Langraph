import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# --- DeepSeek client (OpenAI-compatible) ---
llm_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)
MODEL = "deepseek-v4-flash"

# --- E2B ---
# E2B_API_KEY is read automatically from env by the e2b SDK

# --- Agent settings ---
MAX_RETRIES = 1
TARGET_ACCURACY = 0.80  # for tabular_ml mode

# --- Task types ---
TASK_TYPES = ["tabular_ml", "debug_fix"]
