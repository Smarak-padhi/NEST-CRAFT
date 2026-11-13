# NEST-CRAFT Agent Skills Installation Manifest
**Generated:** November 13, 2026  
**Auditor / Integrator:** Senior Security Architect & Systems Reviewer  
**Platform:** Windows 11, Python 3.12.10, Antigravity 2.0  
**Security Gate:** NVIDIA SkillSpector v2.12.0  

---

## 1. SkillSpector Security Environment
- **Status:** Installed in isolated virtual environment.
- **Path:** `C:\Users\smara\.gemini\tooling\skillspector_env`
- **Binary:** `C:\Users\smara\.gemini\tooling\skillspector_env\Scripts\skillspector.exe`
- **Version:** `2.12.0` (from source commit `3c2c5d7a1ee148d228398070b91d3beaf0d73b11`, Apache-2.0)
- **Dependency Isolation:** 74 packages installed purely inside isolated virtual environment. Zero pollution of system Python.

---

## 2. Retained Global Installations
- **Skill / Plugin:** `ponytail` (6 skills: `ponytail`, `ponytail-review`, `ponytail-audit`, `ponytail-debt`, `ponytail-gain`, `ponytail-help`)
- **Status:** Pre-existing global plugin retained. **Zero duplication.**
- **Path:** `C:\Users\smara\.gemini\config\plugins\ponytail`
- **Source Commit:** `96608e078b2d5ea607c5c3b8b5a54d1c1fba6846`
- **Licence:** MIT
- **Security Audit:** Pure skills directory scanned: **Score 0 (SAFE)**.

---

## 3. Installed Global Skills (Adapted from `agent-rules-books`)
Source Repository: `https://github.com/ciembor/agent-rules-books`  
Source Commit: `893a88a6fce3a80c565bf39ac65021b43a8b2990`  
Licence: MIT  

| Skill Name | Installation Path | Nature & Adaptation | SkillSpector Score | Recommendation |
|:---|:---|:---|:---:|:---:|
| `a-philosophy-of-software-design` | `C:\Users\smara\.gemini\config\skills\a-philosophy-of-software-design` | Deep module design, cognitive load minimization, information hiding. Clean markdown. | **0 / 100** | **SAFE** |
| `refactoring` | `C:\Users\smara\.gemini\config\skills\refactoring` | Martin Fowler incremental refactoring. Sanitized line 355 ("no verification strategy" -> "without safety test verification"). | **7 / 100** | **SAFE** |

---

## 4. Installed Project-Specific Skills (NEST-CRAFT)
Workspace Path: `team_algoryxz/nest_craft/.agents/skills/`  
Mirrored Path for Discovery: `.agents/skills/`  

| Skill Name | Path | Purpose | Licence | SkillSpector Score | Recommendation |
|:---|:---|:---|:---:|:---:|:---:|
| `nest-craft-geometry-qa` | `team_algoryxz/nest_craft/.agents/skills/nest-craft-geometry-qa/SKILL.md` | Strict geometric invariants: zero pairwise overlap ($0.0000\text{ mm}^2$), thermal kerf clearance ($c > 0$), plate containment, inward-buffered feasible region ($H \ominus \mathcal{B}_c$). | Apache-2.0 | **0 / 100** | **SAFE** |
| `nest-craft-remnant-accounting` | `team_algoryxz/nest_craft/.agents/skills/nest-craft-remnant-accounting/SKILL.md` | Non-negotiable economic reporting: separates linear compaction from discrete plate purchasing; tracks prime reusable remnant plates ($\ge 100\text{ mm}$). | Apache-2.0 | **0 / 100** | **SAFE** |
| `industrial-ui-unslop` | `team_algoryxz/nest_craft/.agents/skills/industrial-ui-unslop/SKILL.md` | Adapted from `heydamir/unslop` (commit `97daa3eb`). Enforces high-contrast CAD themes, data-dense tabular layouts, suppression of AI decorative glows. Stripped all Node.js/Playwright scripts. | CC-BY-4.0 | **0 / 100** | **SAFE** |

---

## 5. Quarantined & Rejected Repositories
- **Quarantined:** `voltagent/awesome-design-md` (commit `fcc70284`). Reference-only; not installed as agent skills.
- **Rejected:** `rebelytics/one-skill-to-rule-them-all` (commit `d61bc31f`). Scored 100/CRITICAL in SkillSpector due to autonomous prompt/tool hijacking hooks (`AE1`). Not installed.

---

## 6. Antigravity Discovery Verification
Every installed skill path verified existing on disk and conforming to Antigravity `SKILL.md` frontmatter specification:
- `C:\Users\smara\.gemini\config\plugins\ponytail\skills\ponytail\SKILL.md` -> **True**
- `C:\Users\smara\.gemini\config\skills\a-philosophy-of-software-design\SKILL.md` -> **True**
- `C:\Users\smara\.gemini\config\skills\refactoring\SKILL.md` -> **True**
- `team_algoryxz/nest_craft/.agents/skills/nest-craft-geometry-qa\SKILL.md` -> **True**
- `team_algoryxz/nest_craft/.agents/skills/nest-craft-remnant-accounting\SKILL.md` -> **True**
- `team_algoryxz/nest_craft/.agents/skills/industrial-ui-unslop\SKILL.md` -> **True**
- `.agents/skills/nest-craft-geometry-qa\SKILL.md` -> **True**
- `.agents/skills/nest-craft-remnant-accounting\SKILL.md` -> **True**
- `.agents/skills/industrial-ui-unslop\SKILL.md` -> **True**
