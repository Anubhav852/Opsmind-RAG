FROM python:3.11-slim AS builder
WORKDIR /app
COPY pyproject.toml .
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install . --extra-index-url https://download.pytorch.org/whl/cpu

FROM python:3.11-slim
RUN useradd -m app
COPY --from=builder /install /usr/local
USER app
ENV HF_HOME=/home/app/.cache/huggingface
EXPOSE 8000
CMD ["sh", "-c", "uvicorn opsmind.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
