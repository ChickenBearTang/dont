FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/workspace/AI_TMP/ai:/workspace/AI_TMP/ai/src:/workspace/AI_TMP

WORKDIR /workspace/AI_TMP

COPY . /workspace/AI_TMP/ai

WORKDIR /workspace/AI_TMP/ai

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

WORKDIR /workspace/AI_TMP/ai/src

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
