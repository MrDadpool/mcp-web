# mcp-web — setup on a Mac

This gives a model running in LM Studio the ability to search the web, read
pages, and call HTTP APIs.

## 1. Unzip it somewhere permanent

Not Downloads — the folder has to stay put, because LM Studio launches the
server from this path. `~/mcp-web` is a fine choice.

## 2. Run the installer

Open Terminal and run:

```bash
cd ~/mcp-web
./install.sh
```

macOS may block the script the first time ("cannot be opened because it is
from an unidentified developer"). If that happens:

```bash
xattr -d com.apple.quarantine install.sh
chmod +x install.sh
./install.sh
```

It needs Python 3.11 or newer. If you don't have one, it tells you to install
`uv` first:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then run `./install.sh` again.

## 3. Paste the config into LM Studio

The installer prints a JSON block with the correct path already filled in. In
LM Studio: right sidebar → **Program** tab → **Install** → **Edit mcp.json**.
Paste it in and save.

## 4. Use it

Load a model that supports tool use, enable **mcp-web** for the chat, and ask
it something it would need the web for. LM Studio asks you to approve each
tool call the first time.

## Optional: JavaScript-heavy pages

Most pages work without this. If a site comes back empty because it renders
everything in JavaScript, install the headless browser:

```bash
cd ~/mcp-web
.venv/bin/python -m pip install playwright
.venv/bin/playwright install chromium
```

That downloads about 400MB. A fourth tool, `render_page`, appears the next
time LM Studio starts the server.

## What it will and won't reach

By default the server refuses to connect to your own machine or your local
network — localhost, 192.168.x.x, 10.x.x.x, and so on. This is deliberate: it
stops a model from being talked into reading your router's admin page or a
service you have running privately.

If you actually want the model to reach something on your own machine, add an
env block to the LM Studio config:

```json
{
  "mcpServers": {
    "mcp-web": {
      "command": "/Users/YOU/mcp-web/.venv/bin/mcp-web",
      "env": { "MCPWEB_ALLOW_PRIVATE": "1" }
    }
  }
}
```

Understand what that opens up before you turn it on. Other settings are listed
in README.md.

## If something breaks

LM Studio shows the server's stderr in the Program tab — errors show up there.
To check the server runs at all:

```bash
cd ~/mcp-web
.venv/bin/python -c "import anyio; from mcp_web.server import mcp; print([t.name for t in anyio.run(mcp.list_tools)])"
```

Expect: `['web_search', 'fetch_url', 'http_request']`.
