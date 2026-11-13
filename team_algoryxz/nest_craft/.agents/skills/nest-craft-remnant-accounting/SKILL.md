---
name: nest-craft-remnant-accounting
description: Empirical accounting and economic reporting rules for NEST-CRAFT, preventing linear compaction from being falsely reported as discrete sheet purchase savings, and tracking prime reusable remnant plate geometry.
license: Apache-2.0
---

# NEST-CRAFT Remnant Accounting Skill

Use this skill whenever calculating, reporting, benchmarking, or visualizing nesting efficiency, material savings, scrap generation, or financial ROI in NEST-CRAFT.

## Non-Negotiable Economic Truths

1. **Discrete Sheet Accounting vs Linear Compaction:**
   - In discrete plate manufacturing (e.g., standard $1000 \times 500\text{ mm}$ raw sheets), parts cannot be cut from fractional sheets.
   - If an algorithm nests 17 parts onto 3 sheets, **3 sheets must be purchased and loaded onto the CNC table**.
   - Reducing linear packing extent from $2,350\text{ mm}$ to $1,946\text{ mm}$ on the 3rd sheet **does NOT reduce sheet purchase count** (it remains 3 sheets).
   - **Never present linear compaction as a direct raw material purchasing discount.**

2. **Prime Reusable Remnant Valuation:**
   - Linear compaction is valuable because it preserves an unsevered, contiguous virgin plate section (a *prime remnant*).
   - If the leftover virgin area on the final sheet has minimum dimension $\ge 100\text{ mm}$ (e.g., $434 \times 500\text{ mm}$), it qualifies as **Reusable Prime Remnant Inventory**.
   - Valuation of remnant:
     $$\text{Remnant Value} = \text{Area}_{\text{remnant}} \times \text{Thickness} \times \text{Density} \times \text{Material Cost/kg} \times \text{Discount Factor}$$
   - Where $\text{Discount Factor} = 0.85$ (accounting for storage/handling depreciation).

3. **Multi-Seed Benchmark Reporting:**
   - Deterministic algorithms (BLF) run once per part order.
   - Stochastic algorithms (Simulated Annealing) must run across a fixed multi-seed grid (e.g., `seeds = [42, 101, 202, 303, 404]`).
   - Always report `Mean`, `Std Dev`, `Best`, and `Worst` linear extents and runtimes.
   - Never claim single-run "lucky" seeds as standard performance.
