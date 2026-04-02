# BenchClaw Devlog

## 2026-04-01 — Building v2

---

### What is LabClaw?

[LabClaw](./labclaw/) is an open-source Python library that acts as a unified gateway to 2400+ scientific tools. It gives scientists and developers a single interface to query databases like PubMed, UniProt, ChEMBL, PubChem, OpenTargets, ClinicalTrials, and more — all through one Python SDK, REST API, CLI, or MCP server (for Claude Desktop).

Under the hood LabClaw has three main skills:

| Skill | What it does |
|---|---|
| `tooluniverse` | Wraps the [ToolUniverse](https://github.com/mims-harvard/ToolUniverse) SDK — 2000+ scientific database tools |
| `lifesci` | Life science domain reasoning via an LLM (experiment design, biological Q&A) |
| `write` | Scientific writing assistance (methods sections, abstracts, etc.) |

It exposes all of this through a FastAPI REST server on port 18802, an MCP server for Claude Desktop, and a Python SDK (`from labclaw.brain import execute, reason, write`).

---

### What is the Anthropic SDK?

The [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) (`pip install anthropic`) is the official client library for the Claude API. It lets you:

- Send messages to Claude models (`claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5`)
- Stream responses token-by-token with `client.messages.stream()`
- Use tool calling, structured outputs, vision, and extended thinking
- Access the Batches API (async, 50% cheaper) and Files API

The core pattern is:

```python
import anthropic

client = anthropic.Anthropic(api_key="...")

response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=2048,
    system="You are a helpful scientist.",
    messages=[{"role": "user", "content": "Explain CRISPR."}]
)
print(response.content[0].text)
```

For streaming (so output appears in real time):

```python
with client.messages.stream(model="claude-opus-4-6", max_tokens=4096, messages=[...]) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

---

### BenchClaw v1 — The CLI Auditor

`benchclaw.py` is a minimal command-line tool that audits a lab protocol using Claude. You run it like:

```bash
python benchclaw.py --protocol my_protocol.txt --output report.md
```

It sends the protocol text to `claude-sonnet-4-6` with a system prompt written as a senior molecular biologist, asks it to flag missing steps, safety concerns, QC issues, parameter problems, and improvements, then prints the report and optionally saves it as Markdown.

**What v1 is:**
- ~70 lines of Python
- Single function: `audit_protocol(text) -> str`
- CLI only, no UI
- One feature (auditing)
- Synchronous API call, no streaming

---

### BenchClaw v2 — The Streamlit Web App

`benchclaw_app.py` is a full Streamlit web app with three tools, all accessible from a sidebar navigation menu.

#### Feature 1: Protocol Auditor

Same core idea as v1 but with a web UI and streaming output. The user pastes a protocol into a text area, hits "Audit Protocol", and the Claude audit streams to the page in real time. Upgraded to `claude-opus-4-6` (the most capable model).

#### Feature 2: Literature Cross-Reference

New feature. The user pastes a protocol or describes an experiment. The app:
1. Sends the text to Claude to extract 3–6 relevant PubMed search terms (returns JSON)
2. Queries the [NCBI E-utilities API](https://www.ncbi.nlm.nih.gov/home/develop/api/) (free, no key required) with those terms
3. Fetches full paper records (title, authors, journal, year, abstract, PMID)
4. Displays expandable paper cards with links to PubMed

This is where LabClaw comes in — the `labclaw/src` path is added to `sys.path` so the app can access LabClaw internals, and the PubMed search uses the same NCBI E-utilities endpoints that LabClaw's `search_pubmed` tool wraps.

#### Feature 3: Protocol Generator

New feature. The user describes an experiment in plain English (e.g. "I want to knock out DNMT3A with CRISPR in HEK293 cells and measure methylation changes") and the app generates a complete, structured lab protocol. Options for detail level (standard, Nature Protocols–style, quick overview) and output format (numbered list, Markdown sections, step table). Streams in real time.

---

### v1 vs v2 Comparison

| | v1 | v2 |
|---|---|---|
| Interface | CLI | Streamlit web app |
| Features | Protocol audit only | Audit + Literature search + Protocol generation |
| Model | `claude-sonnet-4-6` | `claude-opus-4-6` |
| Streaming | No | Yes (real-time output) |
| PubMed integration | No | Yes (NCBI E-utilities + Claude keyword extraction) |
| Lines of code | ~70 | ~430 |

---

### How to Run

```bash
cd ~/Desktop/benchclaw
ANTHROPIC_API_KEY="sk-ant-..." /Users/nataliechen/Library/Python/3.9/bin/streamlit run benchclaw_app.py
```

Opens at `http://localhost:8501`.

---

### Roadmap

- [ ] Export audit reports and generated protocols as `.docx` / `.pdf`
- [ ] Protocol versioning — diff two protocols and audit the delta
- [ ] LabClaw deep integration — use `tooluniverse` skill to query UniProt, ChEMBL, PubChem directly from the UI
- [ ] Reagent cost estimator — parse a protocol and look up reagent prices
- [ ] Protocol sharing — save and share protocols via a short link
- [ ] Auth — add user accounts so researchers can save their history
