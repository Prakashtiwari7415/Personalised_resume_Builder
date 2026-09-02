"""
Configuration and Environment Settings for AI Resume Builder
"""

import os
import warnings
from dotenv import load_dotenv
import litellm

# Filter out unnecessary warnings
warnings.filterwarnings('ignore')

# Disable Telemetry & Tracing to avoid interactive terminal prompts
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["CREWAI_TRACING_ENABLED"] = "false"
os.environ["OTEL_SDK_DISABLED"] = "true"

# Load environment variables
load_dotenv()

# Configure LiteLLM
litellm.drop_params = True

# Monkeypatch litellm.completion to remove Groq-unsupported cache fields
_original_completion = litellm.completion

def _clean_completion(*args, **kwargs):
    kwargs.pop('cache_prompt', None)
    if 'messages' in kwargs and isinstance(kwargs['messages'], list):
        for msg in kwargs['messages']:
            if isinstance(msg, dict):
                msg.pop('cache_breakpoint', None)
                msg.pop('cache_control', None)
    return _original_completion(*args, **kwargs)

litellm.completion = _clean_completion

# Model Constants & Defaults
DEFAULT_MODEL = "openai/gpt-oss-20b"
AVAILABLE_MODELS = [
    "openai/gpt-oss-20b",
    "groq/compound-mini",
    "qwen/qwen3.6-27b",
    "qwen/qwen3.8-27b"
]

DEFAULT_LOCATION = "Remote"
EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)
