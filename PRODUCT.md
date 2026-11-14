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
System Design Studio runs directly inside the user's project repository under `.system-design/`. It introduces a Git-backed living state engine (`CURSOR.md`) and instance preferences (`settings.json`) that maintain active focus, causal hardware anchors, an examples registry, and a deferred rabbit-hole queue across sessions and model switches. The agent enforces a strictly artifact-first teaching protocol for new topics, delivering full interactive HTML lessons with embedded simulators across 5 selectable design themes, while conducting subsequent deep-dive Q&A directly inline within chat. All of this is grounded in a comprehensive 50-cluster, 354-topic systems engineering syllabus.

## Core Surfaces
1. Landing / Product Showcase (`index.html`): High-craft technical product presentation demonstrating the `.system-design/` repository workflow, the living cursor architecture, hardware physics telemetry, and universal agent drop-in setups.
2. 50-Cluster Syllabus Browser (`curriculum.html`): Interactive filterable catalog across 5 engineering tiers (Tier 0: Transport, Tier 1: LLD & Object Modeling, Tier 2: HLD & Distributed Infra, Tier 3: Mobile & Offline Sync, Tier 4: ADRs & System Defense) with real-time search, collapsible tiers, and browser storage progress tracking.

## Non-Negotiable Commitments
- 100% local and file-based (`.system-design/`); zero cloud lock-in, zero external SaaS/database dependencies.
- Grounded in physical reality: latency hierarchies, network packet loss, single points of failure, hardware throughput.
- Zero AI marketing slop: no generic card grids, no kickers/eyebrows, no gradient text masks, no zero-offset glowing shadows, strict WCAG AA contrast.
- Lossless updater (`update.sh` + `merge-settings.py`): Updating never overwrites user learning state or custom theme preferences.
