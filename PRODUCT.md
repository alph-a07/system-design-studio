# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack
static HTML/CSS, Vanilla JS (GitHub Pages)

## Users
Software engineers, systems architects, and technical learners studying distributed systems, low-level component design, consensus protocols, and scalable architectures using AI coding agents (Antigravity, Claude Code, Cursor, Codex, Gemini CLI).

## Problem
Conventional AI chat interfaces suffer from catastrophic context amnesia, lose learning lineage across session or model switches, and default to hand-waving buzzwords rather than first-principles engineering realities. Learners get superficial summaries without working through physical hardware trade-offs or interactive mental models.

## Mechanism & Solution
System Design Studio transforms an AI coding agent into a rigorous, interactive systems engineering studio directly inside the learner's local Git repository (`.system-design/`). It replaces ephemeral conversational chat with a persistent, file-backed living cursor (`CURSOR.md`) that tracks active focus, verified invariants, and deferred questions across sessions and model switches.

The learner runs terminal commands strictly twice: once for global machine setup (`install.sh`), and once for workspace initialization (`sds init`). All subsequent study is 100% in-chat:
1. **Deliver (`/sds-teach`)**: Generates standalone interactive visual lessons with tactile failure simulators and mandatory inline jargon tooltips (tap or hover any buzzword for instant plain-English explanations).
2. **Defend (Direct Chat Reply)**: Injects unannounced real-world chaos (asymmetric network partitions, clock skew, disk fsync ceilings) cold in chat, requiring the learner to defend their architectural reasoning before advancement.
3. **Verify (`/sds-complete`)**: Verifies mastery proof, advances the cursor, auto-synthesizes active learning study notes (Hypothesis ➔ Friction ➔ Invariant ➔ Rules of Thumb) in Git Markdown, logs an interview-ready ADR in `DECISIONS.md`, and commits state to Git.

Supported by a live localhost visual workbench (`sds dashboard` on `:8420`), built-in quantitative systems math functions (BDP, Little's Law, quorum size, consistent hashing migration, cache sizing), and 5 customizable designer themes.

## Core Surfaces
1. Landing / Product Showcase (`index.html`): High-craft technical product presentation demonstrating the `.system-design/` repository workflow, the living cursor architecture, hardware physics telemetry, and universal agent drop-in setups.
2. 50-Cluster Syllabus Browser (`curriculum.html`): Interactive filterable catalog across 5 engineering tiers (Tier 0: Transport, Tier 1: LLD & Object Modeling, Tier 2: HLD & Distributed Infra, Tier 3: Mobile & Offline Sync, Tier 4: ADRs & Self Evaluation) with real-time search, collapsible tiers, and browser storage progress tracking.

## Non-Negotiable Commitments
- 100% local and file-based (`.system-design/`); zero cloud lock-in, zero external SaaS/database dependencies.
- Grounded in physical reality: latency hierarchies, network packet loss, single points of failure, hardware throughput.
- Zero AI marketing slop: no generic card grids, no kickers/eyebrows, no gradient text masks, no zero-offset glowing shadows, strict WCAG AA contrast.
- Lossless updater (`update.sh` + `merge-settings.py`): Updating never overwrites user learning state or custom theme preferences.
