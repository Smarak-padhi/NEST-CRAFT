# Laptop-Wide Reusable-Skill Inventory
**Inspected Locations:** `C:\Users\smara\.gemini\`, `C:\Users\smara\.agents\`, `C:\Users\smara\.codex\`, `C:\Users\smara\Desktop\Odisha AI hackathon\.agents\`  
**Date:** November 13, 2026  

---

| Source Location | Tool / Skill Name | Purpose | Scope | Security Status | NEST-CRAFT Relevance | Recommendation |
|:---|:---|:---|:---:|:---:|:---:|:---|
| `~/.gemini/config/plugins/ponytail` | `ponytail` (6 skills) | Anti-overengineering, YAGNI, standard library first | Global Plugin | Score 0 (SAFE) | **High** | **Retain active installation.** Zero duplication. |
| `~/.gemini/config/plugins/coderabbit` | `code-review`, `autofix` | Automated PR review & defect analysis | Global Plugin | Verified | Medium | Leverage for reviewing changes. |
| `~/.gemini/config/skills/` | `graphify` | Codebase architecture knowledge graph builder | Global Skill | Verified | Medium | Use for dependency analysis if needed. |
| `~/.gemini/config/skills/` | `gsd-plan-phase`, `gsd-execute-phase` | Structured plan/execute phase execution | Global Skill | Verified | High | Reference for phase breakdown. |
| `~/.gemini/builtin/skills/` | `generative_ui` | Interactive SVG/HTML UI visualizer | Built-in | Built-in | High | Used for CAD plate visualization. |
| `workspace/.agents/agents/` | `red-team.md`, `ml-benchmark.md` | Skeptical critique & adversarial verification | Workspace Subagents | Verified | High | Retained for Phase 2 independent critic gate. |
| `~/.gemini/config/skills/` | `swift-*`, `ios-*`, `android-*` | Mobile application development | Global Skills | Verified | None | Ignore (unrelated domains). |
| `~/.codex/skills/.system/` | `skill-creator`, `review-agent` | Private OpenAI Codex system routines | Private Codex | System Private | Low | Leave untouched in `.codex/`. |
