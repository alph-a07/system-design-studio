# Shared Engineering Context — Manifest Specification v2.1

## Overview

The **Context Manifest** is the canonical, portable, machine-readable data model representing the active state of a system-design learning instance. It is stored locally at `.system-design/manifest.json`.

**The studio relies on zero external services.** There are no Notion databases or third-party drawing boards. The entire shared context consists exclusively of:
1. **The Curriculum** (`CURRICULUM.md` / `manifest.json`): The 50-cluster roadmap and topic hierarchy.
2. **The Living Cursor** (`CURSOR.md` / `manifest.json`): The operational brain tracking active focus, lineage, examples, and deferred topics.

---

## Complete JSON Schema Reference

```json
{
  "$schemaVersion": "2.1",
  "instanceName": "string (Human-readable name of learning instance)",
  "createdAt": "ISO-8601 Timestamp",
  "lastUpdated": "ISO-8601 Timestamp",
  "curriculum": {
    "id": "curriculum.<id>",
    "title": "string",
    "sourceRef": ".system-design/CURRICULUM.md",
    "activeClusterId": "cluster.<id>",
    "activeTopicId": "topic.<id>",
    "clusters": [
      {
        "id": "cluster.<id>",
        "code": "string (e.g. 0.1, 1.4)",
        "title": "string",
        "order": 1,
        "topics": [
          {
            "id": "topic.<id>",
            "title": "string",
            "status": "unseen | completed | needs-review"
          }
        ]
      }
    ]
  },
  "cursor": {
    "topicFoundationId": "foundation.<topic-id>",
    "topicFoundationStatus": "not-started | in-progress | complete | needs-repair",
    "activeMechanismGroupId": "group.<id>",
    "groupStatus": "queued | teaching | awaiting-evidence | needs-repair | closed",
    "lastCheckpointId": "checkpoint.<id>",
    "lastCheckpointStatus": "not-issued | awaiting-answer | answered",
    "nextTeachingAction": "string (Precise description of next pedagogical action)",
    "backwardAnchor": "string (Causal anchor to previous topics)",
    "forwardHook": "string (Forward connection to subsequent topics)",
    "targetDepth": "string (e.g. [concept][mechanics][contrast][trap])",
    "clusterRealityChecks": [
      "string (Cold questions to pass before cluster sign-off)"
    ]
  },
  "runningContext": {
    "activeMetaphorStrategy": "string",
    "examplesTaken": [
      {
        "id": "example.<id>",
        "conceptId": "concept.<id>",
        "domain": "string (e.g. Financial Ledger, Autonomous Drone Fleet)",
        "scenario": "string",
        "tradeoffsExposed": ["string"],
        "date": "YYYY-MM-DD"
      }
    ],
    "deferredQueue": [
      {
        "id": "defer.<id>",
        "topic": "string",
        "originConceptId": "concept.<id>",
        "targetClusterId": "cluster.<id>",
        "anchorNote": "string",
        "status": "pending | resolved"
      }
    ],
    "coveredConcepts": [
      "concept.<id>"
    ],
    "unresolvedFoundations": []
  },
  "decisions": [
    {
      "id": "decision.<id>",
      "contextId": "string",
      "title": "string",
      "choice": "string",
      "rationale": "string",
      "date": "YYYY-MM-DD"
    }
  ],
  "evidence": [
    {
      "id": "evidence.<id>",
      "topicId": "topic.<id>",
      "type": "verified-explanation",
      "demonstratedClaim": "string",
      "date": "YYYY-MM-DD"
    }
  ]
}
```
