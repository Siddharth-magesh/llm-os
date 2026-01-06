# LLM-OS: References and Resources

## Overview

This document compiles all references, research papers, tools, and resources related to the LLM-OS project.

---

## 1. Core Technologies

### 1.1 Model Context Protocol (MCP)

| Resource | Type | Link |
|----------|------|------|
| MCP Official Site | Documentation | [modelcontextprotocol.io](https://modelcontextprotocol.io/) |
| MCP Specification | Specification | [spec.modelcontextprotocol.io](https://spec.modelcontextprotocol.io/) |
| Anthropic MCP Announcement | Blog Post | [Introducing the Model Context Protocol](https://www.anthropic.com/news/model-context-protocol) |
| MCP Python SDK | GitHub | [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) |
| MCP TypeScript SDK | GitHub | [modelcontextprotocol/typescript-sdk](https://github.com/modelcontextprotocol/typescript-sdk) |
| MCP Servers Collection | GitHub | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) |
| Anthropic MCP Course | Course | [Introduction to MCP](https://anthropic.skilljar.com/introduction-to-model-context-protocol) |
| MCP + Docker | Blog Post | [Docker Blog](https://www.docker.com/blog/the-model-context-protocol-simplifying-building-ai-apps-with-anthropic-claude-desktop-and-docker/) |

### 1.2 LLM Providers

#### Ollama
| Resource | Type | Link |
|----------|------|------|
| Ollama Official Site | Website | [ollama.com](https://ollama.com/) |
| Ollama GitHub | GitHub | [ollama/ollama](https://github.com/ollama/ollama) |
| Ollama Model Library | Models | [ollama.com/library](https://ollama.com/library) |

#### Anthropic Claude
| Resource | Type | Link |
|----------|------|------|
| Claude API Documentation | Documentation | [docs.anthropic.com](https://docs.anthropic.com/) |
| Anthropic Python SDK | GitHub | [anthropics/anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python) |
| Claude Pricing | Pricing | [anthropic.com/pricing](https://www.anthropic.com/pricing) |

#### OpenAI
| Resource | Type | Link |
|----------|------|------|
| OpenAI API Documentation | Documentation | [platform.openai.com/docs](https://platform.openai.com/docs/) |
| OpenAI Python SDK | GitHub | [openai/openai-python](https://github.com/openai/openai-python) |

#### Other LLM Tools
| Resource | Type | Link |
|----------|------|------|
| llama.cpp | GitHub | [ggerganov/llama.cpp](https://github.com/ggerganov/llama.cpp) |
| vLLM | GitHub | [vllm-project/vllm](https://github.com/vllm-project/vllm) |
| LM Studio | Website | [lmstudio.ai](https://lmstudio.ai/) |
| Groq API | Website | [groq.com](https://groq.com/) |
| Together AI | Website | [together.ai](https://www.together.ai/) |

---

## 2. Research Papers

### 2.1 LLM Operating Systems

| Paper | Authors | Year | Link |
|-------|---------|------|------|
| AIOS: LLM Agent Operating System | Mei et al. (Rutgers) | 2024 | [arXiv:2403.16971](https://arxiv.org/abs/2403.16971v2) |
| MemGPT: Towards LLMs as Operating Systems | Packer et al. | 2023 | [arXiv:2310.08560](https://arxiv.org/abs/2310.08560) |
| OS-Copilot: Towards Generalist Computer Agents | Wu et al. | 2024 | [arXiv:2402.07456](https://arxiv.org/abs/2402.07456) |
| AgentOS: A High-Level Programming Language for AI Agents | - | 2024 | Research Paper |

### 2.2 AI Agents

| Paper | Authors | Year | Link |
|-------|---------|------|------|
| ReAct: Synergizing Reasoning and Acting in Language Models | Yao et al. | 2022 | [arXiv:2210.03629](https://arxiv.org/abs/2210.03629) |
| Toolformer: Language Models Can Teach Themselves to Use Tools | Schick et al. | 2023 | [arXiv:2302.04761](https://arxiv.org/abs/2302.04761) |
| WebGPT: Browser-assisted question-answering | OpenAI | 2022 | [arXiv:2112.09332](https://arxiv.org/abs/2112.09332) |

### 2.3 Related Resources

| Resource | Description | Link |
|----------|-------------|------|
| Illustrated LLM OS | Blog Post | [Hugging Face Blog](https://huggingface.co/blog/shivance/illustrated-llm-os) |
| Awesome LLM OS | Curated List | [GitHub](https://github.com/bilalonur/awesome-llm-os) |
| AIOS GitHub | Implementation | [agiresearch/AIOS](https://github.com/agiresearch/AIOS) |

---

## 3. Linux & OS Development

### 3.1 Base Distributions

| Distribution | Type | Link |
|--------------|------|------|
| Ubuntu | Official Site | [ubuntu.com](https://ubuntu.com/) |
| Debian | Official Site | [debian.org](https://www.debian.org/) |
| Arch Linux | Official Site | [archlinux.org](https://archlinux.org/) |
| Alpine Linux | Official Site | [alpinelinux.org](https://alpinelinux.org/) |

### 3.2 ISO Building Tools

| Tool | Description | Link |
|------|-------------|------|
| Cubic | Custom Ubuntu ISO Creator | [GitHub](https://github.com/PJ-Singh-001/Cubic) |
| live-build | Debian Live Build System | [Debian Wiki](https://wiki.debian.org/DebianLive) |
| Debian Live Manual | Documentation | [Live Manual](https://live-team.pages.debian.net/live-manual/) |
| Archiso | Arch Linux ISO Builder | [Arch Wiki](https://wiki.archlinux.org/title/Archiso) |

### 3.3 Linux Customization

| Resource | Type | Link |
|----------|------|------|
| Linux From Scratch | Guide | [linuxfromscratch.org](https://www.linuxfromscratch.org/) |
| Ubuntu Customization | Documentation | [Ubuntu Help](https://help.ubuntu.com/community/LiveCDCustomization) |
| Filesystem Hierarchy Standard | Specification | [FHS 3.0](https://refspecs.linuxfoundation.org/FHS_3.0/fhs-3.0.pdf) |

---

## 4. Development Frameworks

### 4.1 Python Libraries

| Library | Purpose | Link |
|---------|---------|------|
| Textual | Terminal UI Framework | [textual.textualize.io](https://textual.textualize.io/) |
| Rich | Rich Text Formatting | [GitHub](https://github.com/Textualize/rich) |
| Typer | CLI Framework | [typer.tiangolo.com](https://typer.tiangolo.com/) |
| Pydantic | Data Validation | [pydantic.dev](https://pydantic.dev/) |
| httpx | Async HTTP Client | [GitHub](https://github.com/encode/httpx) |
| asyncio | Async Programming | [Python Docs](https://docs.python.org/3/library/asyncio.html) |

### 4.2 TypeScript/JavaScript

| Library | Purpose | Link |
|---------|---------|------|
| Puppeteer | Browser Automation | [pptr.dev](https://pptr.dev/) |
| Playwright | Browser Automation | [playwright.dev](https://playwright.dev/) |
| Zod | Schema Validation | [zod.dev](https://zod.dev/) |

### 4.3 Rust (Optional)

| Library | Purpose | Link |
|---------|---------|------|
| Ratatui | Terminal UI | [GitHub](https://github.com/ratatui-org/ratatui) |
| Crossterm | Terminal Manipulation | [GitHub](https://github.com/crossterm-rs/crossterm) |
| Tokio | Async Runtime | [tokio.rs](https://tokio.rs/) |

---

## 5. Virtualization & Testing

### 5.1 Hypervisors

| Tool | Type | Link |
|------|------|------|
| VirtualBox | VM Hypervisor | [virtualbox.org](https://www.virtualbox.org/) |
| VMware Workstation Player | VM Hypervisor | [vmware.com](https://www.vmware.com/products/workstation-player.html) |
| QEMU | Emulator | [qemu.org](https://www.qemu.org/) |
| KVM | Kernel-based VM | [linux-kvm.org](https://www.linux-kvm.org/) |

### 5.2 Bootable USB Tools

| Tool | Platform | Link |
|------|----------|------|
| Rufus | Windows | [rufus.ie](https://rufus.ie/) |
| Balena Etcher | Cross-platform | [balena.io/etcher](https://www.balena.io/etcher/) |
| Ventoy | Cross-platform | [ventoy.net](https://www.ventoy.net/) |

---

## 6. Security Resources

### 6.1 Sandboxing

| Tool | Description | Link |
|------|-------------|------|
| Firejail | Sandbox Application | [GitHub](https://github.com/netblue30/firejail) |
| AppArmor | MAC Security | [Wiki](https://wiki.ubuntu.com/AppArmor) |
| seccomp | System Call Filtering | [Linux Docs](https://www.kernel.org/doc/html/latest/userspace-api/seccomp_filter.html) |

### 6.2 Security Best Practices

| Resource | Type | Link |
|----------|------|------|
| OWASP Top 10 | Security Guide | [owasp.org](https://owasp.org/www-project-top-ten/) |
| CIS Benchmarks | Security Standards | [cisecurity.org](https://www.cisecurity.org/cis-benchmarks) |

---

## 7. Similar Projects

### 7.1 AI Operating Systems

| Project | Description | Link |
|---------|-------------|------|
| AIOS | LLM Agent OS Research | [GitHub](https://github.com/agiresearch/AIOS) |
| MemGPT/Letta | LLM Memory Management | [GitHub](https://github.com/cpacker/MemGPT) |
| Open Interpreter | Natural Language Code Execution | [GitHub](https://github.com/OpenInterpreter/open-interpreter) |
| LangChain | LLM Application Framework | [langchain.com](https://www.langchain.com/) |

### 7.2 AI Assistants

| Project | Description | Link |
|---------|-------------|------|
| Claude Code | AI-powered CLI | [Anthropic](https://claude.ai/) |
| GitHub Copilot | AI Pair Programmer | [github.com/features/copilot](https://github.com/features/copilot) |
| Cursor | AI Code Editor | [cursor.com](https://cursor.com/) |
| Aider | AI Pair Programming | [GitHub](https://github.com/paul-gauthier/aider) |

---

## 8. Community & Support

### 8.1 Forums & Discussion

| Platform | Topic | Link |
|----------|-------|------|
| Reddit r/LocalLLaMA | Local LLM Discussion | [reddit.com/r/LocalLLaMA](https://www.reddit.com/r/LocalLLaMA/) |
| Reddit r/MachineLearning | ML Research | [reddit.com/r/MachineLearning](https://www.reddit.com/r/MachineLearning/) |
| Hacker News | Tech Discussion | [news.ycombinator.com](https://news.ycombinator.com/) |
| Discord - Ollama | Ollama Community | Discord Link |

### 8.2 Learning Resources

| Resource | Type | Link |
|----------|------|------|
| Andrej Karpathy - LLM OS | Video | YouTube |
| The AI Engineer Path | Course | Various |
| Prompt Engineering Guide | Guide | [promptingguide.ai](https://www.promptingguide.ai/) |

---

## 9. Tools & Utilities

### 9.1 Development Tools

| Tool | Purpose | Link |
|------|---------|------|
| VS Code | IDE | [code.visualstudio.com](https://code.visualstudio.com/) |
| Git | Version Control | [git-scm.com](https://git-scm.com/) |
| Docker | Containerization | [docker.com](https://www.docker.com/) |
| tmux | Terminal Multiplexer | [GitHub](https://github.com/tmux/tmux) |

### 9.2 Debugging & Profiling

| Tool | Purpose | Link |
|------|---------|------|
| htop | Process Viewer | [htop.dev](https://htop.dev/) |
| py-spy | Python Profiler | [GitHub](https://github.com/benfred/py-spy) |
| strace | System Call Tracer | Linux Standard |

---

## 10. Standards & Specifications

| Standard | Description | Link |
|----------|-------------|------|
| JSON-RPC 2.0 | RPC Protocol | [jsonrpc.org](https://www.jsonrpc.org/specification) |
| OpenAPI | API Specification | [openapis.org](https://www.openapis.org/) |
| CommonMark | Markdown Standard | [commonmark.org](https://commonmark.org/) |
| LSP | Language Server Protocol | [microsoft.github.io/language-server-protocol](https://microsoft.github.io/language-server-protocol/) |

---

## 11. Academic Institutions

| Institution | Contribution |
|-------------|--------------|
| Rutgers University | AIOS Research |
| UC Berkeley | MemGPT Research |
| Stanford | AI Agents Research |
| OpenAI | Foundation Models, WebGPT |
| Anthropic | Claude, MCP Protocol |
| Google DeepMind | AI Research |

---

## 12. Blogs & Articles

| Title | Source | Link |
|-------|--------|------|
| Complete Guide to MCP in 2025 | Keywords AI | [Link](https://www.keywordsai.co/blog/introduction-to-mcp) |
| Local LLM Hosting Guide 2025 | Medium | [Link](https://medium.com/@rosgluk/local-llm-hosting-complete-2025-guide-ollama-vllm-localai-jan-lm-studio-more-f98136ce7e4a) |
| What is MCP? | Descope | [Link](https://www.descope.com/learn/post/mcp) |
| How MCP Works | System Design Newsletter | [Link](https://newsletter.systemdesign.one/p/how-mcp-works) |

---

## 13. License Information

| Component | License |
|-----------|---------|
| MCP | MIT |
| Ollama | MIT |
| Textual | MIT |
| Ubuntu | Various (GPL, etc.) |
| Python | PSF |

---

## 14. Changelog

| Date | Update |
|------|--------|
| January 2026 | Initial document creation |

---

## 15. Contributing to References

To suggest additional references:
1. Ensure the resource is relevant to LLM-OS
2. Verify links are working
3. Include proper attribution
4. Categorize appropriately

---

*Document Version: 1.0*
*Last Updated: January 2026*
