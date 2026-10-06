from openai import OpenAI

from .config import settings
from .metrics import TOKENS

_client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)


def chat(messages: list[dict], *, tier: str = "strong", tools: list[dict] | None = None):
    """Model routing: 'strong' for investigation, 'cheap' for verification. Tracks tokens per model."""
    model = settings.llm_model if tier == "strong" else settings.llm_model_cheap
    kwargs = dict(model=model, messages=messages, temperature=0.0)
    if tools:
        kwargs["tools"] = tools
    resp = _client.chat.completions.create(**kwargs)
    if resp.usage:
        TOKENS.labels(model, "prompt").inc(resp.usage.prompt_tokens)
        TOKENS.labels(model, "completion").inc(resp.usage.completion_tokens)
    return resp.choices[0].message, resp.usage
