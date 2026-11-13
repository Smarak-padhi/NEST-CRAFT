# NEST-CRAFT Skills Architecture & Governance
**Platform:** Antigravity 2.0  
**Project:** NEST-CRAFT (Team Algoryxz)  
**Date:** November 13, 2026  

---

## 1. Architectural Philosophy
The NEST-CRAFT skills architecture operates on three strict principles:
1. **Separation of Concerns:** Global skills teach general software craftsmanship; project skills enforce domain invariants.
2. **YAGNI & Anti-Overengineering:** Only capabilities with direct, immediate utility are installed. Bloat and speculative tooling are forbidden.
3. **Explicit Gates:** Security inspection (SkillSpector) must validate every skill prior to execution.

---

## 2. Three-Tier Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│  Tier 1: Global Software Craftsmanship                      │
│  (C:\Users\smara\.gemini\config\)                           │
│  • ponytail (Anti-overengineering & YAGNI)                  │
│  • a-philosophy-of-software-design (Deep modules & APIs)    │
│  • refactoring (Fowler safe incremental transformation)     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Tier 2: CAD UI Craftsmanship & Visual Design               │
│  (team_algoryxz/nest_craft/.agents/skills/)                 │
│  • industrial-ui-unslop (Adapted from unslop)               │
│    - High-density shop-floor telemetry                     │
│    - Suppression of AI decorative slop                      │
│    - Blueprint high-contrast color scheme                   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Tier 3: Domain Invariants & Mathematical QA                │
│  (team_algoryxz/nest_craft/.agents/skills/)                 │
│  • nest-craft-geometry-qa                                   │
│    - Zero pairwise overlap: Area(Pi ∩ Pj) = 0.0000 mm²      │
│    - Strict kerf clearance: dist(Pi, Pj) ≥ c                │
│    - Part-in-part feasible region: H ⊖ Bc                   │
│  • nest-craft-remnant-accounting                            │
│    - Linear compaction ≠ discrete sheet purchase discount   │
│    - Prime remnant tracking (≥ 100 mm width)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Interaction with Subagents
- **`red-team` Subagent:** Audits implementations against `nest-craft-geometry-qa` and `nest-craft-remnant-accounting`.
- **`ml-benchmark` Subagent:** Enforces multi-seed reproducibility and fixed random seeds.
- **`code-review` Plugin:** Verifies code changes against `ponytail` and `refactoring` rules before acceptance.
