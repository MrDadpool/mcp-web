# mcp-web

An MCP server that gives a locally-run LLM access to the internet: web search,
page fetching, raw HTTP, and optional headless rendering. Built for LM Studio,
but it is a plain stdio MCP server and works with any MCP client.

## Tools

| Tool | What it does |
|---|---|
| `web_search` | DuckDuckGo search. Returns title, url, snippet. |
| `fetch_url` | Fetches a page and returns its main content as markdown. |
| `http_request` | Arbitrary HTTP method/headers/body. For JSON APIs. |
| `render_page` | Loads a page in headless Chromium, runs its JS, returns text. Registered only when the `browser` extra is installed. |

## Install

```bash
uv venv
uv pip install -e .
```

With headless rendering:

```bash
uv pip install -e ".[browser]"
uv run playwright install chromium
```

## Wiring into LM Studio

LM Studio reads `~/.lmstudio/mcp.json` (also reachable from the Program tab in
the right sidebar → Install → Edit `mcp.json`). Add:

```json
{
  "mcpServers": {
    "mcp-web": {
      "command": "/Users/YOU/mcp-web/.venv/bin/mcp-web"
    }
  }
}
```

Then load a tool-capable model and enable the server for the chat. LM Studio
asks for confirmation before each tool call by default.

## Security

Local models are talked into things. Every outbound request in this server —
including redirects and browser navigations — goes through `net/guard.py`,
which resolves the hostname and refuses:

- loopback, RFC1918, link-local, reserved, and multicast addresses
- cloud metadata endpoints (169.254.169.254)
- anything but `http` and `https`
- IPv4 addresses disguised as IPv6 (`::ffff:127.0.0.1`) or as integers
  (`http://2130706433/`)

Without this, `http_request` would hand the model your router admin page and
every service you have bound to localhost.

**Known gap:** the guard resolves DNS, then httpx resolves it again to
connect. A hostile authoritative nameserver can answer differently the second
time (DNS rebinding) and reach a private address. Closing this needs a custom
transport that connects to the already-validated IP. Acceptable for a local
tool on a trusted network; not acceptable if you ever expose this server.

## Configuration

All optional, all environment variables:

| Variable | Default | Meaning |
|---|---|---|
| `MCPWEB_ALLOW_PRIVATE` | `0` | `1` lets the model reach localhost and your LAN |
| `MCPWEB_ALLOWLIST` | empty | Comma-separated hosts; when set, nothing else is reachable |
| `MCPWEB_TIMEOUT` | `20` | Per-request timeout, seconds |
| `MCPWEB_MAX_BYTES` | `2000000` | Response body cap |
| `MCPWEB_MAX_REDIRECTS` | `5` | Redirect hop limit |
| `MCPWEB_USER_AGENT` | Chrome-ish | Sent on every request |

## Tests

```bash
uv run pytest
```
