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
System Design Studio runs directly inside the user's project repository under `.system-design/`. It introduces a Git-backed living state engine (`CURSOR.md`) that maintains active focus, causal hardware anchors, an examples registry, and a deferred rabbit-hole queue across sessions and model switches. The agent generates self-contained, interactive HTML teaching artifacts with visual mechanics and failure simulations, grounded in a comprehensive 50-cluster, 354-topic systems engineering syllabus.

## Core Surfaces
1. Landing / Product Showcase (`index.html`): High-craft technical product presentation demonstrating the `.system-design/` repository workflow, the living cursor architecture, hardware physics telemetry, and universal agent drop-in setups.
2. 50-Cluster Syllabus Browser (`curriculum.html`): Interactive filterable catalog across 6 engineering tiers (Transport, LLD, Storage, Consensus, Scaled Patterns, Flagships) with real-time search.
3. Technical Manual & Architecture Docs (`docs.html`): Filesystem contracts, CLI command reference, multi-agent setup guides, and BYO curriculum importer.

## Non-Negotiable Commitments
- 100% local and file-based (`.system-design/`); zero cloud lock-in, zero external SaaS/database dependencies.
- Grounded in physical reality: latency hierarchies, network packet loss, single points of failure, hardware throughput.
- Zero AI marketing slop: no generic card grids, no kickers/eyebrows, no gradient text masks, no zero-offset glowing shadows, strict WCAG AA contrast.
