# AI Healthier Every Day — API + browser self-care app in one container.
# Build from the repository root (the backend serves ../webapp at "/"):
#   docker build -f backend/Dockerfile -t ai-healthier .
#   docker run -p 8000:8000 --env LLM_API_KEY=... ai-healthier
FROM python:3.11-slim

WORKDIR /srv

COPY backend/pyproject.toml backend/README.md* backend/
# src/model are only needed for the optional ST-GCN layer (ENABLE_STGCN=0 by default);
# keep the image lean by excluding them.
COPY backend/app backend/app
COPY webapp webapp

RUN pip install --no-cache-dir "/srv/backend"

EXPOSE 8000
ENV MODEL_SERVICE_DB=/data/model_usage.db
VOLUME ["/data"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
