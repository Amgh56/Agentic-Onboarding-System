"""One small model call, to check the .env values work. Run from backend/:

    python -m scripts.test_llm_call
"""

from app.core import llm

print(llm.complete("Reply with the single word: ready", model="fast"))
