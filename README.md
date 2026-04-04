# ADK — Google Agent Development Kit Projects

A collection of AI agents built with [Google's Agent Development Kit (ADK)](https://github.com/google/adk-python), demonstrating stateful tool use, callbacks, memory persistence, multi-agent orchestration, and live audio support — all powered by Gemini models.

## Repository Structure

```
ADK/
├── StatefulShoppingCartAgent/     # Text-based customer support agent
│   └── agent.py
├── StatefulShoppingCartLiveAgent/ # Voice/audio variant with live streaming
│   └── agent.py
├── MemoryBankAgent/               # Cross-session memory persistence demo
│   └── agent.py
├── GithubAnalyzerAgent/           # Parallel fan-out → gather pipeline
│   └── agent.py
├── Tools/
│   ├── ShoppingCartTool.py        # Cart, checkout, returns, image analysis
│   ├── ExternalAPITool.py         # Open Library book search
│   └── GitHubTool.py              # GitHub REST API (repos, issues, contributors)
├── config/
│   ├── settings.py                # Runtime settings with env-var overrides
│   └── catalog.py                 # Product catalog (IDs, prices, stock, keywords)
├── tests/
│   ├── conftest.py                # Loads .env, sets sys.path
│   ├── test_tools_unit.py         # Unit tests (no LLM required)
│   ├── test_shopping_cart_integration.py   # End-to-end shopping flows (Gemini API)
│   └── test_github_analyzer_integration.py # Parallel agent pipeline tests (Gemini + GitHub API)
├── requirements.txt
└── pytest.ini
```

## Agents

### StatefulShoppingCartAgent

A text-based customer support agent with full shopping lifecycle support.

- **Tools**: add to cart, checkout, product lookup, return tickets, image analysis, book search
- **State management**: cart contents, order history, lifetime value, and VIP status tracked via ADK session state (`user:`, `temp:`, `app:` key prefixes)
- **Callbacks**:
  - `before_tool_callback` — validates product IDs against catalog, blocks empty-cart checkout
  - `after_tool_callback` — counts consecutive errors and escalates to a human after a configurable threshold
  - `after_agent_callback` — persists conversation events to the ADK Memory Bank
- **Memory**: uses `PreloadMemoryTool` to greet returning users by name and recall preferences

### StatefulShoppingCartLiveAgent

Same capabilities as the text agent but configured for **live audio streaming** via Gemini's native audio modality (`gemini-live-2.5-flash-native-audio`), with a configurable voice (default: Aoede).

### MemoryBankAgent

A minimal agent demonstrating ADK's cross-session memory. Conversations are summarized and persisted so the agent remembers facts about the user across sessions.

### GithubAnalyzerAgent

Demonstrates **multi-agent orchestration** with ADK's `ParallelAgent` and `SequentialAgent`:

1. **Fan-out** — three sub-agents run in parallel, each calling a different GitHub API endpoint:
   - `RepoInfoAgent` — repo metadata (stars, forks, language)
   - `IssueTrackerAgent` — recent open issues
   - `ContributorAgent` — top contributors by commit count
2. **Gather** — a `GatherAgent` reads the collected state and composes a structured analysis report

## Tools

| Tool | Source | Description |
|---|---|---|
| `add_to_cart` | ShoppingCartTool | Adds a validated catalog product to the session cart |
| `checkout` | ShoppingCartTool | Finalizes cart into an order, tracks lifetime value and VIP status |
| `get_product_details` | ShoppingCartTool | Returns catalog info (name, price, stock) for a product ID |
| `create_return_ticket` | ShoppingCartTool | Opens a return/support ticket with configurable SLA |
| `analyze_product_image` | ShoppingCartTool | Heuristic keyword matching to identify products from image descriptions |
| `search_books` | ExternalAPITool | Queries the Open Library API for books by title/author |
| `get_repo_info` | GitHubTool | Fetches GitHub repo metadata via REST API |
| `get_repo_issues` | GitHubTool | Fetches recent open issues for a repo |
| `get_repo_contributors` | GitHubTool | Fetches top contributors by commit count |

## Testing

Tests are split into **unit** (no API keys needed) and **integration** (requires Gemini API + network).

```bash
# Unit tests only (fast, no API keys)
pytest tests/test_tools_unit.py -v

# Shopping cart integration (requires GOOGLE_API_KEY)
pytest tests/test_shopping_cart_integration.py -v

# GitHub analyzer integration (requires GOOGLE_API_KEY, optionally GITHUB_TOKEN)
pytest tests/test_github_analyzer_integration.py -v

# All tests
pytest -v
```

### What's Tested

- **Unit**: `AddToCartInput` Pydantic validation, catalog integrity, GitHub/Open Library API smoke tests
- **Shopping Cart Integration**: add-to-cart state updates, invalid product rejection, empty-cart checkout blocking, multi-turn state persistence, full purchase flow, return ticket creation, out-of-stock handling, session isolation between users, user-state sharing across sessions
- **GitHub Analyzer Integration**: parallel fan-out produces complete reports, correct repo referenced, gather agent structures output, graceful error handling for non-existent repos, session isolation

## Getting Started

1. **Install dependencies**
   ```bash
   cd ADK
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Set up environment variables** — create an `.env` file:
   ```env
   GOOGLE_API_KEY=your-gemini-api-key
   GITHUB_TOKEN=your-github-token    # optional, increases rate limits
   ```

3. **Run an agent** with the ADK CLI:
   ```bash
   adk run StatefulShoppingCartAgent
   ```

4. **Run tests**:
   ```bash
   pytest -v
   ```

## Configuration

All runtime settings live in `config/settings.py` and can be overridden via environment variables:

| Variable | Default | Description |
|---|---|---|
| `ADK_TEXT_MODEL` | `gemini-2.5-flash` | Model for text agents |
| `ADK_LIVE_MODEL` | `gemini-live-2.5-flash-native-audio` | Model for live audio agent |
| `ADK_MAX_TOOL_ERRORS_BEFORE_ESCALATE` | `3` | Consecutive errors before human escalation |
| `ADK_DEFAULT_LOYALTY_THRESHOLD` | `500` | Lifetime spend to earn VIP status |
| `ADK_VOICE_NAME` | `Aoede` | TTS voice for the live agent |
| `ADK_OPEN_LIBRARY_URL` | `https://openlibrary.org/search.json` | Open Library endpoint |

## Tech Stack

- **Google ADK** (`google-adk`) — agent framework with session state, memory, and multi-agent orchestration
- **Gemini** — LLM backend (text + live audio)
- **httpx** — async HTTP client for GitHub and Open Library APIs
- **Pydantic** — input validation for tool arguments
- **pytest + pytest-asyncio** — async test framework
