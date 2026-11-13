# NEST-CRAFT Skills Security Audit Report
**Tool:** NVIDIA SkillSpector v2.12.0 (`--no-llm --format json`)  
**Date:** November 13, 2026  
**Auditor:** Senior Security Architect  

---

## 1. Executive Summary
Before approving any agent skill for installation into the Antigravity environment, a comprehensive static security scan was conducted using NVIDIA SkillSpector. All six candidate repositories were inspected, and installed skills were audited both pre- and post-adaptation.

---

## 2. Scan Results Across Target Repositories

| Target Repository | Inspected Scope | SkillSpector Score | Severity | Verdict | Key Finding |
|:---|:---|:---:|:---:|:---:|:---|
| `ponytail` (root) | Whole repo | 100 | CRITICAL | DO_NOT_INSTALL | Taint tracking in test runners and mocked keys. |
| `ponytail/skills` | Active plugin | **0** | **LOW** | **SAFE** | Zero findings. Pure clean Markdown skills. |
| `awesome-design-md` | Whole repo | 97 | CRITICAL | QUARANTINE | 41 findings: `curl \| sh` in docs, prompt heuristics. |
| `unslop` | Whole repo | 24 | MEDIUM | ADAPT | 6 findings: flags Node.js runner scripts. |
| `unslop/skills/unslop` | Pure skill | 45 | MEDIUM | ADAPT | Flags external video script invocation. |
| `one-skill-to-rule-them-all` | Whole repo | 100 | CRITICAL | **REJECT** | **99 findings: AE1 autonomous prompt hijacking hooks.** |
| `agent-rules-books` | 14 books | 93 | CRITICAL | ADAPT | 18 findings: false positives on "Forbidden Patterns" text in DDIA book. |

---

## 3. Scan Results on Installed & Adapted Skills

| Installed Skill | Location | Post-Adaptation Score | Risk Assessment | Identified Issues |
|:---|:---|:---:|:---:|:---|
| `ponytail` (plugin) | Global plugin directory | **0 / 100** | **SAFE** | None |
| `a-philosophy-of-software-design` | Global skills directory | **0 / 100** | **SAFE** | None |
| `refactoring` | Global skills directory | **7 / 100** | **SAFE** | 1 False Positive (`EA2` on "no verification" in descriptive code smell text). |
| `nest-craft-geometry-qa` | Project skills directory | **0 / 100** | **SAFE** | None |
| `nest-craft-remnant-accounting` | Project skills directory | **0 / 100** | **SAFE** | None |
| `industrial-ui-unslop` | Project skills directory | **0 / 100** | **SAFE** | None |

---

## 4. In-Depth Threat Analysis & Mitigations

### 4.1 Rejection of Autonomous Hooks (`one-skill-to-rule-them-all`)
- **Finding ID:** `AE1` (Autonomous Execution / Prompt Hijacking).
- **Mechanism:** Repository contains `pre-prompt-submit.sh` and `post-tool-execution.sh` intended to wrap every agent interaction, parse conversations, and autonomously mutate agent configuration without user confirmation.
- **Resolution:** **Strict Rejection.** Antigravity relies on transparent tool execution and explicit user approval gates. No hooks or autonomous execution scripts were installed.

### 4.2 Exclusion of Node.js / Playwright Dependencies (`unslop`)
- **Finding ID:** `AE1`, `RP1`.
- **Mechanism:** Original repository included `snapshot.mjs` and `story.mjs` which spawn headless Chromium processes to record video reels.
- **Resolution:** Stripped all `.mjs` scripts. Only the pure visual hierarchy, spacing, contrast, and layout principles were extracted into `industrial-ui-unslop`.

### 4.3 False Positive Resolution (`agent-rules-books`)
- **Finding ID:** `AR3` (Anti-Refusal / Jailbreak Heuristic).
- **Mechanism:** Scanner detected the phrase *"Forbidden Patterns"* in Martin Kleppmann's analysis of two-phase locking and distributed transactions.
- **Resolution:** Manual inspection verified zero executable code, network calls, or system commands. Installed only Ousterhout and Fowler architectural rulebooks.
