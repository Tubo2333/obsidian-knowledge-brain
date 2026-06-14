# Design Rationale & Architecture Decisions v2.0

> This document captures core design decisions for the Obsidian Knowledge Brain v2.0 and the "why" behind each.

---

## 1. Why Four-Layer Evolution? (v2.0 New)

### The Problem with v1.0's Single-Layer Design

v1.0 had one trigger: a weekly cron job. This meant:
- **Knowledge vacuum**: Close a session on Monday, the scanner runs Sunday — 6 days of stale knowledge
- **No real-time feedback**: The AI in session N+1 doesn't know what happened in session N
- **Single point of failure**: If the cron didn't fire (computer off), nothing was learned

### The v2.0 Solution: Four Independent Layers

| Layer | Trigger | Latency | Failure Mode |
|-------|---------|---------|-------------|
| L1: Instant Annotation | AI outputs [DECISION]/[ERROR] | Instant (in-session) | AI forgets to annotate (mitigated by Priority 0 in CLAUDE.md) |
| L2: Auto-Harvest | Stop hook + SessionStart hook | Seconds (session boundary) | Hook doesn't fire (mitigated by dual-hook design) |
| L3: Deep Analysis | Daily cron 14:07 | Hours | Computer off (mitigated by missed-scan catch-up in runner.py) |
| L4: Manual Sync | User says "收尾" | On demand | User forgets (mitigated by neat-freak reminder patterns) |

**Key insight**: No single layer needs to be 100% reliable. The four layers compensate for each other. A session missed by Stop hook is caught by SessionStart hook or daily cron.

---

## 2. Why SessionStart Hook? (v2.0 New)

### The Knowledge Vacuum Problem

User workflow: "Do work in Window A → handoff → close A → open Window B → continue."

Without SessionStart hook:
- Window A closes → Stop hook might not fire (Ctrl+C twice, kill -9, etc.)
- Window B opens → AI loads old Agent Memory → doesn't know what happened in Window A
- Wait until 14:07 cron → 3-hour vacuum

With SessionStart hook:
- Window B opens → SessionStart hook fires → scans 48h of unprocessed transcripts → harvests them → Agent Memory updated
- AI initializes with fresh knowledge from Window A
- Vacuum closed: seconds, not hours

### Design Choice: 48-Hour Window

Why 48 hours, not 24? Covers the "close at 11pm, open at 9am next day" pattern. Why not 7 days? Too wide — would repeatedly scan the same transcripts (harvested by Stop hook and cron already).

---

## 3. Why Root-Cause Analysis Instead of Counting? (v2.0 New)

### What v1.0 Did

```
Scan sessions → count error types → "shell-cli_curl_ssl: 4 occurrences" → approval card "(TBD)"
```

### What v2.0 Does

```
Scan sessions → find 6 error types → cluster by ROOT CAUSE:
  - shell-cli_curl_ssl + api-network_gfw_rst → SAME root: GFW interference
  - path-filesystem_file_not_found → root: Windows path separator
  - R-package_package_not_found → root: non-standard R library path
→ For each root cause, extract ONE principle that prevents ALL symptoms
→ Check if existing rules already cover this → action=reinforce (don't duplicate)
→ Generate concrete rule text, not "TBD"
```

### Design Choice: Heuristic KB + LLM Tiered Approach

```
Tier 1: Heuristic Knowledge Base (ROOT_CAUSE_KB)
  - Always runs, no API needed
  - Maps known symptoms → root causes → principles → rule IDs
  - Covers ~80% of real-world error patterns after initial setup

Tier 2: LLM Deep Analysis (optional, API required)
  - Runs when API key is available AND patterns >= 2
  - Discovers NOVEL root causes not in the KB
  - Provides richer rule text and merge suggestions
  - Failure is non-blocking: falls back to Tier 1

Tier 3: Review Flag
  - Errors not matched by KB or LLM → flagged "review"
  - Human reviews and (optionally) adds to KB
```

### Why Not LLM-Only?

- **Cost**: Every scan hitting the API adds up
- **Reliability**: API can be down, rate-limited, or blocked by GFW
- **Speed**: Heuristic analysis is instant; LLM adds 2-10 seconds
- **Transparency**: Heuristic matches are deterministic and debuggable

---

## 4. Why Agent Memory Dual-Write? (v2.0 New)

### v1.0: Rules Only in CLAUDE.md

CLAUDE.md is project-scoped. Rules compiled into it only take effect in that project. Cross-project rules are invisible to other projects.

### v2.0: CLAUDE.md + Agent Memory

```
compiler.py
    ├─→ CLAUDE.md (COMPILED:RULES block)
    │   Project-scoped, human-visible
    │
    └─→ Agent Memory (C:\Users\...\.claude\projects\d--C-file\memory\)
        Each rule → one .md file with YAML frontmatter
        MEMORY.md index rebuilt on every compile
        Loaded by ALL Claude Code sessions in this project scope
```

**Why Agent Memory?**
- **Cross-session**: Agent Memory is loaded at session start, before the AI's first response
- **Cross-project**: Memory files are shared across all sessions in the same Claude Code project scope
- **Fast updates**: Writing a single .md file is faster than editing CLAUDE.md's marked blocks
- **Granular**: Each rule is one file — easy to find, edit, or delete

### The Timing

```
SessionStart hook fires
    → harvests unprocessed transcripts → writes to vault
    → (if new patterns found) triggers compiler
    → compiler writes to Agent Memory
    → AI system prompt assembles → loads MEMORY.md + all memory files
    → AI starts with fresh rules
```

This is why SessionStart hook is so powerful: the entire learning cycle completes BEFORE the AI reads its context.

---

## 5. Why Atomic Writes + Defensive Parsing Everywhere? (v2.0 Hardened)

### v1.0's Fragility

v1.0 assumed well-formed input. Real-world transcripts have:
- Messages that are dicts, lists, or strings (Anthropic API format variation)
- YAML frontmatter with `datetime.date` objects (Python YAML parsing quirk)
- GBK-encoded Chinese characters on Windows stdout
- Missing or empty fields in session summaries

### v2.0's Defense-in-Depth

Every function that reads external data validates it:
```python
# analyzer.py: defensive taxonomy loading
taxonomy = yaml.safe_load(parts[1])
if not isinstance(taxonomy, dict):
    return {"categories": []}  # graceful degradation

# backup.py: defensive message parsing
if isinstance(msg, dict):
    msg_text = str(msg.get('content', ''))[:200]
elif isinstance(msg, list):
    msg_text = str(msg)[:200]
elif isinstance(msg, str):
    msg_text = msg[:200]

# reporter.py: defensive date handling
if hasattr(d, 'isoformat'):
    ds = d.isoformat()[5:]  # datetime.date → string
elif isinstance(d, str) and len(d) >= 10:
    ds = d[5:]
```

### UTF-8 Enforcement on Windows

```python
# runner.py: force UTF-8 on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
```

Without this, emoji and Chinese characters crash with `'gbk' codec can't encode character`.

---

## 6. Why No Persistent Daemon?

v2.0 is event-driven, not a persistent process. Three triggers cover all needs:

| Trigger | Frequency | CPU | Memory |
|---------|-----------|-----|--------|
| Stop hook | Per session end | <2s spike | ~50MB then released |
| SessionStart hook | Per session start | <2s spike | ~50MB then released |
| Cron | Once daily | <5s spike | ~50MB then released |

No background process. No memory leak. No "is it still running?" anxiety.

---

## 7. Design Anti-Patterns (What We Explicitly Avoid)

| Anti-Pattern | Why Not |
|---|---|
| Auto-apply rules without approval | AI making decisions autonomously defeats the purpose |
| Single trigger (cron only) | Knowledge vacuum of up to 7 days |
| Counting errors instead of analyzing root causes | "6 patterns found" is useless without "WHY they happen and HOW to prevent ALL of them" |
| Approval cards with "(TBD)" rule text | Creates busywork — the human has to write the rule from scratch |
| Piling up rules without merging | Rule count grows indefinitely, quality degrades |
| LLM-only analysis | Single point of failure, cost, latency |
| Persistent daemon | Complexity, memory leaks, "is it running?" anxiety |
| Real-time monitoring | Knowledge refinement doesn't need sub-second latency |
