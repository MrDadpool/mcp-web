# mcp-web — setup on Windows

This gives a model running in LM Studio the ability to search the web, read
pages, and call HTTP APIs.

## 1. Unzip it somewhere permanent

Not Downloads — the folder has to stay put, because LM Studio launches the
server from this path. `C:\Users\YOU\mcp-web` is a fine choice.

## 2. Run the installer

Open PowerShell and run:

```powershell
cd $HOME\mcp-web
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

The `-ExecutionPolicy Bypass` is needed because Windows blocks unsigned
scripts by default. It applies to this one run only.

It needs Python 3.11 or newer. If you don't have one, it tells you to install
`uv` first:

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

Then run the installer again.

## 3. Paste the config into LM Studio

The installer prints a JSON block with the correct path already filled in,
backslashes doubled the way JSON requires. In LM Studio: right sidebar →
**Program** tab → **Install** → **Edit mcp.json**. Paste it in and save.

## 4. Use it

Load a model that supports tool use, enable **mcp-web** for the chat, and ask
it something it would need the web for. LM Studio asks you to approve each
tool call the first time.

## Optional: JavaScript-heavy pages

Most pages work without this. If a site comes back empty because it renders
everything in JavaScript, install the headless browser:

```powershell
cd $HOME\mcp-web
.venv\Scripts\python.exe -m pip install playwright
.venv\Scripts\playwright.exe install chromium
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
      "command": "C:\\Users\\YOU\\mcp-web\\.venv\\Scripts\\mcp-web.exe",
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

```powershell
cd $HOME\mcp-web
.venv\Scripts\python.exe -c "import anyio; from mcp_web.server import mcp; print([t.name for t in anyio.run(mcp.list_tools)])"
```

Expect: `['web_search', 'fetch_url', 'http_request']`.
