# Badges

## Regenerating Badges

The coverage and CodeScene badges are static values captured from local runs. To refresh them:

```bash
# Install the dev dependency group (adds coverage.py)
uv sync --group dev

# Coverage: prints the current percent + a paste-ready shields.io URL
uv run --group dev python scripts/compute_metrics.py coverage

# CodeScene: lists mcp_server/ files + LOC weights. Run the CodeScene MCP
# code_health_score tool on each file, then compute the LOC-weighted mean
# (the script prints the formula and a paste-ready badge template).
uv run python scripts/compute_metrics.py codescene-plan
```

Then update the badge URLs in this README with the new values.
