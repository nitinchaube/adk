# Google Agent Development Kit (ADK) — practice workspace

This repository holds **learning experiments** built with the [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/). It includes sample agents: a shopping / customer-support flow, a memory-focused agent, and shared tools.

## Prerequisites

- **Python 3.10+** (this workspace has been used with 3.13)
- A **Google Cloud** project if you use **Vertex AI** or **Memory Bank** (optional for basic Gemini API key flows)

## Quick start

From this directory (`ADK/`):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Environment variables

Create a **`.env`** file in `ADK/` (do not commit it; it is listed in `.gitignore`).

**Option A — Google AI Studio (API key)**

```env
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_key_here
```

**Option B — Vertex AI**

```env
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```

Get a Studio key from [Google AI Studio](https://aistudio.google.com/apikey). For Vertex, use `gcloud auth application-default login` as needed.

### Run the dev UI

ADK discovers **agent packages** as **subfolders** of the directory where you run the command. Each package must contain `agent.py` (lowercase) with a `root_agent` export and an `__init__.py` that imports it.

```bash
cd /path/to/ADK
adk web
```

Open the URL shown (typically `http://127.0.0.1:8000`). Use the dropdown to pick an agent.

**Memory Bank (optional):** if you have an Agent Engine ID for Memory Bank:

```bash
adk web --memory_service_uri=agentengine://YOUR_AGENT_ENGINE_ID
```

## Agents in this repo

| Package | Purpose |
|--------|---------|
| **`MemoryBankAgent`** | Minimal agent with `PreloadMemoryTool` and a post-turn callback that syncs recent events to Memory Bank (when configured). |
| **`StatefulShoppingCartAgent`** | **Text-first** customer support: cart, catalog lookup, returns, image-assisted product matching, Open Library book search. Model: `gemini-2.5-flash`. |
| **`StatefulShoppingCartLiveAgent`** | Same tools as above, tuned for **live audio** (`gemini-live-2.5-flash-native-audio`). Use for voice in ADK Web; normal chat may need the text agent. |

## Project layout

```text
ADK/
├── config/
│   ├── catalog.py            # Product catalog (ids, price, stock, keywords)
│   └── settings.py          # Models, thresholds, Open Library URL, optional env overrides
├── MemoryBankAgent/          # Memory + PreloadMemoryTool
├── StatefulShoppingCartAgent/
├── StatefulShoppingCartLiveAgent/
├── Tools/
│   ├── ShoppingCartTool.py   # Cart, checkout, catalog, returns, image→SKU heuristics
│   └── ExternalAPITool.py    # Open Library search (httpx)
├── Setup.py                  # One-off: create Agent Engine (requires GOOGLE_CLOUD_* env)
├── .env                      # Local secrets (not committed)
└── .gitignore
```

## Configuration (Step 2 — no secrets in repo)

- **Catalog & pricing:** edit `config/catalog.py`.
- **Models, voice, memory slice, HTTP limits:** defaults live in `config/settings.py`; override at runtime with environment variables (all optional), for example:

| Variable | Purpose |
|----------|---------|
| `ADK_TEXT_MODEL` | Text agent model id |
| `ADK_LIVE_MODEL` | Live audio agent model id |
| `ADK_MEMORY_AGENT_MODEL` | MemoryBank agent model |
| `ADK_VOICE_NAME` | TTS voice for live agent |
| `ADK_TEXT_AGENT_NAME` / `ADK_LIVE_AGENT_NAME` / `ADK_MEMORY_AGENT_NAME` | Agent names in ADK |
| `ADK_MEMORY_EVENTS_SLICE_START` / `ADK_MEMORY_EVENTS_SLICE_END` | `events[start:end]` slice for Memory Bank sync (default `-5` / `-1`) |
| `ADK_MAX_TOOL_ERRORS_BEFORE_ESCALATE` | After-tool error escalation threshold |
| `ADK_DEFAULT_LOYALTY_THRESHOLD` | VIP threshold when neither `app:loyalty_threshold` nor legacy `app:loyality_threshold` is present in session |
| `ADK_ORDER_ID_PREFIX` / `ADK_TICKET_ID_PREFIX` | Order and ticket id prefixes |
| `ADK_OPEN_LIBRARY_*` | URL, timeout, result caps for book search |

## Tools (high level)

- **Shopping:** `get_product_details`, `add_to_cart`, `checkout`, `create_return_ticket`, `analyze_product_image`
- **External:** `search_books` (Open Library JSON API)

## Troubleshooting

- **No agents in dropdown:** run `adk web` from **`ADK/`** (parent of the agent folders), not from inside a single agent folder.
- **Live model errors on text-only turns:** use **`StatefulShoppingCartAgent`** for normal chat; reserve the **Live** agent for streaming/voice.
- **Import errors for `Tools`:** each `agent.py` prepends the `ADK/` root to `sys.path` so `from Tools....` resolves when the package is loaded.

## License / sharing

This is a personal learning repo. Code examples follow patterns from Google ADK docs; refer to [ADK documentation](https://google.github.io/adk-docs/) and your Google Cloud terms for production use.
