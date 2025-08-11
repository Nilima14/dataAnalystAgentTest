# llm_client.py
import os
import openai
from typing import List, Dict

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Set OPENAI_API_KEY in environment")

openai.api_key = OPENAI_API_KEY

def chat_completion(messages: List[Dict], model: str = "gpt-4o-mini", max_tokens=1500, temperature=0.0):
    """
    Wrapper returning assistant text (string). Messages: list of dicts [{role:..., content:...}, ...]
    """
    resp = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content
