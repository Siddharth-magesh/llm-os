# Available External MCP Servers

**Comprehensive catalog of MCP servers you can integrate with OSSARTH**

**Last Updated:** January 9, 2026

---

## What Are External MCP Servers?

External MCP servers are Node.js (or other language) packages that run as separate processes and communicate with OSSARTH via JSON-RPC 2.0. They provide specialized capabilities without requiring Python dependencies.

**How They Work:**
1. OSSARTH spawns server as subprocess
2. Communication via stdin/stdout (JSON-RPC 2.0)
3. Server provides tools (functions) you can call
4. Results returned to OSSARTH

---

## Currently Tested & Working

### Memory Server ✅
**Package:** `@modelcontextprotocol/server-memory`
**Purpose:** Knowledge graph for persistent memory
**Tools:** 9 (create_entities, create_relations, read_graph, etc.)
**Use Case:** Store and query information across sessions

### Sequential Thinking ✅
**Package:** `@modelcontextprotocol/server-sequential-thinking`
**Purpose:** Multi-step reasoning with thought revision
**Tools:** 1 (sequentialthinking)
**Use Case:** Break down complex problems step-by-step

---

## Official MCP Servers (Ready to Test)

### Category: File & Data Operations

#### 1. Filesystem
**Package:** `@modelcontextprotocol/server-filesystem`
**Purpose:** Secure file operations with access controls
**Tools:** Read, write, list, search files
**API Key:** No
**Use Case:** File management, content search

#### 2. Git
**Package:** `@modelcontextprotocol/server-git`
**Purpose:** Git repository operations
**Tools:** Read, search, manipulate repositories
**API Key:** No
**Use Case:** Version control, code history

---

### Category: Web & Network

#### 3. Fetch
**Package:** `@modelcontextprotocol/server-fetch`
**Purpose:** Web content fetching and conversion
**Tools:** HTTP requests, web scraping, content extraction
**API Key:** No
**Use Case:** Download web pages, API calls

#### 4. Brave Search
**Package:** `@modelcontextprotocol/server-brave-search`
**Purpose:** Web search via Brave Search API
**Tools:** Search the web
**API Key:** Yes (Brave Search API key)
**Use Case:** Real-time web search

#### 5. Firecrawl
**Package:** Various implementations
**Purpose:** Advanced web scraping and search
**Tools:** Crawl websites, extract structured data
**API Key:** Yes
**Use Case:** Large-scale web data extraction

---

### Category: Browser Automation

#### 6. Puppeteer
**Package:** `@modelcontextprotocol/server-puppeteer`
**Purpose:** Headless browser automation
**Tools:** Navigate, click, screenshot, extract
**API Key:** No
**Use Case:** Web testing, automation, scraping

#### 7. Playwright
**Package:** Various implementations
**Purpose:** Cross-browser automation
**Tools:** Browser control, testing
**API Key:** No
**Use Case:** Multi-browser testing

#### 8. Browserbase
**Package:** Various implementations
**Purpose:** Cloud browser automation
**Tools:** Remote browser control
**API Key:** Yes
**Use Case:** Scalable browser automation

#### 9. Chrome DevTools MCP
**Package:** Various implementations
**Purpose:** Control and inspect Chrome browsers
**Tools:** DevTools protocol access
**API Key:** No
**Use Case:** Browser debugging, inspection

---

### Category: Time & Utilities

#### 10. Time
**Package:** `@modelcontextprotocol/server-time`
**Purpose:** Time and timezone operations
**Tools:** Get time, convert timezones, format dates
**API Key:** No
**Use Case:** Time calculations, timezone conversion

#### 11. Everything (Reference Server)
**Package:** `@modelcontextprotocol/server-everything`
**Purpose:** Comprehensive test/reference server
**Tools:** Prompts, resources, multiple tool examples
**API Key:** No
**Use Case:** Testing MCP capabilities, learning

---

### Category: APIs & Integrations

#### 12. GitHub
**Package:** `@modelcontextprotocol/server-github`
**Purpose:** GitHub API integration
**Tools:** Repos, issues, PRs, commits
**API Key:** Yes (GitHub token)
**Use Case:** Code repository management

#### 13. GitLab
**Package:** Various implementations
**Purpose:** GitLab API integration
**Tools:** Similar to GitHub
**API Key:** Yes (GitLab token)
**Use Case:** GitLab project management

#### 14. Slack
**Package:** `@modelcontextprotocol/server-slack`
**Purpose:** Slack workspace integration
**Tools:** Send messages, read channels, manage workspace
**API Key:** Yes (Slack token)
**Use Case:** Team communication automation

#### 15. Google Maps
**Package:** `@modelcontextprotocol/server-google-maps`
**Purpose:** Maps and location services
**Tools:** Geocoding, directions, places
**API Key:** Yes (Google Maps API key)
**Use Case:** Location-based features

#### 16. Google Drive
**Package:** Various implementations
**Purpose:** Google Drive file operations
**Tools:** Upload, download, share files
**API Key:** Yes (Google OAuth)
**Use Case:** Cloud file management

#### 17. Supabase
**Package:** Various implementations
**Purpose:** Supabase database and auth
**Tools:** Database queries, authentication, edge functions
**API Key:** Yes (Supabase credentials)
**Use Case:** Backend as a service

---

### Category: Database & Storage

#### 18. PostgreSQL
**Package:** Various implementations
**Purpose:** PostgreSQL database operations
**Tools:** SQL queries, table management
**API Key:** Yes (DB credentials)
**Use Case:** Relational database access

#### 19. SQLite
**Package:** `@modelcontextprotocol/server-sqlite`
**Purpose:** SQLite database operations
**Tools:** SQL queries, local database
**API Key:** No
**Use Case:** Local data storage

#### 20. Redis
**Package:** Various implementations
**Purpose:** Redis cache operations
**Tools:** Key-value storage, caching
**API Key:** Yes (Redis credentials)
**Use Case:** Fast data caching

#### 21. AWS Knowledge Base
**Package:** Various implementations
**Purpose:** AWS knowledge retrieval
**Tools:** Query AWS docs and resources
**API Key:** Yes (AWS credentials)
**Use Case:** AWS documentation access

---

### Category: Monitoring & Error Tracking

#### 22. Sentry
**Package:** `@modelcontextprotocol/server-sentry`
**Purpose:** Error monitoring and tracking
**Tools:** Query errors, issues, releases
**API Key:** Yes (Sentry token)
**Use Case:** Application error monitoring

#### 23. Scout Monitoring
**Package:** Various implementations
**Purpose:** Performance monitoring
**Tools:** Performance metrics, error tracking
**API Key:** Yes
**Use Case:** Application performance analysis

---

### Category: AI & Machine Learning

#### 24. Exa
**Package:** Various implementations
**Purpose:** AI-optimized search
**Tools:** Semantic search, AI search
**API Key:** Yes
**Use Case:** Intelligent search

#### 25. MiniMax MCP
**Package:** Various implementations
**Purpose:** Text-to-speech, image, video generation
**Tools:** TTS, image gen, video gen APIs
**API Key:** Yes (MiniMax API)
**Use Case:** Multimedia content generation

#### 26. Kaggle MCP
**Package:** Various implementations
**Purpose:** Kaggle platform access
**Tools:** Datasets, models, competitions, notebooks
**API Key:** Yes (Kaggle credentials)
**Use Case:** Machine learning resources

---

### Category: Learning & Education

#### 27. Anki MCP
**Package:** Various implementations
**Purpose:** Anki flashcard integration
**Tools:** Create, review, manage flashcards
**API Key:** No
**Use Case:** Spaced repetition learning

---

### Category: Development Tools

#### 28. E2B
**Package:** Various implementations
**Purpose:** Code execution in sandboxes
**Tools:** Run code securely, test execution
**API Key:** Yes
**Use Case:** Safe code execution

#### 29. Next.js DevTools
**Package:** Various implementations
**Purpose:** Next.js development utilities
**Tools:** Project analysis, optimization
**API Key:** No
**Use Case:** Next.js development

#### 30. Xcode Build MCP
**Package:** Various implementations
**Purpose:** iOS/macOS app building
**Tools:** Build, test, deploy Apple apps
**API Key:** No
**Use Case:** Apple platform development

#### 31. Context 7
**Package:** Various implementations
**Purpose:** Cursor IDE documentation
**Tools:** Up-to-date Cursor docs
**API Key:** No
**Use Case:** IDE assistance

#### 32. DeepWiki by Devin
**Package:** Various implementations
**Purpose:** Codebase context and analysis
**Tools:** Code understanding, documentation
**API Key:** Yes
**Use Case:** Code intelligence

---

### Category: Cloud & Infrastructure

#### 33. Cloudflare
**Package:** Various implementations
**Purpose:** Cloudflare platform management
**Tools:** Workers, KV, R2, D1 operations
**API Key:** Yes (Cloudflare credentials)
**Use Case:** Edge computing, CDN

---

### Category: Financial & Data

#### 34. Alpha Vantage
**Package:** Various implementations
**Purpose:** Financial market data
**Tools:** Stocks, ETFs, forex, crypto data
**API Key:** Yes (Alpha Vantage key)
**Use Case:** Financial analysis

#### 35. Sophtron Financial
**Package:** Various implementations
**Purpose:** Banking and financial accounts
**Tools:** Balance, transactions, payments
**API Key:** Yes
**Use Case:** Financial data aggregation

#### 36. Bright Data
**Package:** Various implementations
**Purpose:** Web data extraction
**Tools:** Automated web access, scraping
**API Key:** Yes
**Use Case:** Large-scale data collection

---

## Community Servers (100+ Available)

Visit [mcpservers.org](https://mcpservers.org/) for a complete, up-to-date catalog of community-contributed servers including:

- **Language Translation** - Various translation APIs
- **Image Processing** - Image manipulation tools
- **Video Processing** - Video editing and conversion
- **Audio Tools** - Audio processing and transcription
- **Social Media** - Twitter, LinkedIn, Facebook integrations
- **Email Services** - Email automation
- **Calendar Tools** - Calendar management
- **Project Management** - Jira, Asana, Trello integrations
- **CRM Systems** - Salesforce, HubSpot integrations
- **Analytics** - Google Analytics, Mixpanel
- **Custom Business Logic** - Domain-specific tools

---

## How to Choose a Server

### No API Key Required (Easiest to Start)
1. **Memory** - Already tested ✅
2. **Sequential Thinking** - Already tested ✅
3. **Filesystem** - File operations
4. **Time** - Time utilities
5. **Fetch** - Web requests
6. **Everything** - Testing/learning
7. **Puppeteer** - Browser automation

### API Key Required (More Powerful)
1. **GitHub** - Code repository access
2. **Slack** - Team communication
3. **Brave Search** - Web search
4. **Google Maps** - Location services
5. **Sentry** - Error monitoring

---

## Installation Guide

### Test Any Server (Example: Filesystem)

```bash
# Test it first
cd D:\llm-os\tests\mcp
```

Create `test_filesystem_server.py`:
```python
import asyncio
from mcp_client_simple import SimpleMCPClient

async def test_filesystem():
    client = SimpleMCPClient("npx", ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allow"])

    await client.start()
    await client.initialize()

    tools = await client.list_tools()
    print(f"Tools: {[t['name'] for t in tools]}")

    # Test read
    result = await client.call_tool("read_file", {"path": "test.txt"})
    print(f"Result: {result}")

    await client.close()

asyncio.run(test_filesystem())
```

Run:
```bash
python test_filesystem_server.py
```

---

## Server Categories Summary

| Category | Count | Examples | API Keys |
|----------|-------|----------|----------|
| File & Data | 2 | Filesystem, Git | No |
| Web & Network | 3 | Fetch, Brave Search, Firecrawl | Mixed |
| Browser Automation | 4 | Puppeteer, Playwright, Browserbase | Mixed |
| Time & Utilities | 2 | Time, Everything | No |
| APIs & Integrations | 8 | GitHub, Slack, Google Maps | Yes |
| Database & Storage | 4 | PostgreSQL, SQLite, Redis | Mixed |
| Monitoring | 2 | Sentry, Scout | Yes |
| AI & ML | 3 | Exa, MiniMax, Kaggle | Yes |
| Learning | 1 | Anki | No |
| Development | 5 | E2B, Next.js, Xcode | Mixed |
| Cloud | 1 | Cloudflare | Yes |
| Financial | 3 | Alpha Vantage, Sophtron, Bright Data | Yes |
| Community | 100+ | Various | Various |

**Total Official Servers:** ~35
**Total Community Servers:** 100+
**Total Available:** 135+

---

## Recommended Next Servers to Test

Based on usefulness for OSSARTH:

### Priority 1 (No API Key)
1. **Filesystem** - Essential for file operations
2. **Time** - Useful for scheduling and time ops
3. **Fetch** - Web content fetching

### Priority 2 (Easy API Keys)
4. **GitHub** - Code repository management (free token)
5. **Brave Search** - Web search (free tier available)

### Priority 3 (Advanced)
6. **Puppeteer** - Browser automation
7. **SQLite** - Local database
8. **Slack** - Team integration (if needed)

---

## Testing New Servers

### Quick Test Template

```python
import asyncio
from mcp_client_simple import SimpleMCPClient

async def test_new_server():
    client = SimpleMCPClient("npx", ["-y", "@scope/package-name"])

    try:
        print("Starting server...")
        await client.start()

        print("Initializing...")
        await client.initialize()
        print(f"Server: {client.server_info}")

        print("Listing tools...")
        tools = await client.list_tools()
        for tool in tools:
            print(f"- {tool['name']}: {tool['description']}")

        print("\nTest successful!")

    finally:
        await client.close()

asyncio.run(test_new_server())
```

---

## Resources

- **Official Servers:** https://github.com/modelcontextprotocol/servers
- **Server Directory:** https://mcpservers.org/
- **MCP Specification:** https://modelcontextprotocol.io/
- **Documentation:** https://modelcontextprotocol.io/docs

---

## Next Steps

1. **Review this list** - Identify servers useful for your use case
2. **Test servers** - Start with no-API-key servers
3. **Get API keys** - For servers requiring authentication
4. **Integrate** - Add to OSSARTH configuration
5. **Customize** - Fork and modify if needed

---

**Summary:**
- 2 servers tested and working ✅
- 33+ official servers ready to test
- 100+ community servers available
- Simple test process established
- Integration path clear

Ready to add more servers to OSSARTH!
