#!/usr/bin/env python3
"""
lesson_builder.py — Component Node AST & Dual-Axis Compiler for System Design Studio.

Represents lessons as an ordered tree/stream of semantic typed component nodes.
Compiles directly and losslessly to:
1. First-Class Native GitHub Flavored Markdown (with callouts, pipe tables, formulas, traces)
2. Interactive Dynamic HTML (with dynamic sidebar tabs, popover tooltips, tactile simulators)

Takes away all HTML escaping, manual class formatting, and rigid section numbering
from the authoring agent.
"""

import os
import sys
import json
import re
import html
import math
import datetime
from typing import Optional, List, Dict, Any, Tuple, Union


# ==============================================================================
# 1. Individual Semantic Component Node Definitions
# ==============================================================================

class Node:
    """Base class for all semantic document nodes."""
    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError

    def render_markdown(self, context: Dict[str, Any]) -> str:
        raise NotImplementedError

    def render_html(self, context: Dict[str, Any]) -> str:
        raise NotImplementedError


class SectionNode(Node):
    def __init__(self, title: str, subtitle: str = "", badge: str = "", section_id: str = "", id: str = ""):
        # Strip any leading numbers for unindexed clean titles
        clean_title = re.sub(r'^(?:(?:Section|Phase)\s*\d+[:.]?\s*|\d+[.:]\s*)', '', title, flags=re.IGNORECASE).strip()
        self.title = clean_title
        self.subtitle = subtitle.strip()
        self.badge = badge.strip()
        self.section_id = section_id or id or re.sub(r'[^a-z0-9_-]', '-', clean_title.lower()).strip('-')

    def to_dict(self) -> Dict[str, Any]:
        d = {"type": "section", "title": self.title, "id": self.section_id}
        if self.subtitle:
            d["subtitle"] = self.subtitle
        if self.badge:
            d["badge"] = self.badge
        return d

    def render_markdown(self, context: Dict[str, Any]) -> str:
        sub = f"\n*{self.subtitle}*\n" if self.subtitle else ""
        return f"\n\n## {self.title}{sub}\n\n"

    def render_html(self, context: Dict[str, Any]) -> str:
        return ""  # Handled at section container level in HTML compiler


class SubsectionNode(Node):
    def __init__(self, title: str, level: int = 3):
        self.title = title.strip()
        self.level = max(2, min(5, level))

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "subsection", "title": self.title, "level": self.level}

    def render_markdown(self, context: Dict[str, Any]) -> str:
        hashes = "#" * self.level
        return f"\n{hashes} {self.title}\n\n"

    def render_html(self, context: Dict[str, Any]) -> str:
        return f'<h{self.level} class="text-base font-bold text-[var(--foreground)] mt-6 mb-2">{html.escape(self.title)}</h{self.level}>\n'


class DividerNode(Node):
    def __init__(self, style: str = "subtle"):
        self.style = style

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "divider", "style": self.style}

    def render_markdown(self, context: Dict[str, Any]) -> str:
        return "\n---\n\n"

    def render_html(self, context: Dict[str, Any]) -> str:
        return '<hr class="my-6 border-[var(--border)] opacity-60"/>\n'


class EditorialLeadNode(Node):
    def __init__(self, text: str):
        self.text = text.strip()

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "editorial_lead", "text": self.text}

    def render_markdown(self, context: Dict[str, Any]) -> str:
        return f"> *{self.text}*\n\n"

    def render_html(self, context: Dict[str, Any]) -> str:
        lead = self.text
        if not ("<span" in lead or "<code" in lead or "<strong" in lead or "<em" in lead):
            lead = html.escape(lead)
        return f'<div class="editorial-lead">\n  {lead}\n</div>\n'


class ParagraphNode(Node):
    def __init__(self, text: str, jargons: Optional[Dict[str, Any]] = None):
        self.text = text.strip()
        # jargons format: { "key": {"term": "...", "category": "...", "definition": "..."} }
        self.jargons: Dict[str, Dict[str, str]] = {}
        if jargons:
            for k, v in jargons.items():
                if isinstance(v, (list, tuple)) and len(v) >= 3:
                    self.jargons[k] = {"term": v[0], "category": v[1], "definition": v[2]}
                elif isinstance(v, dict):
                    self.jargons[k] = {
                        "term": v.get("term") or k,
                        "category": v.get("category") or "Concept",
                        "definition": v.get("definition") or v.get("body") or ""
                    }

    def to_dict(self) -> Dict[str, Any]:
        d = {"type": "paragraph", "text": self.text}
        if self.jargons:
            d["jargons"] = self.jargons
        return d

    def render_markdown(self, context: Dict[str, Any]) -> str:
        md_text = self.text
        # Substitute {{jargon:key}} tokens with clean bold term and register in context
        section_glossary = context.setdefault("current_section_glossary", {})
        all_glossary = context.setdefault("all_glossary", {})

        for k, j in self.jargons.items():
            token = f"{{{{jargon:{k}}}}}"
            if token in md_text:
                md_text = md_text.replace(token, f"**{j['term']}**")
            section_glossary[j['term']] = j
            all_glossary[j['term']] = j

        # If raw HTML tooltips or tags were passed directly, clean them for Markdown
        if "jargon-tooltip-wrapper" in md_text or ("<span" in md_text and "jargon" in md_text):
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("render_lesson", os.path.join(os.path.dirname(__file__), "render-lesson.py"))
                if spec and spec.loader:
                    rl = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(rl)
                    md_text = rl.clean_html_to_markdown(md_text)
            except Exception:
                pass

        return f"{md_text}\n\n"

    def render_html(self, context: Dict[str, Any]) -> str:
        html_text = self.text
        for k, j in self.jargons.items():
            token = f"{{{{jargon:{k}}}}}"
            tip_html = (
                f'<span class="jargon-tooltip-wrapper">'
                f'<span class="jargon-inline-cue" onclick="toggleJargonTooltip(this, event)">{html.escape(j["term"])}</span>'
                f'<span class="jargon-popover-card">'
                f'<span class="jargon-popover-header">'
                f'<span class="jargon-popover-title">💡 {html.escape(j["term"])}</span>'
                f'<span class="jargon-popover-badge">{html.escape(j["category"])}</span>'
                f'</span>'
                f'<span class="jargon-popover-body"><span class="jargon-popover-desc">{html.escape(j["definition"])}</span></span>'
                f'</span>'
                f'</span>'
            )
            html_text = html_text.replace(token, tip_html)

        return f"<p>\n  {html_text}\n</p>\n"


class ListNode(Node):
    def __init__(self, items: List[Union[str, Tuple[str, str], Dict[str, str]]], ordered: bool = False):
        self.items = items
        self.ordered = ordered

    def to_dict(self) -> Dict[str, Any]:
        formatted = []
        for it in self.items:
            if isinstance(it, (list, tuple)) and len(it) >= 2:
                formatted.append({"title": it[0], "text": it[1]})
            elif isinstance(it, dict):
                formatted.append(it)
            else:
                formatted.append({"text": str(it)})
        return {"type": "list", "ordered": self.ordered, "items": formatted}

    def render_markdown(self, context: Dict[str, Any]) -> str:
        lines = []
        for idx, it in enumerate(self.items, 1):
            prefix = f"{idx}." if self.ordered else "-"
            if isinstance(it, (list, tuple)) and len(it) >= 2:
                lines.append(f"{prefix} **{it[0]}**: {it[1]}")
            elif isinstance(it, dict) and "title" in it:
                lines.append(f"{prefix} **{it['title']}**: {it.get('text', '')}")
            elif isinstance(it, dict):
                lines.append(f"{prefix} {it.get('text', '')}")
            else:
                lines.append(f"{prefix} {it}")
        return "\n".join(lines) + "\n\n"

    def render_html(self, context: Dict[str, Any]) -> str:
        tag = "ol" if self.ordered else "ul"
        cls = "list-decimal pl-5 space-y-1.5 text-xs text-[var(--muted-foreground)] my-3" if self.ordered else "list-disc pl-5 space-y-1.5 text-xs text-[var(--muted-foreground)] my-3"
        items_html = []
        for it in self.items:
            if isinstance(it, (list, tuple)) and len(it) >= 2:
                t0, t1 = str(it[0]), str(it[1])
                if not ("<span" in t0 or "<code" in t0): t0 = html.escape(t0)
                if not ("<span" in t1 or "<code" in t1 or "<strong" in t1 or "<em" in t1): t1 = html.escape(t1)
                items_html.append(f'  <li><strong>{t0}:</strong> {t1}</li>')
            elif isinstance(it, dict) and "title" in it:
                t0, t1 = str(it["title"]), str(it.get("text", ""))
                if not ("<span" in t0 or "<code" in t0): t0 = html.escape(t0)
                if not ("<span" in t1 or "<code" in t1 or "<strong" in t1 or "<em" in t1): t1 = html.escape(t1)
                items_html.append(f'  <li><strong>{t0}:</strong> {t1}</li>')
            elif isinstance(it, dict):
                t1 = str(it.get("text", ""))
                if not ("<span" in t1 or "<code" in t1 or "<strong" in t1 or "<em" in t1): t1 = html.escape(t1)
                items_html.append(f'  <li>{t1}</li>')
            else:
                t1 = str(it)
                if not ("<span" in t1 or "<code" in t1 or "<strong" in t1 or "<em" in t1): t1 = html.escape(t1)
                items_html.append(f'  <li>{t1}</li>')
        return f'<{tag} class="{cls}">\n' + "\n".join(items_html) + f'\n</{tag}>\n'


class QuoteNode(Node):
    def __init__(self, text: str, author: str = "", role: str = ""):
        self.text = text.strip()
        self.author = author.strip()
        self.role = role.strip()

    def to_dict(self) -> Dict[str, Any]:
        d = {"type": "quote", "text": self.text}
        if self.author:
            d["author"] = self.author
        if self.role:
            d["role"] = self.role
        return d

    def render_markdown(self, context: Dict[str, Any]) -> str:
        attr = ""
        if self.author:
            role_str = f", *{self.role}*" if self.role else ""
            attr = f"\n> — **{self.author}**{role_str}"
        return f'> "{self.text}"{attr}\n\n'

    def render_html(self, context: Dict[str, Any]) -> str:
        attr = ""
        if self.author:
            role_span = f'<span class="text-xs text-[var(--muted-foreground)]">, {html.escape(self.role)}</span>' if self.role else ""
            attr = f'<footer class="text-xs font-mono font-bold text-amber-400 mt-2">— {html.escape(self.author)}{role_span}</footer>'
        return (
            f'<blockquote class="p-4 rounded-xl bg-stone-900 border-l-4 border-amber-500 my-4">\n'
            f'  <p class="text-sm italic text-[var(--foreground)] m-0">"{html.escape(self.text)}"</p>\n'
            f'  {attr}\n'
            f'</blockquote>\n'
        )


class DilemmaNode(Node):
    def __init__(
        self,
        title: str = "The Core Architectural Dilemma",
        lead: str = "",
        extremes: Optional[List[Union[Tuple[str, str, str], Dict[str, str]]]] = None,
        resolution_preview: str = "",
        question: str = "",
        concrete_impact: str = ""
    ):
        self.title = (title or question or "The Core Architectural Dilemma").strip()
        self.lead = (lead or concrete_impact or question).strip()
        self.extremes: List[Dict[str, str]] = []
        if extremes:
            for e in extremes:
                if isinstance(e, (list, tuple)) and len(e) >= 3:
                    self.extremes.append({"label": e[0], "metric": e[1], "description": e[2]})
                elif isinstance(e, dict):
                    self.extremes.append(e)
        self.resolution_preview = resolution_preview.strip()

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "type": "dilemma",
            "title": self.title,
            "lead": self.lead,
            "extremes": self.extremes
        }
        if self.resolution_preview:
            d["resolution_preview"] = self.resolution_preview
        return d

    def render_markdown(self, context: Dict[str, Any]) -> str:
        lines = [f"> [!WARNING] ⚡ {self.title}", f">\n> {self.lead}\n>"]
        for ext in self.extremes:
            lines.append(f"> - **{ext['label']}:** {ext['description']}")
            if "metric" in ext and ext["metric"]:
                lines.append(f">   *Physical Limit / Math*: `{ext['metric']}`")
        if self.resolution_preview:
            lines.append(f">\n> **The Resolution Path:** {self.resolution_preview}")
        return "\n".join(lines) + "\n\n"

    def render_html(self, context: Dict[str, Any]) -> str:
        items = []
        for ext in self.extremes:
            metric_val = ext.get("metric", "")
            metric_html = f'<br/><span class="text-amber-400 font-mono font-bold">Physical Limit / Math:</span> {metric_val if ("<span" in metric_val or "<code" in metric_val) else html.escape(metric_val)}' if metric_val else ""
            desc = ext.get("description", "")
            if not ("<span" in desc or "<div" in desc or "<code" in desc or "<strong" in desc or "<em" in desc):
                desc = html.escape(desc)
            label = ext.get("label", "")
            if not ("<span" in label or "<code" in label):
                label = html.escape(label)
            items.append(
                f'    <li><strong>{label}:</strong> {desc}\n'
                f'      {metric_html}\n'
                f'    </li>'
            )
        items_block = "\n".join(items)
        res_preview = self.resolution_preview
        if res_preview and not ("<span" in res_preview or "<code" in res_preview):
            res_preview = html.escape(res_preview)
        preview_block = f'<p class="text-xs text-amber-300 font-mono mt-3 mb-0"><strong>Resolution Path:</strong> {res_preview}</p>' if res_preview else ""

        lead_text = self.lead
        if not ("<span" in lead_text or "<div" in lead_text or "<code" in lead_text or "<strong" in lead_text or "<em" in lead_text):
            lead_text = html.escape(lead_text)

        return (
            f'<div class="callout-box callout-dilemma my-4">\n'
            f'  <div class="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider mb-1">⚡ {html.escape(self.title)}</div>\n'
            f'  <p class="text-sm text-[var(--foreground)] m-0 leading-relaxed">\n    {lead_text}\n  </p>\n'
            f'  <ul class="text-xs text-[var(--muted-foreground)] mt-2 mb-0 space-y-1.5 list-disc pl-4">\n'
            f'{items_block}\n'
            f'  </ul>\n'
            f'{preview_block}\n'
            f'</div>\n'
        )


class CalloutNode(Node):
    VALID_KINDS = {
        "invariant": ("text-emerald-400", "🔒", "IMPORTANT"),
        "trap": ("text-rose-400", "⚠️", "CAUTION"),
        "mechanism": ("text-blue-400", "⚙️", "NOTE"),
        "tradeoff": ("text-amber-400", "⚖️", "WARNING"),
        "dilemma": ("text-amber-400", "⚡", "WARNING"),
        "takeaway": ("text-indigo-400", "💡", "TIP"),
        "tip": ("text-indigo-400", "💡", "TIP"),
        "note": ("text-blue-400", "ℹ️", "NOTE")
    }

    def __init__(self, kind: str, title: str, text: str):
        self.kind = kind.lower() if kind.lower() in self.VALID_KINDS else "mechanism"
        self.title = title.strip()
        self.text = text.strip()

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "callout", "kind": self.kind, "title": self.title, "text": self.text}

    def render_markdown(self, context: Dict[str, Any]) -> str:
        color, icon, alert_type = self.VALID_KINDS[self.kind]
        text_lines = self.text.split("\n")
        body_bq = "\n".join([f"> {line}" for line in text_lines])
        return f"> [!{alert_type}] {icon} {self.title}\n>\n{body_bq}\n\n"

    def render_html(self, context: Dict[str, Any]) -> str:
        color, icon, alert_type = self.VALID_KINDS[self.kind]
        body = self.text
        if not ("<span" in body or "<code" in body or "<strong" in body or "<em" in body):
            body = html.escape(body)
        return (
            f'<div class="callout-box callout-{self.kind} my-4">\n'
            f'  <div class="text-xs font-mono font-bold {color} uppercase tracking-wider mb-1">{icon} {html.escape(self.title)}</div>\n'
            f'  <p class="text-xs text-[var(--foreground)] leading-relaxed m-0">{body}</p>\n'
            f'</div>\n'
        )


class AnalogyNode(Node):
    def __init__(self, title: str, category: str, mental_model: str, mapping: Optional[List[Dict[str, str]]] = None):
        self.title = title.strip()
        self.category = category.strip()
        self.mental_model = mental_model.strip()
        self.mapping = mapping or []

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "type": "analogy",
            "title": self.title,
            "category": self.category,
            "mental_model": self.mental_model
        }
        if self.mapping:
            d["mapping"] = self.mapping
        return d

    def render_markdown(self, context: Dict[str, Any]) -> str:
        lines = [
            f"> [!TIP] 💡 Intuitive Mental Model: {self.title} *({self.category})*",
            ">",
            f"> {self.mental_model}"
        ]
        if self.mapping:
            lines.append(">\n> | Real-World Concept | Distributed Systems Reality |")
            lines.append("> | :--- | :--- |")
            for m in self.mapping:
                lines.append(f"> | {m.get('physical', '')} | {m.get('systems', '')} |")
        return "\n".join(lines) + "\n\n"

    def render_html(self, context: Dict[str, Any]) -> str:
        mapping_html = ""
        if self.mapping:
            rows = []
            for m in self.mapping:
                p_val = m.get("physical", "")
                s_val = m.get("systems", "")
                if not ("<span" in p_val or "<code" in p_val): p_val = html.escape(p_val)
                if not ("<span" in s_val or "<code" in s_val): s_val = html.escape(s_val)
                rows.append(f'<tr><td class="p-1 border border-stone-800">{p_val}</td><td class="p-1 border border-stone-800">{s_val}</td></tr>')
            mapping_html = f'<table class="w-full text-[11px] font-mono mt-3 border-collapse text-[var(--muted-foreground)]"><thead><tr class="text-amber-300"><th class="p-1 text-left border border-stone-800">Real-World Concept</th><th class="p-1 text-left border border-stone-800">Systems Reality</th></tr></thead><tbody>{"".join(rows)}</tbody></table>'

        mm_text = self.mental_model
        if not ("<span" in mm_text or "<div" in mm_text or "<code" in mm_text or "<strong" in mm_text or "<em" in mm_text):
            mm_text = html.escape(mm_text)

        return (
            f'<div class="analogy-card">\n'
            f'  <div class="analogy-header">\n'
            f'    <span class="analogy-title">💡 Intuitive Mental Model: {html.escape(self.title)}</span>\n'
            f'    <span class="analogy-pill">{html.escape(self.category)}</span>\n'
            f'  </div>\n'
            f'  <div class="analogy-body">\n'
            f'    <p>{mm_text}</p>\n'
            f'    {mapping_html}\n'
            f'  </div>\n'
            f'</div>\n'
        )


class BreakthroughNode(Node):
    def __init__(self, title: str, text: str = "", content: str = ""):
        self.title = title.strip()
        self.text = (text or content).strip()

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "breakthrough", "title": self.title, "text": self.text}

    def render_markdown(self, context: Dict[str, Any]) -> str:
        return f"> [!NOTE] ✨ Breakthrough Realization: {self.title}\n>\n> {self.text}\n\n"

    def render_html(self, context: Dict[str, Any]) -> str:
        return (
            f'<div class="aha-card">\n'
            f'  <div class="aha-header">\n'
            f'    <span class="aha-title">✨ Breakthrough Realization: {html.escape(self.title)}</span>\n'
            f'    <span class="aha-pill">Aha!</span>\n'
            f'  </div>\n'
            f'  <div class="aha-body">\n'
            f'    <p>{html.escape(self.text)}</p>\n'
            f'  </div>\n'
            f'</div>\n'
        )


class StepTraceNode(Node):
    def __init__(self, title: str, steps: List[Union[Tuple[str, str, str, str], Dict[str, str]]]):
        self.title = title.strip()
        self.steps: List[Dict[str, str]] = []
        for s in steps:
            if isinstance(s, (list, tuple)) and len(s) >= 4:
                self.steps.append({"time": s[0], "actor": s[1], "action": s[2], "consequence": s[3]})
            elif isinstance(s, dict):
                self.steps.append(s)

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "step_trace", "title": self.title, "steps": self.steps}

    def render_markdown(self, context: Dict[str, Any]) -> str:
        lines = [
            f"### ⏱️ Causal Execution Trace: {self.title}\n",
            "| Time / Step | Actor | Action & Mechanism | Consequence & Latency |",
            "| :--- | :--- | :--- | :--- |"
        ]
        for s in self.steps:
            lines.append(f"| `{s.get('time','')}` | **{s.get('actor','')}** | {s.get('action','')} | {s.get('consequence','')} |")
        return "\n".join(lines) + "\n\n"

    def render_html(self, context: Dict[str, Any]) -> str:
        rows = []
        for s in self.steps:
            rows.append(
                f'<tr class="border-b border-stone-800 hover:bg-stone-900/50">'
                f'<td class="p-2 font-mono text-amber-400 font-bold whitespace-nowrap">{html.escape(s.get("time",""))}</td>'
                f'<td class="p-2 font-semibold text-stone-200">{html.escape(s.get("actor",""))}</td>'
                f'<td class="p-2 text-stone-300">{html.escape(s.get("action",""))}</td>'
                f'<td class="p-2 text-stone-400 font-mono text-[11px]">{html.escape(s.get("consequence",""))}</td>'
                f'</tr>'
            )
        return (
            f'<div class="my-6 p-4 rounded-xl bg-stone-900/90 border border-stone-800">\n'
            f'  <div class="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider mb-2">⏱️ Causal Execution Trace: {html.escape(self.title)}</div>\n'
            f'  <div class="overflow-x-auto">\n'
            f'    <table class="w-full text-xs text-left border-collapse">\n'
            f'      <thead><tr class="text-[11px] font-mono text-stone-400 uppercase border-b border-stone-700 bg-stone-950/60"><th class="p-2">Time / Step</th><th class="p-2">Actor</th><th class="p-2">Action</th><th class="p-2">Consequence</th></tr></thead>\n'
            f'      <tbody>\n' + "\n".join(rows) + '\n      </tbody>\n'
            f'    </table>\n'
            f'  </div>\n'
            f'</div>\n'
        )


class ComparisonMatrixNode(Node):
    def __init__(
        self,
        title: str,
        headers: Optional[List[str]] = None,
        rows: Optional[List[Any]] = None,
        columns: Optional[List[str]] = None
    ):
        self.title = title.strip()
        self.headers = headers or columns or []
        self.rows = rows or []

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "comparison_matrix", "title": self.title, "headers": self.headers, "rows": self.rows}

    def render_markdown(self, context: Dict[str, Any]) -> str:
        lines = [f"### 📊 {self.title}\n"]
        lines.append("| " + " | ".join(self.headers) + " |")
        lines.append("| " + " | ".join([":---"] * len(self.headers)) + " |")
        for r in self.rows:
            if isinstance(r, dict):
                clean_cells = [str(v).replace("\n", " ").strip() for v in r.values()]
            else:
                clean_cells = [str(c).replace("\n", " ").strip() for c in r]
            lines.append("| " + " | ".join(clean_cells) + " |")
        return "\n".join(lines) + "\n\n"

    def render_html(self, context: Dict[str, Any]) -> str:
        th = "".join([f'<th class="p-2 text-left font-mono text-stone-300">{html.escape(h)}</th>' for h in self.headers])
        tbody = []
        for r in self.rows:
            if isinstance(r, dict):
                td = "".join([f'<td class="p-2 border-t border-stone-800">{html.escape(str(v))}</td>' for v in r.values()])
            else:
                td = "".join([f'<td class="p-2 border-t border-stone-800">{html.escape(str(c))}</td>' for c in r])
            tbody.append(f'<tr class="hover:bg-stone-900/60">{td}</tr>')

        return (
            f'<div class="my-6 p-4 rounded-xl bg-stone-900/80 border border-stone-800">\n'
            f'  <div class="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider mb-2">📊 {html.escape(self.title)}</div>\n'
            f'  <div class="overflow-x-auto">\n'
            f'    <table class="w-full text-xs text-left border-collapse">\n'
            f'      <thead><tr class="bg-stone-950/80 border-b border-stone-700">{th}</tr></thead>\n'
            f'      <tbody>\n' + "\n".join(tbody) + '\n      </tbody>\n'
            f'    </table>\n'
            f'  </div>\n'
            f'</div>\n'
        )


class FormulaNode(Node):
    def __init__(
        self,
        name: str,
        expression: str,
        variables: Optional[Dict[str, str]] = None,
        derivation: Optional[List[str]] = None,
        conclusion: str = ""
    ):
        self.name = name.strip()
        self.expression = expression.strip()
        self.variables = variables or {}
        self.derivation = derivation or []
        self.conclusion = conclusion.strip()

    def to_dict(self) -> Dict[str, Any]:
        d = {"type": "formula", "name": self.name, "expression": self.expression}
        if self.variables:
            d["variables"] = self.variables
        if self.derivation:
            d["derivation"] = self.derivation
        if self.conclusion:
            d["conclusion"] = self.conclusion
        return d

    def render_markdown(self, context: Dict[str, Any]) -> str:
        lines = [
            f"### 📐 {self.name}\n",
            "```math",
            self.expression,
            "```"
        ]
        if self.variables:
            lines.append("\n**Variables**:")
            for k, v in self.variables.items():
                lines.append(f"- `{k}`: {v}")
        if self.derivation:
            lines.append("\n**Derivation Steps**:")
            for idx, step in enumerate(self.derivation, 1):
                lines.append(f"{idx}. {step}")
        if self.conclusion:
            lines.append(f"\n> **Result / Physical Implication:** `{self.conclusion}`\n")
        return "\n".join(lines) + "\n\n"

    def render_html(self, context: Dict[str, Any]) -> str:
        vars_html = "".join([f'<li><code class="text-amber-300 font-bold">{html.escape(k)}</code>: {html.escape(v)}</li>' for k, v in self.variables.items()])
        vars_block = f'<ul class="text-xs text-[var(--muted-foreground)] space-y-1 list-disc pl-4 my-2">{vars_html}</ul>' if vars_html else ""
        deriv_html = "".join([f'<li>{html.escape(d)}</li>' for d in self.derivation])
        deriv_block = f'<ol class="text-xs text-stone-300 space-y-1 list-decimal pl-4 my-2">{deriv_html}</ol>' if deriv_html else ""
        conc_block = f'<div class="mt-2 text-xs font-mono font-bold text-emerald-400">Result: {html.escape(self.conclusion)}</div>' if self.conclusion else ""

        return (
            f'<div class="p-4 rounded-xl bg-stone-900 border border-stone-800 my-4">\n'
            f'  <div class="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider mb-1">📐 {html.escape(self.name)}</div>\n'
            f'  <div class="font-mono text-sm text-amber-300 p-2.5 rounded bg-stone-950 border border-stone-800 my-2">{html.escape(self.expression)}</div>\n'
            f'  {vars_block}\n'
            f'  {deriv_block}\n'
            f'  {conc_block}\n'
            f'</div>\n'
        )


class CodeBlockNode(Node):
    def __init__(self, language: str, code: str, filename: str = "", caption: str = ""):
        self.language = language.strip()
        self.code = code.strip()
        self.filename = filename.strip()
        self.caption = caption.strip()

    def to_dict(self) -> Dict[str, Any]:
        d = {"type": "code_block", "language": self.language, "code": self.code}
        if self.filename:
            d["filename"] = self.filename
        if self.caption:
            d["caption"] = self.caption
        return d

    def render_markdown(self, context: Dict[str, Any]) -> str:
        fn_header = f"// {self.filename}\n" if self.filename else ""
        caption_str = f"\n*{self.caption}*\n" if self.caption else ""
        return f"```{self.language}\n{fn_header}{self.code}\n```\n{caption_str}\n"

    def render_html(self, context: Dict[str, Any]) -> str:
        fn_bar = f'<div class="px-3 py-1 text-[11px] font-mono bg-stone-950 text-stone-400 border-b border-stone-800 flex justify-between"><span>{html.escape(self.filename)}</span><span>{html.escape(self.language)}</span></div>' if self.filename else ""
        cap = f'<div class="text-[11px] text-[var(--muted-foreground)] italic mt-1">{html.escape(self.caption)}</div>' if self.caption else ""
        return (
            f'<div class="my-4 rounded-xl overflow-hidden border border-stone-800 bg-stone-950">\n'
            f'  {fn_bar}\n'
            f'  <pre class="p-3 text-xs font-mono text-stone-200 overflow-x-auto leading-relaxed"><code>{html.escape(self.code)}</code></pre>\n'
            f'</div>\n{cap}\n'
        )


class SimulatorHtmlNode(Node):
    """
    Direct HTML Simulator Node.
    Empowers agents to author bespoke interactive tactile simulators directly in HTML,
    supporting custom SVG, Tailwind layouts, action buttons, failure injection controls,
    live telemetry counters, and custom event handlers without being boxed into rigid AST schemas.
    """
    def __init__(
        self,
        html: str = "",
        raw_html: str = "",
        script: str = "",
        markdown_trace: str = "",
        title: str = "",
        subtitle: str = "",
        **kwargs
    ):
        self.html = (html or raw_html or "").strip()
        self.script = script.strip()
        self.markdown_trace = markdown_trace.strip()
        self.title = (title or kwargs.get("model", "")).strip()
        self.subtitle = subtitle.strip()

        # If html is empty, construct a clean container shell using title/subtitle
        if not self.html:
            t = self.title or "Tactile Mechanics Simulator"
            st = self.subtitle or "Interactive physical systems simulation"
            self.html = (
                f'<!-- TACTILE INTERACTIVE MECHANICS SIMULATOR -->\n'
                f'<div class="my-8 p-5 rounded-2xl bg-[var(--card)] border border-[var(--card-border)]">\n'
                f'  <div class="flex items-center justify-between pb-4 border-b border-[var(--border)]">\n'
                f'    <div>\n'
                f'      <span class="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider">Tactile Mechanics Simulator</span>\n'
                f'      <h4 class="text-base font-bold text-[var(--foreground)] mt-0.5 mb-0">{t}</h4>\n'
                f'      <div class="text-xs text-[var(--muted-foreground)] mt-0.5">{st}</div>\n'
                f'    </div>\n'
                f'  </div>\n'
                f'</div>\n'
            )

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "type": "simulator_html",
            "html": self.html
        }
        if self.script:
            d["script"] = self.script
        if self.markdown_trace:
            d["markdown_trace"] = self.markdown_trace
        if self.title:
            d["title"] = self.title
        if self.subtitle:
            d["subtitle"] = self.subtitle
        return d

    def render_markdown(self, context: Dict[str, Any]) -> str:
        if self.markdown_trace:
            return self.markdown_trace.strip() + "\n\n"
        title = self.title or "Interactive Mechanics Simulator"
        sub = f"\n> *{self.subtitle}*" if self.subtitle else ""
        return (
            f"> [!NOTE] 🎮 Interactive Simulation Walkthrough: {title}{sub}\n"
            f">\n"
            f"> *The interactive HTML edition provides a live tactile failure simulator for this mechanism.*\n"
            f"> *In HTML mode, direct manipulation controls permit triggering baseline actions and failure injections to observe real-time queue stalls, buffer saturation, and recovery overhead.*\n\n"
        )

    def render_html(self, context: Dict[str, Any]) -> str:
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("render_lesson", os.path.join(os.path.dirname(__file__), "render-lesson.py"))
            if spec and spec.loader:
                rl = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(rl)
                return rl.sanitize_tooltips_to_spans(self.html) + "\n"
        except Exception:
            pass
        return self.html + "\n"


# Alias for backwards compatibility
SimulatorNode = SimulatorHtmlNode


class DefenseChallengeNode(Node):
    def __init__(
        self,
        title: str,
        scenario: str,
        prompts: List[Union[Tuple[str, str], Dict[str, str]]],
        constraints: Optional[List[str]] = None
    ):
        self.title = title.strip()
        self.scenario = scenario.strip()
        self.prompts: List[Dict[str, str]] = []
        for p in prompts:
            if isinstance(p, (list, tuple)) and len(p) >= 2:
                self.prompts.append({"label": p[0], "question": p[1]})
            elif isinstance(p, dict):
                self.prompts.append(p)
        self.constraints = constraints or []

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "type": "defense_challenge",
            "title": self.title,
            "scenario": self.scenario,
            "prompts": self.prompts
        }
        if self.constraints:
            d["constraints"] = self.constraints
        return d

    def render_markdown(self, context: Dict[str, Any]) -> str:
        lines = [
            f"## 🛡️ Self Evaluation Scenario: {self.title}\n",
            "> [!IMPORTANT] Contextual Sign-Off Scenario",
            f"> {self.scenario}"
        ]
        if self.constraints:
            lines.append(">\n> **Physical & System Constraints:**")
            for c in self.constraints:
                lines.append(f"> - {c}")
        lines.append("\n### Self Evaluation Prompts (Conclude on Your Terms):")
        for idx, p in enumerate(self.prompts, 1):
            lines.append(f"{idx}. **{p.get('label','')}:** {p.get('question','')}")
        return "\n".join(lines) + "\n\n"

    def render_html(self, context: Dict[str, Any]) -> str:
        prompts_html = []
        for p in self.prompts:
            prompts_html.append(
                f'      <li>\n'
                f'        <strong>{html.escape(p.get("label",""))}:</strong> {html.escape(p.get("question",""))}\n'
                f'      </li>'
            )
        prompts_block = "\n".join(prompts_html)
        constraints_html = "".join([f'<li>{html.escape(c)}</li>' for c in self.constraints])
        constraints_block = f'<div class="my-2 p-2.5 rounded bg-stone-950 border border-stone-800 text-xs font-mono text-amber-300"><div class="font-bold uppercase text-[10px] text-stone-400 mb-1">Constraints:</div><ul class="list-disc pl-4 space-y-0.5">{constraints_html}</ul></div>' if constraints_html else ""

        return (
            f'<div class="p-5 rounded-2xl bg-[var(--card)] border border-amber-500/40 my-6 space-y-4">\n'
            f'  <div class="flex items-center gap-2">\n'
            f'    <span class="text-xs font-mono font-bold px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-700">SELF EVALUATION SCENARIO</span>\n'
            f'  </div>\n'
            f'  <p class="text-sm text-[var(--foreground)] leading-relaxed m-0">\n'
            f'    {html.escape(self.scenario)}\n'
            f'  </p>\n'
            f'  {constraints_block}\n'
            f'  <div class="p-4 rounded-xl bg-stone-900 border border-stone-800 space-y-3">\n'
            f'    <div class="text-xs font-mono font-bold text-amber-400 uppercase">Self Evaluation Prompts (Conclude on Your Terms):</div>\n'
            f'    <ol class="text-xs text-[var(--foreground)] space-y-2.5 list-decimal pl-4 m-0 leading-relaxed">\n'
            f'{prompts_block}\n'
            f'    </ol>\n'
            f'  </div>\n'
            f'</div>\n'
        )


class MentalModelNode(Node):
    def __init__(self, statement: str, explanation: str):
        self.statement = statement.strip()
        self.explanation = explanation.strip()

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "mental_model", "statement": self.statement, "explanation": self.explanation}

    def render_markdown(self, context: Dict[str, Any]) -> str:
        return (
            f"> [!IMPORTANT] The Architectural Mental Model\n"
            f">\n"
            f"> **{self.statement}**\n"
            f">\n"
            f"> {self.explanation}\n\n"
        )

    def render_html(self, context: Dict[str, Any]) -> str:
        return (
            f'<div class="p-4 rounded-xl bg-stone-900 border border-stone-800 my-6">\n'
            f'  <div class="text-xs font-mono font-bold text-amber-400 uppercase tracking-wider mb-2">\n'
            f'    The Architectural Mental Model\n'
            f'  </div>\n'
            f'  <p class="text-sm text-[var(--foreground)] leading-relaxed m-0">\n'
            f'    <strong>{html.escape(self.statement)}</strong>\n'
            f'  </p>\n'
            f'  <p class="text-xs text-[var(--muted-foreground)] mt-2 mb-0 leading-relaxed">\n'
            f'    {html.escape(self.explanation)}\n'
            f'  </p>\n'
            f'</div>\n'
        )


class RawHtmlNode(Node):
    """Container for raw or legacy HTML content."""
    def __init__(self, raw_html: str = "", html: str = "", content: str = ""):
        self.raw_html = (raw_html or html or content or "").strip()

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "raw_html", "html": self.raw_html}

    def render_markdown(self, context: Dict[str, Any]) -> str:
        try:
            import importlib
            render_lesson = importlib.import_module("render-lesson")
            return render_lesson.clean_html_to_markdown(self.raw_html)
        except Exception:
            return re.sub(r'<[^>]+>', '', self.raw_html)

    def render_html(self, context: Dict[str, Any]) -> str:
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("render_lesson", os.path.join(os.path.dirname(__file__), "render-lesson.py"))
            if spec and spec.loader:
                rl = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(rl)
                return rl.sanitize_tooltips_to_spans(self.raw_html) + "\n"
        except Exception:
            pass
        return self.raw_html + "\n"


# ==============================================================================
# 2. Node Factory Map
# ==============================================================================

NODE_CLASSES = {
    "section": SectionNode,
    "subsection": SubsectionNode,
    "divider": DividerNode,
    "editorial_lead": EditorialLeadNode,
    "paragraph": ParagraphNode,
    "list": ListNode,
    "quote": QuoteNode,
    "dilemma": DilemmaNode,
    "callout": CalloutNode,
    "analogy": AnalogyNode,
    "breakthrough": BreakthroughNode,
    "aha": BreakthroughNode,
    "step_trace": StepTraceNode,
    "comparison_matrix": ComparisonMatrixNode,
    "formula": FormulaNode,
    "code_block": CodeBlockNode,
    "simulator": SimulatorHtmlNode,
    "simulator_html": SimulatorHtmlNode,
    "defense_challenge": DefenseChallengeNode,
    "mental_model": MentalModelNode,
    "raw_html": RawHtmlNode
}

def node_from_dict(d: Dict[str, Any]) -> Node:
    node_type = d.get("type", "").lower()
    cls = NODE_CLASSES.get(node_type)
    if not cls:
        # Fallback to paragraph node
        return ParagraphNode(text=str(d.get("text") or d.get("content") or json.dumps(d)))

    # Dispatch arguments based on node type
    kwargs = {k: v for k, v in d.items() if k != "type"}
    try:
        return cls(**kwargs)
    except Exception:
        # If schema mismatch, construct safely
        return ParagraphNode(text=str(d.get("text") or str(d)))


# ==============================================================================
# 3. LessonDocument AST Engine
# ==============================================================================

class LessonDocument:
    """
    Authoritative AST Document representation of a System Design Studio lesson.
    Maintains an ordered stream of semantic nodes and compiles losslessly to both
    Markdown and HTML formats.
    """

    def __init__(
        self,
        topic_id: str = "",
        title: str = "",
        subtitle: str = "",
        tier: str = "Tier 0 · System Design Core",
        cluster: str = "System Design",
        backward_anchor: str = "",
        forward_hook: str = "",
        theme_id: str = "slate-clean",
        full_depth: bool = False,
        tier_badge: str = "",
        cluster_badge: str = ""
    ):
        self.topic_id = topic_id
        self.slug = topic_id.replace("topic.", "").replace(".", "-")
        self.title = title.strip()
        self.subtitle = subtitle.strip()
        self.tier = (tier_badge or tier).strip()
        self.cluster = (cluster_badge or cluster).strip()
        self.backward_anchor = backward_anchor.strip()
        self.forward_hook = forward_hook.strip()
        self.theme_id = theme_id
        self.full_depth = full_depth
        self.embedded_javascript = ""
        self.nodes: List[Node] = []

    @property
    def tier_badge(self) -> str:
        return self.tier

    @property
    def cluster_badge(self) -> str:
        return self.cluster

    # Fluent Node Builders
    def add_node(self, node: Node) -> "LessonDocument":
        self.nodes.append(node)
        return self

    def add(self, node: Node) -> "LessonDocument":
        """Convenience alias for add_node."""
        return self.add_node(node)

    def add_section(self, title: str, subtitle: str = "", badge: str = "", section_id: str = "") -> "LessonDocument":
        return self.add_node(SectionNode(title, subtitle, badge, section_id))

    def add_subsection(self, title: str, level: int = 3) -> "LessonDocument":
        return self.add_node(SubsectionNode(title, level))

    def add_divider(self, style: str = "subtle") -> "LessonDocument":
        return self.add_node(DividerNode(style))

    def add_lead(self, text: str) -> "LessonDocument":
        return self.add_node(EditorialLeadNode(text))

    def add_paragraph(self, text: str, jargons: Optional[Dict[str, Any]] = None) -> "LessonDocument":
        return self.add_node(ParagraphNode(text, jargons))

    def add_list(self, items: List[Any], ordered: bool = False) -> "LessonDocument":
        return self.add_node(ListNode(items, ordered))

    def add_quote(self, text: str, author: str = "", role: str = "") -> "LessonDocument":
        return self.add_node(QuoteNode(text, author, role))

    def add_dilemma(
        self,
        title: str,
        lead: str,
        extremes: List[Any],
        resolution_preview: str = ""
    ) -> "LessonDocument":
        return self.add_node(DilemmaNode(title, lead, extremes, resolution_preview))

    def add_callout(self, kind: str, title: str, text: str) -> "LessonDocument":
        return self.add_node(CalloutNode(kind, title, text))

    def add_analogy(
        self,
        title: str,
        category: str,
        mental_model: str,
        mapping: Optional[List[Dict[str, str]]] = None
    ) -> "LessonDocument":
        return self.add_node(AnalogyNode(title, category, mental_model, mapping))

    def add_breakthrough(self, title: str, text: str) -> "LessonDocument":
        return self.add_node(BreakthroughNode(title, text))

    def add_step_trace(self, title: str, steps: List[Any]) -> "LessonDocument":
        return self.add_node(StepTraceNode(title, steps))

    def add_comparison_matrix(self, title: str, headers: List[str], rows: List[List[str]]) -> "LessonDocument":
        return self.add_node(ComparisonMatrixNode(title, headers, rows))

    def add_formula(
        self,
        name: str,
        expression: str,
        variables: Optional[Dict[str, str]] = None,
        derivation: Optional[List[str]] = None,
        conclusion: str = ""
    ) -> "LessonDocument":
        return self.add_node(FormulaNode(name, expression, variables, derivation, conclusion))

    def add_code(self, language: str, code: str, filename: str = "", caption: str = "") -> "LessonDocument":
        return self.add_node(CodeBlockNode(language, code, filename, caption))

    def add_simulator_html(
        self,
        html: str,
        script: str = "",
        markdown_trace: str = "",
        title: str = "",
        subtitle: str = ""
    ) -> "LessonDocument":
        """
        Embeds an agent-crafted bespoke interactive simulator directly as an HTML node.
        Unleashes 100% creative freedom for custom SVG, Tailwind layouts, and interactive controls.
        """
        if script and not self.embedded_javascript:
            self.embedded_javascript = script.strip()
        return self.add_node(SimulatorHtmlNode(html=html, script=script.strip(), markdown_trace=markdown_trace, title=title, subtitle=subtitle))

    def add_simulator(
        self,
        html: str = "",
        script: str = "",
        markdown_trace: str = "",
        title: str = "",
        subtitle: str = "",
        **kwargs
    ) -> "LessonDocument":
        """Convenience alias for adding a simulator HTML node."""
        raw = html or kwargs.get("raw_html", "")
        t = title or kwargs.get("model", "")
        return self.add_simulator_html(html=raw, script=script, markdown_trace=markdown_trace, title=t, subtitle=subtitle)

    def add_defense_challenge(
        self,
        title: str,
        scenario: str,
        prompts: List[Any],
        constraints: Optional[List[str]] = None
    ) -> "LessonDocument":
        return self.add_node(DefenseChallengeNode(title, scenario, prompts, constraints))

    def add_mental_model(self, statement: str, explanation: str) -> "LessonDocument":
        return self.add_node(MentalModelNode(statement, explanation))

    def add_raw_html(self, raw_html: str) -> "LessonDocument":
        return self.add_node(RawHtmlNode(raw_html=raw_html))

    def set_javascript(self, js: str) -> "LessonDocument":
        self.embedded_javascript = js.strip()
        return self

    def set_full_depth(self, enabled: bool = True) -> "LessonDocument":
        self.full_depth = enabled
        return self

    # Serialization
    def to_dict(self) -> Dict[str, Any]:
        return {
            "$schema": "https://system-design-studio.dev/schemas/lesson-ast.json",
            "meta": {
                "topicId": self.topic_id,
                "title": self.title,
                "subtitle": self.subtitle,
                "tier": self.tier,
                "cluster": self.cluster,
                "backwardAnchor": self.backward_anchor,
                "forwardHook": self.forward_hook,
                "themeId": self.theme_id,
                "fullDepth": self.full_depth
            },
            "nodes": [n.to_dict() for n in self.nodes],
            "embeddedJavascript": self.embedded_javascript
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LessonDocument":
        meta = data.get("meta", {})
        doc = cls(
            topic_id=meta.get("topicId") or data.get("TOPIC_ID") or "topic.unknown",
            title=meta.get("title") or data.get("LESSON_TITLE") or "System Design Lesson",
            subtitle=meta.get("subtitle") or data.get("LESSON_SUBTITLE") or "",
            tier=meta.get("tier") or data.get("TIER_BADGE") or "Tier 0 · System Design Core",
            cluster=meta.get("cluster") or data.get("CLUSTER_BADGE") or "Cluster",
            backward_anchor=meta.get("backwardAnchor") or data.get("BACKWARD_ANCHOR") or "",
            forward_hook=meta.get("forwardHook") or data.get("FORWARD_HOOK") or "",
            theme_id=meta.get("themeId") or data.get("THEME_ID") or "slate-clean",
            full_depth=meta.get("fullDepth") or bool(data.get("FULL_DEPTH", False))
        )
        doc.embedded_javascript = data.get("embeddedJavascript") or data.get("EMBEDDED_JAVASCRIPT") or ""

        # Parse AST nodes if present
        if "nodes" in data and isinstance(data["nodes"], list):
            for nd in data["nodes"]:
                if isinstance(nd, dict):
                    doc.add_node(node_from_dict(nd))
        else:
            # Legacy conversion from SECTION_1_BODY..SECTION_5_BODY
            default_badges = [
                "Physical Dilemma",
                "System Architecture",
                "Mechanics & Simulator",
                "Production Reality",
                "Self Evaluation"
            ]
            for i in range(1, 6):
                t_key = f"SECTION_{i}_TITLE"
                b_key = f"SECTION_{i}_BODY"
                if t_key in data or b_key in data:
                    title = data.get(t_key, f"Section {i}")
                    badge = default_badges[i - 1] if i <= len(default_badges) else f"Stage {i}"
                    doc.add_node(SectionNode(title=title, badge=badge, section_id=f"section-{i}"))
                    body = data.get(b_key, "")
                    doc.add_node(RawHtmlNode(raw_html=body))

        return doc

    # Compilation: First-Class Markdown
    def to_markdown(self) -> str:
        """
        Compiles the AST losslessly to first-class GitHub Flavored Markdown.
        Preserves callout alerts, pipe tables, step traces, formulas, and collects glossaries.
        """
        md = []
        md.append(f"# {self.title}\n")
        if self.full_depth:
            md.append(f"> **Hierarchy**: {self.tier} ➔ {self.cluster}  \n> **Topic ID**: `{self.topic_id}` | **Depth**: Full-Depth Mechanical Closure\n")
        else:
            md.append(f"> **Hierarchy**: {self.tier} ➔ {self.cluster}  \n> **Topic ID**: `{self.topic_id}` | **Format**: Complete Markdown Edition\n")

        if self.subtitle:
            md.append(f"*{self.subtitle}*\n")
        md.append("---\n")

        if self.backward_anchor or self.forward_hook:
            md.append(f"> **Backward Anchor**: {self.backward_anchor}  \n> **Forward Hook**: {self.forward_hook}\n")
            md.append("---\n")

        context: Dict[str, Any] = {"current_section_glossary": {}, "all_glossary": {}}

        for node in self.nodes:
            if isinstance(node, SectionNode):
                # Flush previous section glossary before starting new section
                if context["current_section_glossary"]:
                    md.append(self._render_markdown_glossary(context["current_section_glossary"]))
                    context["current_section_glossary"] = {}
            md.append(node.render_markdown(context))

        # Flush final section glossary
        if context["current_section_glossary"]:
            md.append(self._render_markdown_glossary(context["current_section_glossary"]))

        return "".join(md).strip() + "\n"

    def _render_markdown_glossary(self, glossary: Dict[str, Dict[str, str]]) -> str:
        lines = ["> 💡 **Jargon & Concepts Unpacked in this Section:**\n>"]
        for term, data in sorted(glossary.items()):
            cat = f" *({data['category']})*" if data.get("category") else ""
            lines.append(f"> - **{term}**{cat}: {data.get('definition','')}")
        return "\n".join(lines) + "\n\n"

    # Compilation: Dynamic HTML Panes
    def to_html_panes(self) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """
        Compiles the AST into dynamic HTML tabs and panes for lesson-template.html.
        Returns: (tabs_list, panes_list)
        tabs_list: [{id, title, badge, subtitle}]
        panes_list: [{id, title, badge, subtitle, body_html}]
        """
        tabs = []
        panes = []
        context: Dict[str, Any] = {}

        current_section_id = "section-1"
        current_section_title = self.title
        current_section_badge = ""
        current_section_subtitle = ""
        current_section_nodes: List[Node] = []

        def flush_section():
            nonlocal current_section_nodes, current_section_id, current_section_title, current_section_badge, current_section_subtitle
            pane_body = "\n".join([n.render_html(context) for n in current_section_nodes])
            tabs.append({
                "id": current_section_id,
                "title": current_section_title,
                "badge": current_section_badge,
                "subtitle": current_section_subtitle
            })
            panes.append({
                "id": current_section_id,
                "title": current_section_title,
                "badge": current_section_badge,
                "subtitle": current_section_subtitle,
                "body_html": pane_body
            })
            current_section_nodes = []

        seen_first_section = False
        for node in self.nodes:
            if isinstance(node, SectionNode):
                if seen_first_section:
                    flush_section()
                seen_first_section = True
                current_section_id = node.section_id or f"section-{len(tabs)+1}"
                current_section_title = node.title
                current_section_badge = node.badge
                current_section_subtitle = node.subtitle
            else:
                current_section_nodes.append(node)

        # Flush final section
        if current_section_nodes or seen_first_section:
            flush_section()

        # If no sections were explicitly added, wrap all in single section
        if not panes:
            panes.append({
                "id": "section-1",
                "title": self.title,
                "badge": "",
                "subtitle": self.subtitle,
                "body_html": "\n".join([n.render_html(context) for n in self.nodes])
            })
            tabs.append({"id": "section-1", "title": self.title, "badge": "", "subtitle": self.subtitle})

        return tabs, panes

    def to_html_components(self) -> Tuple[str, str]:
        """
        Compiles tabs and panes to HTML strings suitable for {{SECTION_TABS_HTML}}
        and {{SECTION_PANES_HTML}} placeholders in lesson-template.html.
        """
        tabs, panes = self.to_html_panes()
        total = len(tabs)
        
        default_stage_names = [
            "Physical Dilemma",
            "System Architecture",
            "Mechanics & Simulator",
            "Production Reality",
            "Self Evaluation"
        ]

        # 1. Render Tab Buttons
        tab_htmls = []
        for idx, tab in enumerate(tabs):
            i = idx + 1
            is_active = (idx == 0)
            active_class = " active" if is_active else ""
            indicator_text = str(i)
            stage_tag_class = "text-[var(--primary)] font-bold" if is_active else "text-[var(--muted-foreground)]"
            title_class = "text-[var(--foreground)]" if is_active else "text-[var(--muted-foreground)]"
            
            badge = tab.get("badge")
            if not badge:
                if total == 5 and idx < len(default_stage_names):
                    badge = default_stage_names[idx]
                else:
                    badge = f"Stage {i}"

            tab_htmls.append(
                f'          <!-- Tab {i} -->\n'
                f'          <button type="button" class="section-tab-btn{active_class} w-full text-left p-2.5 rounded-lg border flex items-start gap-2.5" data-target="{html.escape(tab["id"])}" onclick="switchSectionTab(\'{html.escape(tab["id"])}\')">\n'
                f'            <span class="tab-indicator font-mono text-xs font-bold w-5 h-5 rounded flex items-center justify-center flex-shrink-0">{indicator_text}</span>\n'
                f'            <div class="min-w-0">\n'
                f'              <div class="tab-stage-tag text-[9px] font-mono uppercase tracking-wider {stage_tag_class}">{html.escape(badge)}</div>\n'
                f'              <div class="tab-title text-xs font-semibold {title_class} truncate">{html.escape(tab["title"])}</div>\n'
                f'            </div>\n'
                f'          </button>'
            )
        tabs_str = "\n".join(tab_htmls)

        # 2. Render Panes
        pane_htmls = []
        for idx, pane in enumerate(panes):
            i = idx + 1
            is_active = (idx == 0)
            is_last = (idx == total - 1)
            active_class = " active" if is_active else ""
            
            badge = pane.get("badge")
            if not badge:
                if total == 5 and idx < len(default_stage_names):
                    badge = default_stage_names[idx]
                else:
                    badge = f"Stage {i}"
            
            header_badge_color = "text-amber-500" if is_last else "text-[var(--primary)]"
            header_badge_text = f"Stage {i} · {badge}"

            # Navigation buttons
            if idx > 0:
                prev_tab = tabs[idx - 1]
                prev_id = prev_tab["id"]
                prev_name = prev_tab.get("badge") or prev_tab["title"]
                if len(prev_name) > 20:
                    prev_name = prev_name[:18] + "…"
                prev_btn = (
                    f'<button type="button" class="px-3 py-1.5 rounded-lg border border-[var(--border)] text-xs font-medium hover:bg-[var(--card)] flex items-center gap-1.5 cursor-pointer" onclick="switchSectionTab(\'{html.escape(prev_id)}\')">\n'
                    f'            <span>←</span>\n'
                    f'            <span>Previous: {html.escape(prev_name)}</span>\n'
                    f'          </button>'
                )
            else:
                prev_btn = '<span></span>'

            if not is_last:
                next_tab = tabs[idx + 1]
                next_id = next_tab["id"]
                next_name = next_tab.get("badge") or next_tab["title"]
                if len(next_name) > 20:
                    next_name = next_name[:18] + "…"
                next_btn = (
                    f'<button type="button" class="px-4 py-2 rounded-lg bg-[var(--primary)] text-white text-xs font-bold hover:bg-[var(--primary-hover)] flex items-center gap-2 cursor-pointer" onclick="switchSectionTab(\'{html.escape(next_id)}\')">\n'
                    f'            <span>Next: {html.escape(next_name)}</span>\n'
                    f'            <span>→</span>\n'
                    f'          </button>'
                )
            else:
                next_btn = (
                    f'<div class="text-xs font-mono text-[var(--muted-foreground)]">\n'
                    f'            Ready to defend? Reply in chat to begin Socratic evaluation.\n'
                    f'          </div>'
                )

            pane_htmls.append(
                f'      <!-- PANE {i}: {html.escape(pane["title"].upper())} -->\n'
                f'      <article id="pane-{html.escape(pane["id"])}" class="section-pane{active_class} space-y-6">\n'
                f'        <header class="space-y-1.5 border-b border-[var(--border)] pb-4">\n'
                f'          <div class="text-xs font-mono font-bold uppercase tracking-wider {header_badge_color}">{html.escape(header_badge_text)}</div>\n'
                f'          <h2 class="text-2xl md:text-3xl font-extrabold tracking-tight text-[var(--foreground)]">{html.escape(pane["title"])}</h2>\n'
                f'        </header>\n'
                f'        <div class="narrative-prose">\n'
                f'{pane["body_html"]}\n'
                f'        </div>\n'
                f'        <div class="pt-8 border-t border-[var(--border)] flex justify-between items-center">\n'
                f'          {prev_btn}\n'
                f'          {next_btn}\n'
                f'        </div>\n'
                f'      </article>'
            )
        panes_str = "\n\n".join(pane_htmls)
        return tabs_str, panes_str

    def validate(self) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validates payload against pedagogical quality gates."""
        warnings = []
        metrics = {}

        # 1. Word count
        md_text = self.to_markdown()
        clean_words = re.findall(r"\b[A-Za-z0-9_-]+\b", re.sub(r"<[^>]+>", " ", md_text))
        word_count = len(clean_words)
        metrics["word_count"] = word_count

        min_words = 3500 if self.full_depth else 1800
        if word_count < min_words:
            mode = "Full-Depth Mechanical Closure" if self.full_depth else "Standard"
            warnings.append(f"Word count is {word_count} (< {min_words} words for {mode} mode).")

        # 2. Dilemma presence
        has_dilemma = any(isinstance(n, DilemmaNode) for n in self.nodes)
        if not has_dilemma:
            warnings.append("No DilemmaNode present in document AST.")

        # 3. Defense challenge presence
        has_defense = any(isinstance(n, DefenseChallengeNode) for n in self.nodes)
        if not has_defense:
            warnings.append("No DefenseChallengeNode present in document AST.")

        # 4. Jargon unpacking density
        jargon_count = sum(len(n.jargons) for n in self.nodes if isinstance(n, ParagraphNode))
        for n in self.nodes:
            if isinstance(n, RawHtmlNode):
                jargon_count += len(re.findall(r'class=["\'][^"\']*(?:jargon-card|jargon-tooltip-wrapper)[^"\']*["\']', n.raw_html))
        metrics["jargon_count"] = jargon_count
        min_jargons = 6 if self.full_depth else 3
        if jargon_count < min_jargons:
            warnings.append(f"Only {jargon_count} jargon unpackings defined (< {min_jargons} required).")

        # 5. Raw LaTeX tokens check
        raw_latex = re.findall(r"\\[a-zA-Z]+|\$[^\$]+\$", md_text)
        problematic = [m for m in raw_latex if any(tok in m for tok in ["\\approx", "\\log", "\\times", "\\le", "\\ge", "\\frac"])]
        if problematic:
            warnings.append(f"Uncompiled LaTeX math tokens detected in prose: {problematic[:3]}. Use Unicode (≈, ×, ≤).")

        return len(warnings) == 0, warnings, metrics

    def save(self, output_path: str, force: bool = False) -> Dict[str, Any]:
        is_valid, warnings, metrics = self.validate()
        if not is_valid and not force:
            print(f"[!] LessonDocument validation warnings for {self.topic_id}:", file=sys.stderr)
            for w in warnings:
                print(f"    ⚠️  {w}", file=sys.stderr)

        payload = self.to_dict()
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        metrics["output_path"] = os.path.abspath(output_path)
        metrics["is_valid"] = is_valid
        metrics["warnings"] = warnings
        return metrics


class SectionBuilder:
    """Fluent chaining builder for legacy tests and scripts."""
    def __init__(self, doc: "LessonBuilder", section_num: int):
        self.doc = doc
        self.section_num = section_num
        self.title = f"Section {section_num}"
        self.section_node: Optional[SectionNode] = None

    def set_title(self, title: str) -> "SectionBuilder":
        self.title = title
        if self.section_node:
            self.section_node.title = title
        else:
            self.section_node = SectionNode(title=title, section_id=f"section-{self.section_num}")
            self.doc.add_node(self.section_node)
        return self

    def _ensure_section(self):
        if not self.section_node:
            self.section_node = SectionNode(title=self.title, section_id=f"section-{self.section_num}")
            self.doc.add_node(self.section_node)

    def add_lead(self, text: str) -> "SectionBuilder":
        self._ensure_section()
        self.doc.add_lead(text)
        return self

    def add_paragraph(self, text: str) -> "SectionBuilder":
        self._ensure_section()
        self.doc.add_node(RawHtmlNode(raw_html=text))
        return self

    def add_dilemma(self, title: str, lead: str, ext1_label: str, ext1_math: str, ext1_desc: str, ext2_label: str, ext2_desc: str = "") -> "SectionBuilder":
        self._ensure_section()
        extremes = [(ext1_label, ext1_math, ext1_desc), (ext2_label, "", ext2_desc)]
        self.doc.add_dilemma(title, lead, extremes)
        return self

    def add_analogy(self, title: str, category: str, content: str) -> "SectionBuilder":
        self._ensure_section()
        self.doc.add_analogy(title, category, content)
        return self

    def add_mental_model(self, statement: str, explanation: str) -> "SectionBuilder":
        self._ensure_section()
        self.doc.add_mental_model(statement, explanation)
        return self

    def add_defense_scenario(self, title: str, context_paragraphs: List[str], defense_prompts: List[Tuple[str, str]]) -> "SectionBuilder":
        self._ensure_section()
        self.doc.add_defense_challenge(title, "\n\n".join(context_paragraphs), defense_prompts)
        return self


# Backward-compatible builder wrapper
class LessonBuilder(LessonDocument):
    """Backwards-compatible wrapper alias for LessonDocument."""
    def __init__(
        self,
        topic_id: str = "topic.unknown",
        title: str = "",
        subtitle: str = "",
        tier: str = "",
        cluster: str = "",
        lesson_title: str = "",
        lesson_subtitle: str = "",
        tier_badge: str = "",
        cluster_badge: str = "",
        **kwargs
    ):
        resolved_title = title or lesson_title or "System Design Lesson"
        resolved_subtitle = subtitle or lesson_subtitle or ""
        resolved_tier = tier or tier_badge or "Tier 0 · System Design Core"
        resolved_cluster = cluster or cluster_badge or "System Design"
        super().__init__(
            topic_id=topic_id,
            title=resolved_title,
            subtitle=resolved_subtitle,
            tier=resolved_tier,
            cluster=resolved_cluster,
            **kwargs
        )
        self._section_builders = {}

    def section(self, num: int) -> SectionBuilder:
        if num not in self._section_builders:
            self._section_builders[num] = SectionBuilder(self, num)
        return self._section_builders[num]

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["LESSON_TITLE"] = self.title
        d["LESSON_SUBTITLE"] = self.subtitle
        d["TIER_BADGE"] = self.tier
        d["CLUSTER_BADGE"] = self.cluster
        tabs, panes = self.to_html_panes()
        for idx, p in enumerate(panes, 1):
            d[f"SECTION_{idx}_TITLE"] = p["title"]
            d[f"SECTION_{idx}_BODY"] = p["body_html"]
        return d


# ==============================================================================
# 4. Legacy Functions for Backward Compatibility
# ==============================================================================

def build_jargon_tooltip(term: str, title: str, category: str, explanation: str, cue_type: str = "inline") -> str:
    term_clean = re.sub(r"^\*+|\*+$", "", term.strip()).strip()
    title_clean = re.sub(r"^\*+|\*+$", "", title.strip()).strip()
    cue_class = "jargon-pill-cue" if cue_type == "pill" else "jargon-inline-cue"
    return (
        f'<span class="jargon-tooltip-wrapper">'
        f'<span class="{cue_class}" onclick="toggleJargonTooltip(this, event)">{html.escape(term_clean)}</span>'
        f'<span class="jargon-popover-card">'
        f'<span class="jargon-popover-header">'
        f'<span class="jargon-popover-title">💡 {html.escape(title_clean)}</span>'
        f'<span class="jargon-popover-badge">{html.escape(category)}</span>'
        f'</span>'
        f'<span class="jargon-popover-body"><span class="jargon-popover-desc">{html.escape(explanation)}</span></span>'
        f'</span>'
        f'</span>'
    )

def build_editorial_lead(text: str) -> str:
    return EditorialLeadNode(text).render_html({})

def build_dilemma_callout(title: str, lead: str, extreme1_label: str, extreme1_math: str, extreme1_desc: str, extreme2_label: str, extreme2_desc: str) -> str:
    return DilemmaNode(title, lead, [(extreme1_label, extreme1_math, extreme1_desc), (extreme2_label, "", extreme2_desc)]).render_html({})

def build_callout(kind: str, title: str, content: str) -> str:
    return CalloutNode(kind, title, content).render_html({})

def build_analogy_card(title: str, category: str, content: str) -> str:
    return AnalogyNode(title, category, content).render_html({})

def build_aha_card(title: str, content: str) -> str:
    return BreakthroughNode(title, content).render_html({})

def build_mental_model_box(statement: str, explanation: str) -> str:
    return MentalModelNode(statement, explanation).render_html({})

def build_defense_scenario(scenario_title: str, context_paragraphs: List[str], defense_prompts: List[Tuple[str, str]]) -> str:
    return DefenseChallengeNode(scenario_title, "\n\n".join(context_paragraphs), defense_prompts).render_html({})

def build_simulator_container(title: str = "", subtitle: str = "", html: str = "", **kwargs) -> str:
    return SimulatorHtmlNode(html=html, title=title, subtitle=subtitle, **kwargs).render_html({})

# Node class aliases
MathFormulaNode = FormulaNode
FailureScenarioNode = DefenseChallengeNode
BreakthroughCardNode = BreakthroughNode


# ==============================================================================
# 5. Study Note AST Document & Auto-Synthesizer
# ==============================================================================

class NoteDocument:
    """
    Structured active-learning study note AST container.
    Strictly follows the 4-phase pedagogical contract:
    1. Initial Intuition & Working Hypothesis
    2. Dialectic & Friction Encountered
    3. Derived Invariant (The 'Aha!' Synthesis)
    4. Personal Rule of Thumb & Sizing Reality
    (Plus optional 5. Mathematical & Physical Invariants, 6. Production Takeaways)
    """

    def __init__(
        self,
        topic_id: str = "",
        title: str = "",
        tier: Union[str, Dict[str, Any]] = "Tier 0",
        cluster: Union[str, Dict[str, Any]] = "General",
        verified_date: str = "",
        status: str = "Verified Sign-Off (Active Learning Synthesis)",
        hypothesis: str = "",
        friction: Union[str, List[str]] = "",
        derived_invariant: str = "",
        rules_of_thumb: Optional[List[Dict[str, str]]] = None,
        formulas: Optional[List[Dict[str, str]]] = None,
        takeaways: Optional[List[str]] = None,
        future_safe_anchors: Optional[List[str]] = None,
        highlighted_passages: Optional[List[Any]] = None,
        glossary_terms: Optional[List[Dict[str, str]]] = None,
    ):
        self.topic_id = topic_id
        self.title = title
        self.tier = tier if isinstance(tier, dict) else {"code": "0", "name": str(tier)}
        self.cluster = cluster if isinstance(cluster, dict) else {"code": "0.1", "title": str(cluster)}
        self.verified_date = verified_date or datetime.date.today().isoformat()
        self.status = status
        self.hypothesis = hypothesis
        self.friction = friction
        self.derived_invariant = derived_invariant
        self.rules_of_thumb = rules_of_thumb or []
        self.formulas = formulas or []
        self.takeaways = takeaways or []
        self.future_safe_anchors = future_safe_anchors or []
        self.highlighted_passages = highlighted_passages or []
        self.glossary_terms = glossary_terms or []

    def add_rule(self, tradeoff: str, decision_rule: str, production_bound: str) -> "NoteDocument":
        self.rules_of_thumb.append({
            "tradeoff": tradeoff,
            "decision_rule": decision_rule,
            "production_bound": production_bound,
        })
        return self

    def add_formula(
        self,
        name: str,
        formula: str,
        variables: Optional[Dict[str, str]] = None,
        implication: str = "",
    ) -> "NoteDocument":
        self.formulas.append({
            "name": name,
            "formula": formula,
            "variables": variables or {},
            "implication": implication,
        })
        return self

    def add_takeaway(self, takeaway: str) -> "NoteDocument":
        self.takeaways.append(takeaway)
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic_id": self.topic_id,
            "title": self.title,
            "tier": self.tier,
            "cluster": self.cluster,
            "verified_date": self.verified_date,
            "status": self.status,
            "hypothesis": self.hypothesis,
            "friction": self.friction,
            "derived_invariant": self.derived_invariant,
            "rules_of_thumb": self.rules_of_thumb,
            "formulas": self.formulas,
            "takeaways": self.takeaways,
            "future_safe_anchors": self.future_safe_anchors,
            "highlighted_passages": self.highlighted_passages,
            "glossary_terms": self.glossary_terms,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NoteDocument":
        return cls(
            topic_id=data.get("topic_id") or data.get("topicId", ""),
            title=data.get("title", ""),
            tier=data.get("tier", "Tier 0"),
            cluster=data.get("cluster", "General"),
            verified_date=data.get("updated_date") or data.get("verified_date") or data.get("verifiedDate", ""),
            status=data.get("status", "Reference Note"),
            hypothesis=data.get("core_context") or data.get("hypothesis", ""),
            friction=data.get("mechanics_and_failures") or data.get("friction", ""),
            derived_invariant=data.get("core_invariant") or data.get("derived_invariant") or data.get("derivedInvariant", ""),
            rules_of_thumb=data.get("rules_of_thumb") or data.get("rulesOfThumb", []),
            formulas=data.get("formulas", []),
            takeaways=data.get("takeaways", []),
            future_safe_anchors=data.get("future_safe_anchors") or data.get("futureSafeAnchors", []),
            highlighted_passages=data.get("highlighted_passages") or data.get("highlightedPassages", []),
            glossary_terms=data.get("glossary_terms") or data.get("glossaryTerms", []),
        )

    def save(self, path: str):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "NoteDocument":
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def to_markdown(self) -> str:
        tier_title = self.tier.get("name", f"Tier {self.tier.get('code', '0')}") if isinstance(self.tier, dict) else str(self.tier)
        cluster_title = self.cluster.get("title", self.cluster.get("code", "General")) if isinstance(self.cluster, dict) else str(self.cluster)

        lines = [
            f"# {self.title}",
            f"**Track**: {tier_title} ➔ {cluster_title}",
            f"**Updated**: {self.verified_date}\n",
            "## 1. Core Context & Problem Space",
            f"> {self.hypothesis}\n",
            "## 2. Failure Modes & Bottleneck Mechanics",
        ]

        if isinstance(self.friction, list):
            for f in self.friction:
                lines.append(f"- {f}")
        else:
            lines.append(self.friction.strip())
        lines.append("")

        lines.extend([
            "## 3. Core Architectural Invariant",
            f"> {self.derived_invariant}\n",
            "## 4. Trade-Offs & Sizing Reference",
            "| Architectural Trade-Off / Constraint | Operational Decision Rule | Production Bound / Sizing Invariant |",
            "| :--- | :--- | :--- |",
        ])

        if self.rules_of_thumb:
            for r in self.rules_of_thumb:
                tradeoff = r.get("tradeoff", "")
                rule = r.get("decision_rule", "")
                bound = r.get("production_bound", "")
                lines.append(f"| **{tradeoff}** | {rule} | {bound} |")
        else:
            lines.append("| **Latency vs. Durability** | Favor batching on the critical path | Bound commit latency to max acceptable RTT |")
        lines.append("")

        if self.formulas:
            lines.append("## 5. Mathematical & Physical Bounds")
            for f in self.formulas:
                name = f.get("name", "Physical Law")
                formula = f.get("formula", "")
                implication = f.get("implication", "")
                vars_dict = f.get("variables", {})
                lines.append(f"### {name}")
                if formula:
                    lines.append(f"$$\n{formula}\n$$\n")
                if vars_dict:
                    lines.append("**Variables:**")
                    for k, v in vars_dict.items():
                        lines.append(f"- `${k}$`: {v}")
                    lines.append("")
                if implication:
                    lines.append(f"> **Production Implication:** {implication}\n")

        if self.takeaways:
            lines.append("## 6. Production Takeaways & Heuristics")
            for t in self.takeaways:
                lines.append(f"- {t}")
            lines.append("")

        if self.future_safe_anchors:
            lines.append("## Quick Refresh Anchors")
            for anchor in self.future_safe_anchors:
                lines.append(f"- {anchor}")
            lines.append("")

        if self.glossary_terms:
            lines.append("## Key Glossary")
            for g in self.glossary_terms:
                if isinstance(g, dict):
                    term = str(g.get("term") or g.get("title") or "").strip()
                    badge = str(g.get("badge") or "").strip()
                    defn = re.sub(r"\s+", " ", str(g.get("definition") or g.get("body") or g.get("desc") or "")).strip()
                    badge_str = f" ({badge})" if badge else ""
                    if term and defn:
                        lines.append(f"- **{term}**{badge_str}: {defn}")
            lines.append("")

        if self.highlighted_passages:
            lines.append("## Highlighted Passages")
            for hl in self.highlighted_passages:
                if isinstance(hl, dict):
                    txt = re.sub(r"\s+", " ", str(hl.get("text") or "")).strip()
                    pane_id = hl.get("paneId") or ""
                    m = re.search(r"section-(\d+)", pane_id)
                    stage_prefix = f"**[Stage {m.group(1)}]** " if m else ""
                    if txt:
                        lines.append(f"- {stage_prefix}*\"{txt}\"*")
                elif str(hl).strip():
                    lines.append(f"- *\"{str(hl).strip()}\"*")
            lines.append("")

        return "\n".join(lines).strip() + "\n"

    @classmethod
    def from_lesson(
        cls,
        lesson_data: Union[Dict[str, Any], "LessonDocument"],
        hypothesis: str = "",
        friction: str = "",
        evidence: str = "",
    ) -> "NoteDocument":
        """
        Dynamically extracts and synthesizes a NoteDocument from a LessonDocument AST or JSON payload.
        Pulls opening dilemma, failure scenarios, comparison matrices, and formulas automatically.
        """
        if isinstance(lesson_data, dict):
            metadata = lesson_data.get("metadata", {})
            title = metadata.get("title") or lesson_data.get("lesson_title") or metadata.get("topic_id", "System Design Topic")
            topic_id = metadata.get("topic_id") or lesson_data.get("topic_id") or ""
            tier = metadata.get("tier") or {"code": "0", "name": lesson_data.get("tier_badge", "Tier 0")}
            cluster = metadata.get("cluster") or {"code": "0.1", "title": lesson_data.get("cluster_badge", "General")}
            nodes = lesson_data.get("nodes", [])
            sections = lesson_data.get("sections", [])
        else:
            title = lesson_data.title
            topic_id = lesson_data.topic_id
            tier = {"code": "0", "name": getattr(lesson_data, "tier", getattr(lesson_data, "tier_badge", "Tier 0"))}
            cluster = {"code": "0.1", "title": getattr(lesson_data, "cluster", getattr(lesson_data, "cluster_badge", "General"))}
            nodes = [n.to_dict() if hasattr(n, "to_dict") else n for n in lesson_data.nodes]
            sections = []

        extracted_hypothesis = hypothesis.strip() if hypothesis else ""
        extracted_friction = friction.strip() if friction else ""
        extracted_invariant = evidence.strip() if evidence else ""
        rules: List[Dict[str, str]] = []
        formulas: List[Dict[str, str]] = []
        takeaways: List[str] = []

        # 1. Scan Nodes in AST
        for node in nodes:
            ntype = node.get("type", "")

            # Extract context from dilemma or warning callouts
            if not extracted_hypothesis and ntype in ("dilemma", "callout"):
                kind = node.get("kind", "")
                if kind in ("warning", "dilemma", "problem", "challenge") or ntype == "dilemma":
                    q = node.get("lead") or node.get("question") or node.get("title") or node.get("content") or node.get("text", "")
                    if q:
                        extracted_hypothesis = q.strip()[:240]

            # Extract failure scenarios from failure_scenario, mental_model, or defense_challenge
            if not extracted_friction and ntype in ("failure_scenario", "mental_model", "defense_challenge"):
                scen = node.get("scenario") or node.get("statement") or node.get("text") or node.get("title", "")
                imp = node.get("impact") or node.get("explanation") or "Degrades under high load or partition conditions"
                if scen:
                    extracted_friction = f"- **Failure Scenario**: {scen}\n- **System Impact**: {imp}"

            # Extract invariant from breakthrough cards or quotes
            if not extracted_invariant and ntype in ("breakthrough", "quote"):
                extracted_invariant = node.get("content") or node.get("text") or node.get("quote", "")

            # Extract rules of thumb from comparison matrix
            if ntype == "comparison_matrix":
                for row in node.get("rows", []):
                    dim = row.get("dimension") or row.get("name", "")
                    opt_a = row.get("option_a", "")
                    opt_b = row.get("option_b", "")
                    verdict = row.get("verdict", "")
                    tradeoff = row.get("tradeoff", "")
                    rules.append({
                        "tradeoff": f"{dim}: {opt_a} vs {opt_b}".strip(": "),
                        "decision_rule": verdict or tradeoff or "Evaluate access patterns and durability requirements",
                        "production_bound": tradeoff or f"Select {opt_a} or {opt_b} based on latency bounds",
                    })

            # Extract rules of thumb from sizing rules
            if ntype == "sizing_rule":
                rules.append({
                    "tradeoff": node.get("metric", "Sizing Bound"),
                    "decision_rule": node.get("rule_of_thumb", "Tune production buffer parameters"),
                    "production_bound": node.get("production_bound") or node.get("formula", ""),
                })

            # Extract formulas
            if ntype in ("formula", "math_formula"):
                formulas.append({
                    "name": node.get("name", "Physical Invariant"),
                    "formula": node.get("formula") or node.get("expression", ""),
                    "variables": node.get("variables", {}),
                    "implication": node.get("implication") or node.get("conclusion", ""),
                })

        # 2. Also scan legacy sections if present
        for sec in sections:
            if not extracted_hypothesis and sec.get("dilemma"):
                extracted_hypothesis = sec.get("dilemma", {}).get("question", "")
            if "sizing_rules" in sec:
                for sr in sec["sizing_rules"]:
                    rules.append({
                        "tradeoff": sr.get("metric", ""),
                        "decision_rule": sr.get("rule_of_thumb", ""),
                        "production_bound": sr.get("production_bound", ""),
                    })

        # Clean fallbacks if AST lacked specific nodes
        if not extracted_invariant:
            extracted_invariant = f"Proved unassisted that {title} enforces deterministic causal ordering and bounded blast radius by strictly decoupling volatile state from the critical write path."

        if not extracted_friction:
            extracted_friction = f"- **The Socratic Stress Test**: Challenged the working assumption against uncoordinated hardware crashes, trans-oceanic network jitter, and concurrent race conditions.\n- **Where the Model Broke**: Under extreme saturation, tail latency cascaded uncontrollably without explicit backpressure."

        if not extracted_hypothesis:
            extracted_hypothesis = f"Assumed standard synchronous request-response architecture would satisfy requirements for {title} before evaluating uncoordinated distributed failure states."

        return cls(
            topic_id=topic_id,
            title=title,
            tier=tier,
            cluster=cluster,
            hypothesis=extracted_hypothesis,
            friction=extracted_friction,
            derived_invariant=extracted_invariant,
            rules_of_thumb=rules,
            formulas=formulas,
            takeaways=takeaways,
        )


# ==============================================================================
# 6. Reusable System Design Math Calculations
# ==============================================================================

def calculate_bdp(bandwidth_mbps: float, rtt_ms: float) -> Dict[str, Any]:
    """
    Computes Bandwidth-Delay Product (BDP) in bits, bytes, KB, and MB.
    Calculates maximum throughput achievable with a standard unscaled 64KB TCP window.
    """
    bandwidth_bps = float(bandwidth_mbps) * 1e6
    rtt_sec = float(rtt_ms) / 1000.0
    bdp_bits = bandwidth_bps * rtt_sec
    bdp_bytes = bdp_bits / 8.0

    standard_window_bytes = 65535  # 64 KB (RFC 793 unscaled max)
    if rtt_sec > 0:
        standard_window_max_bps = (standard_window_bytes * 8.0) / rtt_sec
        standard_window_cap_mbps = min(float(bandwidth_mbps), standard_window_max_bps / 1e6)
    else:
        standard_window_cap_mbps = float(bandwidth_mbps)

    window_scaling_required = bdp_bytes > standard_window_bytes
    efficiency_pct = (standard_window_cap_mbps / float(bandwidth_mbps)) * 100.0 if bandwidth_mbps > 0 else 100.0

    return {
        "bandwidth_mbps": bandwidth_mbps,
        "rtt_ms": rtt_ms,
        "bdp_bits": int(bdp_bits),
        "bdp_bytes": int(bdp_bytes),
        "bdp_kb": round(bdp_bytes / 1024.0, 2),
        "bdp_mb": round(bdp_bytes / (1024.0 * 1024.0), 2),
        "standard_tcp_window_cap_mbps": round(standard_window_cap_mbps, 2),
        "standard_window_efficiency_pct": round(efficiency_pct, 1),
        "window_scaling_required": window_scaling_required,
        "formula": "BDP = Bandwidth (bps) × RTT (sec) / 8",
        "insight": (
            f"At {bandwidth_mbps} Mbps with {rtt_ms}ms RTT, BDP requires {round(bdp_bytes / 1024.0, 1)} KB in flight. "
            f"An unscaled 64KB TCP window will artificially throttle throughput to {round(standard_window_cap_mbps, 2)} Mbps "
            f"({round(efficiency_pct, 1)}% of line rate) without RFC 7323 window scaling."
        ),
    }


def calculate_quorum(node_count: int) -> Dict[str, Any]:
    """
    Computes majority quorum size, fault tolerance, and assesses even-node trade-offs.
    """
    n = int(node_count)
    if n < 1:
        raise ValueError("node_count must be >= 1")

    quorum_majority = (n // 2) + 1
    fault_tolerance = (n - 1) // 2
    is_even = (n % 2 == 0)

    warning = ""
    if is_even:
        warning = (
            f"Even node count (N={n}) provides F={fault_tolerance} fault tolerance, "
            f"which is identical to N={n-1} nodes. Node {n} incurs network/coordination overhead "
            f"without providing additional crash resilience."
        )

    return {
        "node_count": n,
        "majority_quorum": quorum_majority,
        "fault_tolerance": fault_tolerance,
        "is_even": is_even,
        "warning": warning,
        "formula": "Q = ⌊N / 2⌋ + 1, F = ⌊(N - 1) / 2⌋",
        "quorum_configurations": {
            "balanced": {"write": quorum_majority, "read": quorum_majority, "note": "Standard linearizable reads and writes"},
            "fast_read": {"write": n, "read": 1, "note": "Single-node reads; all nodes must participate in writes"},
            "write_biased": {"write": quorum_majority, "read": (n - quorum_majority) + 1, "note": "W + R > N invariant preserved"},
        },
    }


def calculate_disk_tps(
    seek_time_ms: float,
    transfer_time_ms: float = 0.0,
    rotational_latency_ms: float = 0.0,
) -> Dict[str, Any]:
    """
    Computes random IOPS and unbatched fsync commit ceilings for storage devices.
    """
    total_latency_ms = float(seek_time_ms) + float(transfer_time_ms) + float(rotational_latency_ms)
    if total_latency_ms <= 0:
        iops = 1000000.0
    else:
        iops = 1000.0 / total_latency_ms

    group_commit_50x = iops * 50.0

    return {
        "seek_time_ms": seek_time_ms,
        "transfer_time_ms": transfer_time_ms,
        "rotational_latency_ms": rotational_latency_ms,
        "total_latency_ms": round(total_latency_ms, 3),
        "random_iops_ceiling": int(iops),
        "group_commit_50x_tps": int(group_commit_50x),
        "formula": "IOPS = 1000 / (Seek + Rotational + Transfer ms)",
        "insight": (
            f"Unbatched synchronous fsync commits on this storage device cap transaction throughput at "
            f"~{int(iops)} TPS. Group commit batching amortizes fsync latency, raising throughput to ~{int(group_commit_50x)} TPS."
        ),
    }


def calculate_littles_law(arrival_rate_rps: float, latency_ms: float) -> Dict[str, Any]:
    """
    Applies Little's Law (L = λ × W) to compute concurrent in-flight requests and simulates latency spikes.
    """
    lambda_val = float(arrival_rate_rps)
    w_sec = float(latency_ms) / 1000.0
    l_concurrency = lambda_val * w_sec

    spikes = {}
    for mult in [2, 5, 10, 50]:
        spike_w = w_sec * mult
        spikes[f"{mult}x_latency"] = {
            "latency_ms": round(latency_ms * mult, 1),
            "concurrent_requests": round(lambda_val * spike_w, 1),
        }

    return {
        "arrival_rate_rps": lambda_val,
        "latency_ms": latency_ms,
        "average_service_time_sec": round(w_sec, 4),
        "concurrent_in_flight_requests": round(l_concurrency, 2),
        "formula": "L = λ × W (Concurrency = Arrival Rate × Service Time)",
        "spike_scenarios": spikes,
        "insight": (
            f"At {lambda_val} RPS with {latency_ms}ms latency, the system holds {round(l_concurrency, 1)} requests in flight. "
            f"If downstream stalls 10x to {latency_ms * 10}ms, concurrency surges to {spikes['10x_latency']['concurrent_requests']}, "
            f"exhausting connection pools unless protected by circuit breakers and load shedding."
        ),
    }


def calculate_consistent_hash_migration(keys_count: int, nodes_count: int) -> Dict[str, Any]:
    """
    Computes key migration blast radius in consistent hashing vs naive modulo hashing.
    """
    k = int(keys_count)
    n = int(nodes_count)
    if n < 1:
        raise ValueError("nodes_count must be >= 1")

    keys_migrated_consistent = int(k / (n + 1))
    fraction_consistent = 1.0 / (n + 1)

    fraction_modulo = float(n) / (n + 1)
    keys_migrated_modulo = int(k * fraction_modulo)

    saved_migrations = keys_migrated_modulo - keys_migrated_consistent

    return {
        "keys_count": k,
        "nodes_count": n,
        "adding_node_to": n + 1,
        "consistent_hashing_keys_migrated": keys_migrated_consistent,
        "consistent_hashing_pct_moved": round(fraction_consistent * 100.0, 2),
        "modulo_hashing_keys_migrated": keys_migrated_modulo,
        "modulo_hashing_pct_moved": round(fraction_modulo * 100.0, 2),
        "unnecessary_migrations_prevented": saved_migrations,
        "recommended_vnodes_per_node": "150-250 virtual nodes (bounds variance standard deviation < 5%)",
        "formula": "Consistent Hash Movement = K / (N + 1) vs Modulo = K × N / (N + 1)",
    }


def calculate_cache_sizing(
    daily_active_users: int,
    read_requests_per_user: int,
    avg_object_size_kb: float,
    hot_data_fraction: float = 0.2,
) -> Dict[str, Any]:
    """
    Computes cache RAM requirements (80/20 Zipf working set), QPS, and network egress bandwidth.
    """
    dau = int(daily_active_users)
    reads_per_user = int(read_requests_per_user)
    obj_kb = float(avg_object_size_kb)

    total_daily_reads = dau * reads_per_user
    avg_qps = total_daily_reads / 86400.0
    peak_qps = avg_qps * 2.0

    daily_volume_gb = (total_daily_reads * obj_kb) / (1024.0 * 1024.0)
    working_set_ram_gb = daily_volume_gb * float(hot_data_fraction)
    egress_bandwidth_gbps = (peak_qps * obj_kb * 8.0) / (1000.0 * 1000.0)

    return {
        "daily_active_users": dau,
        "total_daily_reads": total_daily_reads,
        "avg_qps": round(avg_qps, 1),
        "peak_qps": round(peak_qps, 1),
        "daily_volume_gb": round(daily_volume_gb, 2),
        "working_set_ram_gb": round(working_set_ram_gb, 2),
        "hot_data_fraction": hot_data_fraction,
        "peak_egress_bandwidth_gbps": round(egress_bandwidth_gbps, 2),
        "formula": "RAM = Daily Volume × Hot Fraction (80/20 Pareto rule)",
    }


def calculate_token_bucket(
    capacity: int,
    refill_rate_per_sec: float,
    burst_duration_sec: float = 1.0,
) -> Dict[str, Any]:
    """
    Computes token bucket rate limiter burst capacity and refill dynamics.
    """
    cap = int(capacity)
    refill = float(refill_rate_per_sec)
    burst_dur = float(burst_duration_sec)

    burst_allowed = cap + (refill * burst_dur)
    sustained_rps = refill
    time_to_refill_from_empty_sec = cap / refill if refill > 0 else float("inf")

    return {
        "bucket_capacity": cap,
        "refill_rate_rps": refill,
        "burst_duration_sec": burst_dur,
        "max_burst_requests": int(burst_allowed),
        "max_sustained_rps": sustained_rps,
        "time_to_refill_from_empty_sec": round(time_to_refill_from_empty_sec, 2),
        "formula": "Max Burst = Capacity + (Refill Rate × Burst Duration)",
    }


def calculate_bloom_filter(
    expected_items: int,
    false_positive_rate: float = 0.01,
) -> Dict[str, Any]:
    """
    Computes required bits, memory in MB, and optimal hash function count for a Bloom filter.
    """
    n = int(expected_items)
    p = float(false_positive_rate)
    if n < 1 or p <= 0 or p >= 1:
        raise ValueError("expected_items >= 1 and 0 < false_positive_rate < 1")

    m_bits = - (n * math.log(p)) / ((math.log(2)) ** 2)
    k_hashes = (m_bits / n) * math.log(2)
    bits_per_item = m_bits / n
    bytes_required = math.ceil(m_bits / 8.0)
    mb_required = bytes_required / (1024.0 * 1024.0)

    return {
        "expected_items": n,
        "false_positive_rate": p,
        "required_bits": int(math.ceil(m_bits)),
        "bits_per_item": round(bits_per_item, 2),
        "optimal_hash_functions_k": int(round(k_hashes)),
        "memory_bytes": bytes_required,
        "memory_mb": round(mb_required, 2),
        "formula": "m = -n ln(p) / (ln 2)², k = (m / n) ln 2",
        "rule_of_thumb": f"~{round(bits_per_item, 1)} bits per key achieves {p*100}% false positive rate with k={int(round(k_hashes))} hash functions",
    }


# ==============================================================================
# 7. CLI Interface
# ==============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="System Design Studio Component AST Builder & Compiler")
    parser.add_argument("--schema", choices=["lesson", "note"], nargs="?", const="lesson", help="Print canonical AST schema (lesson or note)")
    parser.add_argument("--validate", type=str, metavar="FILE", help="Validate a lesson payload AST file")
    parser.add_argument("--full-depth", action="store_true", help="Validate in full-depth mode (>= 3,500 words)")
    parser.add_argument("--to-markdown", type=str, metavar="FILE", help="Compile an AST payload to GFM Markdown")
    parser.add_argument("--components", action="store_true", help="List all available AST component nodes")
    parser.add_argument("--render-note", type=str, metavar="FILE", help="Compile a NoteDocument JSON to GFM Markdown")
    parser.add_argument("--from-lesson", type=str, metavar="FILE", help="Synthesize NoteDocument from lesson payload file")
    parser.add_argument("--calc", type=str, choices=["bdp", "quorum", "disk", "littles_law", "consistent_hash", "cache", "token_bucket", "bloom"], help="Run a standard system design calculation")
    parser.add_argument("--bandwidth", type=float, default=10000.0, help="Bandwidth in Mbps for BDP")
    parser.add_argument("--rtt", type=float, default=50.0, help="RTT in ms for BDP")
    parser.add_argument("--nodes", type=int, default=5, help="Node count for quorum / hashing")
    parser.add_argument("--keys", type=int, default=1000000, help="Key count for consistent hashing")
    parser.add_argument("--seek-time", type=float, default=8.0, help="Seek time in ms for disk TPS")
    parser.add_argument("--arrival-rate", type=float, default=5000.0, help="Arrival rate in RPS for Little's Law")
    parser.add_argument("--latency", type=float, default=20.0, help="Latency in ms for Little's Law")
    parser.add_argument("--dau", type=int, default=10000000, help="Daily active users for cache sizing")
    parser.add_argument("--reads-per-user", type=int, default=20, help="Reads per user for cache sizing")
    parser.add_argument("--object-size-kb", type=float, default=10.0, help="Average object size in KB for cache sizing")
    parser.add_argument("--capacity", type=int, default=1000, help="Token bucket capacity")
    parser.add_argument("--refill-rate", type=float, default=100.0, help="Token bucket refill rate")
    parser.add_argument("--items", type=int, default=1000000, help="Item count for Bloom filter")
    parser.add_argument("--fp-rate", type=float, default=0.01, help="False positive rate for Bloom filter")

    args = parser.parse_args()

    if args.schema:
        schema_file = "note-schema.json" if args.schema == "note" else "lesson-schema.json"
        schema_path = os.path.join(os.path.dirname(__file__), "..", "resources", schema_file)
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                print(f.read())
        sys.exit(0)

    if args.components:
        for name, cls in sorted(NODE_CLASSES.items()):
            print(f"- {name}: {cls.__doc__ or cls.__name__}")
        sys.exit(0)

    if args.render_note:
        doc = NoteDocument.load(args.render_note)
        print(doc.to_markdown())
        sys.exit(0)

    if args.from_lesson:
        with open(args.from_lesson, "r", encoding="utf-8") as f:
            data = json.load(f)
        doc = NoteDocument.from_lesson(data)
        print(doc.to_markdown())
        sys.exit(0)

    if args.calc:
        res = {}
        if args.calc == "bdp":
            res = calculate_bdp(args.bandwidth, args.rtt)
        elif args.calc == "quorum":
            res = calculate_quorum(args.nodes)
        elif args.calc == "disk":
            res = calculate_disk_tps(args.seek_time)
        elif args.calc == "littles_law":
            res = calculate_littles_law(args.arrival_rate, args.latency)
        elif args.calc == "consistent_hash":
            res = calculate_consistent_hash_migration(args.keys, args.nodes)
        elif args.calc == "cache":
            res = calculate_cache_sizing(args.dau, args.reads_per_user, args.object_size_kb)
        elif args.calc == "token_bucket":
            res = calculate_token_bucket(args.capacity, args.refill_rate)
        elif args.calc == "bloom":
            res = calculate_bloom_filter(args.items, args.fp_rate)
        print(json.dumps(res, indent=2))
        sys.exit(0)

    if args.validate or args.to_markdown:
        target = args.validate or args.to_markdown
        with open(target, "r", encoding="utf-8") as f:
            data = json.load(f)
        doc = LessonDocument.from_dict(data)
        if args.full_depth:
            doc.set_full_depth(True)

        if args.to_markdown:
            print(doc.to_markdown())
            sys.exit(0)

        is_valid, warnings, metrics = doc.validate()
        print("-" * 60)
        print(f"📋 LESSON AST AUDIT: {os.path.basename(target)}")
        print(f"   Nodes        : {len(doc.nodes)} nodes")
        print(f"   Word Count   : {metrics['word_count']} words")
        print(f"   Jargon Count : {metrics['jargon_count']} unpackings")
        print(f"   Full Depth   : {'Enabled' if doc.full_depth else 'Standard'}")
        print("-" * 60)
        if warnings:
            for w in warnings:
                print(f"  ⚠️  {w}")
            sys.exit(1)
        else:
            print("  ✅ All AST invariants passed!")
            sys.exit(0)

    parser.print_help()


if __name__ == "__main__":
    main()
