# Deploy AbletonMCP to Google Cloud Run

This guide is the canonical Docker-based deployment path for hosting AbletonMCP as a remote MCP server on Google Cloud Run.

It assumes:

- you want a public unauthenticated HTTPS endpoint
- the Cloud Run service can already reach the Ableton Remote Script bridge over the network
- you want Streamable HTTP at `/mcp/`

Important security note:

- this guide uses `--allow-unauthenticated` on purpose
- that means anyone with the service URL can call your MCP tools
- only use this setup if that exposure is acceptable for your environment

## Runtime Contract

The container listens with these defaults:

- `ABLETON_MCP_TRANSPORT=streamable-http`
- `ABLETON_MCP_BIND_HOST=0.0.0.0`
- `ABLETON_MCP_HTTP_PATH=/mcp/`
- `PORT=8080`

The service still needs these Ableton bridge settings:

- `ABLETON_MCP_HOST`
- `ABLETON_MCP_PORT`
- optional `ABLETON_MCP_CONNECT_TIMEOUT`
- optional `ABLETON_MCP_RESPONSE_TIMEOUT`

The deployed MCP endpoint shape is:

```text
https://<service-url>/mcp/
```

## 1. Set Variables

```bash
export PROJECT_ID="your-gcp-project"
export REGION="us-central1"
export REPOSITORY="ableton-mcp"
export SERVICE="ableton-mcp-v2"
export IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE}:v1.0.0"
export ABLETON_MCP_HOST_VALUE="reachable-ableton-bridge-host"
export ABLETON_MCP_PORT_VALUE="9877"
```

## 2. Enable Required Services

```bash
gcloud config set project "${PROJECT_ID}"

gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com
```

## 3. Create an Artifact Registry Repository

Create it once per region:

```bash
gcloud artifacts repositories create "${REPOSITORY}" \
  --repository-format=docker \
  --location="${REGION}"
```

Configure Docker auth:

```bash
gcloud auth configure-docker "${REGION}-docker.pkg.dev"
```

## 4. Build and Push the Container

```bash
docker build -t "${IMAGE}" .
docker push "${IMAGE}"
```

## 5. Deploy to Cloud Run

```bash
gcloud run deploy "${SERVICE}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars "ABLETON_MCP_TRANSPORT=streamable-http,ABLETON_MCP_BIND_HOST=0.0.0.0,ABLETON_MCP_HTTP_PATH=/mcp/,ABLETON_MCP_HOST=${ABLETON_MCP_HOST_VALUE},ABLETON_MCP_PORT=${ABLETON_MCP_PORT_VALUE}"
```

If you need custom bridge timeouts, add them to `--set-env-vars`.

## 6. Get the Service URL

```bash
SERVICE_URL="$(gcloud run services describe "${SERVICE}" \
  --region "${REGION}" \
  --format='value(status.url)')"

echo "${SERVICE_URL}/mcp/"
```

That printed URL is the remote MCP endpoint.

## 7. Manual Verification

Verify the service from a remote MCP client:

1. Connect the client to `https://<service-url>/mcp/`
2. Call `health_check`
3. Call `get_session_info`

Expected result:

- the MCP connection succeeds
- `health_check` returns a valid Ableton status payload
- `get_session_info` returns track, return-track, and scene information

## 8. Negative-Path Check

To confirm clean error handling, redeploy once with a bad bridge host or port:

```bash
gcloud run deploy "${SERVICE}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars "ABLETON_MCP_TRANSPORT=streamable-http,ABLETON_MCP_BIND_HOST=0.0.0.0,ABLETON_MCP_HTTP_PATH=/mcp/,ABLETON_MCP_HOST=203.0.113.10,ABLETON_MCP_PORT=9999"
```

Then call `health_check` again.

Expected result:

- the service stays up
- the tool call fails with a clean Ableton transport error
- the request does not hang indefinitely

After that, redeploy with the correct bridge host and port.
