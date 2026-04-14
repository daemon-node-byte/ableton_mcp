FROM python:3.11-slim

ARG ABLETON_MCP_HOST=localhost
ARG ABLETON_MCP_PORT=9877

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ABLETON_MCP_HOST=${ABLETON_MCP_HOST} \
    ABLETON_MCP_PORT=${ABLETON_MCP_PORT} \
    ABLETON_MCP_TRANSPORT=streamable-http \
    ABLETON_MCP_BIND_HOST=0.0.0.0 \
    ABLETON_MCP_HTTP_PATH=/mcp/ \
    PORT=8080

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY mcp_server /app/mcp_server

RUN python -m pip install --upgrade pip && \
    python -m pip install .

ENTRYPOINT ["ableton-mcp"]
