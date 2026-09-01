# mcp-web — project tracking

## Now
Nothing in flight. v0.1 core is built and passing.

## Done
- Design agreed: single stdio server, Python + MCP SDK, DuckDuckGo search,
  private-IP blocking by default, headless browser as a lazy optional extra.
- `net/guard.py` — SSRF guard. Blocks loopback/RFC1918/link-local/reserved,
  cloud metadata, non-http schemes, IPv6-mapped and integer-encoded IPv4.
- `net/client.py` — shared httpx client, manual redirect loop so every hop is
  re-validated, response size cap.
- `extract.py` — trafilatura HTML → markdown with a tag-stripping fallback.
- Tools: `web_search`, `fetch_url`, `http_request`, `render_page`.
- Migrated to MCP SDK 2.x (`MCPServer`, was `FastMCP` in 1.x).
- 26 tests passing. Live smoke test of search/fetch/http against the real
  internet passed.

## Next up
- Install the `browser` extra and verify `render_page` end to end — it is the
  one tool never exercised against a real page.
- Wire into `~/.lmstudio/mcp.json` and confirm a local model calls the tools.
- Consider a pinned-IP httpx transport to close the DNS rebinding gap noted in
  the README.
