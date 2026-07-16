# For MCP registry build verification (e.g. Glama's reproducible-build gate).
# Emulo's MCP server is normally run locally as `python emulo.py mcp` so it can
# read your own mined profile under ~/.emulo. In a bare container it starts and
# lists its tool but has no local profile to serve unless ~/.emulo is mounted.
FROM python:3.12-slim
WORKDIR /app
COPY emulo.py MINING_PROMPT.md ./
ENTRYPOINT ["python", "emulo.py", "mcp"]
