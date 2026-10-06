from prometheus_client import Counter, Histogram

TOKENS = Counter("opsmind_llm_tokens_total", "LLM tokens", ["model", "kind"])
INVESTIGATIONS = Counter("opsmind_investigations_total", "Investigations", ["status"])
RETRIEVE_LAT = Histogram("opsmind_retrieve_seconds", "Retrieval latency")
