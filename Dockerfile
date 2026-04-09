FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ABLETON_MCP_TRANSPORT=stdio \
    ABLETON_MCP_HOST=host.docker.internal \
    ABLETON_MCP_PORT=9877

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY mcp_server /app/mcp_server

RUN python -m pip install --upgrade pip && \
    python -m pip install .

ENTRYPOINT ["ableton-mcp"]
