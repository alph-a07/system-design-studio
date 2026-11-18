# System Design Dummy Lab

> **Project Curriculum Track**: Scoped to project. Generated on 2026-11-18 via System Design Studio.

---


# Tier 0 — HLD Building Blocks (Prerequisite Slice)

## 🔁 1. [0.1] APIs & Network Transport for Design

*Depth: [concept][contrast][trap]  |  Depends on: none*

### Atomic Topics∂

- [x]  TCP vs UDP — what reliability costs, and why real-time media often picks UDP — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [x]  HTTP/1.1 vs HTTP/2 vs HTTP/3 — where head-of-line blocking lives at each layer and why QUIC moved to UDP — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  TLS handshake cost and session resumption — why connection reuse matters on cellular — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  REST vs gRPC vs GraphQL — payload shape, coupling, cacheability, tooling tradeoffs — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Polling vs long-polling vs SSE vs WebSocket — connection cost vs latency — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Pagination: offset vs cursor/keyset — why offset skips/duplicates under writes and degrades at depth — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Idempotency — which HTTP methods are idempotent, idempotency keys for unsafe operations, why retries make this mandatory — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  API versioning and backward compatibility — additive changes, tolerant readers — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 DDIA (Kleppmann) Ch4 — Encoding and Evolution (1st ed. numbering) — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  🛠️ Build a tiny server, show a duplicate POST caused by a client retry after timeout, then fix it with an idempotency key — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*
- [ ]  🛠️ Page through a table with offset pagination while inserting rows mid-scroll — observe duplicates/skips — then redo with a cursor — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  For each provider API your client application calls, do you know whether it paginates by page number, cursor or link header — and what your loop does if the list shifts mid-fetch? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Explain how a retry after a timeout can double-charge without an idempotency key. Where exactly is the ambiguity: client, network, or server? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---


---

## 🔁 2. [0.2] Databases: Indexes, Transactions & Isolation

*Depth: [concept][mechanics][contrast][trap]  |  Depends on: none*

### Atomic Topics

- [ ]  B-tree index — why range scans and ordered reads are cheap, and why every extra index taxes writes — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  LSM tree — why writes are fast, and what compaction and read amplification cost — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Composite indexes — leftmost-prefix rule, covering indexes — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Reading a query plan — seq scan vs index scan, and why the planner sometimes ignores your index — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  ACID — what each letter actually guarantees, and what 'C' really depends on — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Isolation levels — read committed, repeatable read, snapshot, serializable; dirty / non-repeatable / phantom reads and write skew — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Optimistic vs pessimistic concurrency control; version columns; lost updates — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Normalization vs denormalization — read/write tradeoff, and when duplication is the right call — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  SQL vs NoSQL — decided by access pattern, not fashion — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 DDIA Ch3 (Storage and Retrieval) and Ch7 (Transactions) — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  🛠️ Create a 1M-row table, EXPLAIN a query before/after adding an index, then break the index by wrapping the column in a function — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*
- [ ]  🛠️ Reproduce write skew (two on-call doctors both go off-call) under snapshot isolation using two sessions — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  In an application using client-side embedded storage (e.g. IndexedDB or SQLite) — can you map its (compound) indexes onto the B-tree rules above, and say what a query that can't use an index costs? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Why doesn't 'I used a transaction' automatically prevent a lost update — which isolation level or pattern actually does? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---


---

## 🔁 3. [0.3] Caching Fundamentals

*Depth: [concept][mechanics][contrast][trap]  |  Depends on: none*

### Atomic Topics

- [ ]  Cache-aside vs read-through vs write-through vs write-back vs write-around — consistency and failure tradeoffs of each — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Eviction — LRU, LFU, FIFO, TTL — which workload each wins on — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Invalidation — why it's hard; TTL vs explicit vs versioned keys — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Cache stampede / thundering herd — request coalescing, jittered TTLs, locking — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Cache penetration (nonexistent keys) — negative caching, bloom-filter guard — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  HTTP caching — Cache-Control, ETag / If-None-Match, max-age vs s-maxage, stale-while-revalidate — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  CDN basics — what's cacheable, origin shield, purge — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 MDN — HTTP caching (https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching) — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  🛠️ Implement cache-aside in front of a deliberately slow fake DB, fire 100 concurrent misses on one key, then fix with single-flight — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*
- [ ]  🛠️ Serve a resource with an ETag and confirm the 304 path with curl — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  In an offline-capable web application / PWA — which of its resources are governed by HTTP cache headers vs a service-worker cache, and who invalidates each? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Given a write-back cache and a crash, exactly what data is lost, and how would the design detect it? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---


---

## 🔁 4. [0.4] Queues, Async Messaging & Delivery Semantics

*Depth: [concept][contrast][trap]  |  Depends on: none*

### Atomic Topics

- [ ]  Queue (competing consumers) vs pub/sub (fan-out) — who receives each message — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  At-most-once vs at-least-once vs exactly-once — why exactly-once is really at-least-once plus an idempotent consumer — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Acknowledgement, visibility timeout, redelivery, poison messages, dead-letter queues — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Ordering guarantees — per-queue vs per-partition vs none, and what you give up when you add consumers — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Backpressure — bounded queues, and what happens when producers outpace consumers — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Why async at all — decoupling, load leveling, latency hiding — and the cost: eventual consistency and harder debugging — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Outbox pattern (concept level) — atomic DB write plus event publish — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 DDIA Ch11 (Stream Processing), first half — messaging systems — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  🛠️ Producer + 3 consumers on an in-process queue; kill a consumer mid-message and implement redelivery with idempotent handling — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*
- [ ]  🛠️ Create a poison message and route it to a dead-letter queue after N failures — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  Explain why 'exactly-once delivery' is a misleading phrase using the lost-ack vs lost-work ambiguity. — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Kotlin Channels vs a durable broker queue: which guarantees does a Channel NOT give you? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---


---

## 🔁 5. [0.5] Estimation, Latency Numbers & Availability Math

*Depth: [concept][mechanics][pattern]  |  Depends on: none*

### Atomic Topics

- [ ]  Latency orders of magnitude — memory, SSD, same-DC network, cross-region — and how they drive design choices — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Back-of-envelope method — DAU to QPS, peak factor, storage growth, bandwidth, read:write ratio — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Powers of two and rounding discipline — aim for order of magnitude, state assumptions — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Availability nines — downtime per year; serial vs parallel availability composition — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  SLI / SLO / SLA / error budget — definitions and how they drive decisions — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Throughput vs latency; percentiles (p50/p95/p99); tail-latency amplification under fan-out — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 Google SRE book — Embracing Risk, and Service Level Objectives chapters (https://sre.google/sre-book/table-of-contents/) — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  📝 Estimate QPS, storage and bandwidth for a photo-sharing app with 50M DAU; compare to a reference estimate and list every assumption that differed — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  Three services at 99.9% called serially: what is the best-case composed availability, and why does fan-out make p99 worse than any single dependency's p99? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Can you turn '100M DAU' into peak write QPS in under two minutes, stating assumptions aloud? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---


---


# Tier 1 — Low-Level Design (LLD)

## 🔁 6. [1.1] From Requirements to Model: Entities, Invariants & Ownership

*Depth: [concept][pattern][trap]  |  Depends on: none*

### Atomic Topics

- [ ]  Extract nouns and verbs, then separate real entities from attributes and from behaviors — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Value object vs entity — identity decides equals/hashCode and lifecycle — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Invariants — what must always be true, and which single class is responsible for enforcing it — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Aggregate boundary — the unit that changes together and is saved/locked together — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  State ownership — who may mutate what; one writer per piece of state — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Make illegal states unrepresentable — sealed types over flag/nullable combinations — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Clarifying questions before modeling — scope, scale, concurrency, extensibility axes — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 Effective Java 3rd ed., Items 17 and 50 (minimize mutability; defensive copies) — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  📝 Model a hotel booking domain from a 5-line requirement; list every invariant and the class that enforces it — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*
- [ ]  🛠️ Refactor a class with three booleans (isActive, isPaused, isDeleted) into a sealed state type and count the impossible combinations you removed — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  Take one UiState from your own app: can you list its invariants and say whether the type makes violations impossible or merely unlikely? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Why does a bigger aggregate hurt concurrency, and why does a too-small aggregate break invariants? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---


---

## 🔁 7. [1.2] Designing for Change: Cohesion, Coupling & Variation Points

*Depth: [concept][contrast][pattern][trap]  |  Depends on: 1.1*

### Atomic Topics

- [ ]  Cohesion and coupling — how to judge them informally in a class — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Find the axis of change first and abstract only what varies — why abstracting everything fails — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Composition over inheritance as a default — and what inheritance still buys — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Depend on abstractions at boundaries you own, on concretes inside a module — the rule of three — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Dependency direction and layering — who may import whom — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Law of Demeter and tell-don't-ask as coupling reducers — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Over-engineering signals — single-implementation interfaces, speculative generality, pattern-for-pattern's-sake — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 Refactoring Guru — code smells (https://refactoring.guru/refactoring/smells) — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  📝 Design a discount engine with 3 rules, then add 2 more rules plus stacking; record exactly which code changed each time — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  In a multi-provider service client, what is the real variation axis across external providers, and does your provider interface abstract exactly that — or also things that never vary? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Name one abstraction you've written with exactly one implementation today and decide whether it earns its keep. — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---


---

## 🔁 8. [1.3] Patterns in Context I: Choosing by Problem Shape

*Depth: [pattern][contrast][trap]  |  Depends on: 1.2*

### Atomic Topics

- [ ]  Strategy — swap an algorithm at runtime; versus if/else on type — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  State — behavior changes with state; versus Strategy: who triggers the change — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Observer / in-process pub-sub — decoupling, lifetime and leak risks, ordering — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Command — action as object: queueing, undo/redo, logging, retry — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Decorator — stack behavior behind one interface; versus inheritance explosion — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Factory Method / Abstract Factory / Builder — when creation complexity justifies each — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  For every pattern: the force that justifies it, and the cost it adds — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 Refactoring Guru — design patterns catalog (https://refactoring.guru/design-patterns) — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  🛠️ Implement notification channels with Strategy, then with State; write down when each fits better — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  Given a requirement in plain words, can you name the force and the pattern before drawing a class diagram? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Strategy and State look identical in UML — what differs in intent and in who owns the transition? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---


---


# Tier 2 — High-Level Design (HLD)

## 🔁 20. [2.1] Scalability Fundamentals & Load Balancing

*Depth: [concept][mechanics][contrast]  |  Depends on: 0.1, 0.5*

### Atomic Topics

- [ ]  Vertical vs horizontal scaling — limits, cost, failure domains — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Stateless services — why externalizing session/state enables horizontal scale — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Load balancer L4 vs L7 — what each can see and route on; TLS termination — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Algorithms — round robin, least connections, consistent hash, power of two choices — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Health checks, connection draining, sticky sessions and why they hurt — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Autoscaling signals, lag, thrash and warm-up — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Single points of failure — finding them in any diagram — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Bottleneck analysis — CPU, memory, I/O, network, locks, downstream — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 DDIA Ch1 — Reliable, Scalable, Maintainable — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  📝 Evolve a single-server app to 100x traffic step by step; record the bottleneck that appears at each step — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*
- [ ]  🛠️ Run 3 instances behind nginx or haproxy and demonstrate sticky vs non-sticky behavior with in-memory sessions — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  For any design you draw, can you name the next bottleneck before being asked? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Why does least-connections beat round-robin for long-lived or uneven requests? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---


---

## 🔁 21. [2.2] Data Partitioning & Consistent Hashing

*Depth: [mechanics][internals][trap]  |  Depends on: 0.2, 2.1*

### Atomic Topics

- [ ]  Why partition — data size and write throughput exceed one node — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Range vs hash vs directory-based partitioning — scans vs even spread — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Consistent hashing and virtual nodes — why mod N reshuffles everything and this doesn't — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Hot keys and hot partitions — celebrity problem, key salting, splitting hot shards — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Rebalancing strategies — fixed partition counts, dynamic splitting, avoiding stampedes — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Secondary indexes in sharded stores — local (scatter-gather) vs global (write amplification) — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Cross-shard queries and transactions — cost, and avoidance through data modeling — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Choosing a shard key — cardinality, distribution, access pattern — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 DDIA Ch6 — Partitioning — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  🛠️ Implement a consistent-hash ring with virtual nodes; add/remove nodes and measure the fraction of keys that move — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*
- [ ]  🛠️ Simulate a Zipf-distributed key workload and show the hot partition — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  Why does hash(userId) % N break during resharding, and how many keys move in a ring when one node is added? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  A 'likes' counter on a viral post: where is the hot spot, and how do you spread it without losing correctness? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---


---

## 🔁 22. [2.3] Replication, Consistency Models & CAP/PACELC

*Depth: [mechanics][contrast][trap]  |  Depends on: 0.2, 0.5, 2.2*

### Atomic Topics

- [ ]  Leader-follower, multi-leader, leaderless — failure and conflict behavior of each — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Sync vs async replication — durability vs latency; failover data loss — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Replication-lag anomalies — read-your-writes, monotonic reads, consistent prefix — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Quorums (W+R>N) — what they guarantee, and what they don't (sloppy quorums, hinted handoff) — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Conflict resolution — LWW pitfalls, version vectors, CRDTs at concept level — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Consistency spectrum — linearizable, sequential, causal, eventual — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  CAP — what it actually says (about partitions); PACELC for the normal-case tradeoff — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Split brain, failover and fencing — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 DDIA Ch5 (Replication) and Ch9 (Consistency and Consensus) — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  📖 Jepsen — consistency models map (https://jepsen.io/consistency) — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  🛠️ Run a primary plus replica (Postgres or Redis), inject lag, demonstrate a read-your-writes violation, and implement a fix (read from primary for N seconds after a write) — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  Explain why 'CAP: pick two' is misleading, using what happens during and outside a partition. — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Why can a W+R>N quorum still return stale data? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---


---

## 🔁 23. [2.4] Distributed Coordination & Transactions

*Depth: [mechanics][internals][trap]  |  Depends on: 0.4, 2.3*

### Atomic Topics

- [ ]  Why distributed transactions are hard — partial failure and no global clock — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  2PC — protocol, blocking on coordinator failure, why it's rare at scale — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Saga — choreography vs orchestration, compensating actions, what isn't compensable — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Outbox plus idempotent consumers — reliable event publishing without 2PC — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Idempotency keys end to end; deduplication windows — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Distributed locks — leases and fencing tokens; why a Redis lock alone is unsafe without fencing — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Leader election and consensus at concept level — Raft terms, log replication, majorities — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Time — clock drift, Lamport/vector clocks, why wall clocks can't order events — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 DDIA Ch8 and Ch9 — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  📖 Raft visualization (https://raft.github.io/) — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  📝 Design order → payment → inventory as a saga with compensation; for every step, write the failure and the system's state afterwards — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  Describe how a lock holder pausing for GC corrupts data after its lease expired, and which fencing-token check prevents it. — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Which steps in your saga can't be undone, and what do you do instead? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---


---

## 🔁 24. [2.5] Storage Engines & Choosing the Right Database

*Depth: [contrast][mechanics][pattern]  |  Depends on: 0.2, 2.2, 2.3*

### Atomic Topics

- [ ]  B-tree vs LSM in practice — write amplification, read amplification, compaction pain — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Row vs columnar — OLTP vs OLAP access patterns — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Key-value, document, wide-column, relational, graph, time-series, search — what each is for — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Query-first modeling (DynamoDB/Cassandra) vs entity-first modeling (relational) — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Polyglot persistence — its cost; source of truth vs derived stores — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Blob/object storage — when files don't belong in a database — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Choosing by consistency need, query shapes, scale, ops cost, team skill — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Schema evolution at scale — expand/contract migrations — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 DDIA Ch2 and Ch3 — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  📖 Amazon Dynamo paper (2007) — design principles sections — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  📝 For five workloads (chat messages, ledger, product search, session store, metrics) pick a store, justify it, and name the rejected alternative — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  Can you justify a database choice by access patterns first and brand second? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  What breaks if a derived search index drifts from the source of truth, and how is it repaired? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---


---

## 🔁 26. [2.7] Messaging, Streaming & Event-Driven Design

*Depth: [mechanics][contrast][trap]  |  Depends on: 0.4, 2.2, 2.3*

### Atomic Topics

- [ ]  Kafka model — topic, partition, offset, consumer group, retention, log compaction — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Ordering — per partition only; key choice determines order and hot partitions — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Delivery semantics — acks, idempotent producer, transactions, consumer commit strategies — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Consumer lag, rebalancing, poison messages, replay — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Event sourcing — the log as truth, projections, snapshots; its costs and when it's wrong — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  CQRS — separate read/write models, consistency lag, when it's overkill — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Change data capture — keeping derived stores in sync from a DB log — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Stream vs batch processing; windowing and late data at concept level — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 DDIA Ch11 — Stream Processing — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  📖 Kafka docs — Design section (https://kafka.apache.org/documentation/#design) — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  🛠️ Run a local Kafka, produce keyed events, kill a consumer, and observe rebalance and redelivery — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*
- [ ]  📝 Design an order-events pipeline with a projection into a search index — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  Why can't adding consumers beyond the partition count raise throughput, and how does key choice create hot partitions? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  When does event sourcing become a liability? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---


---

## 🔁 29. [2.10] Security & Identity in System Design

*Depth: [mechanics][pattern][trap]  |  Depends on: 0.1*

### Atomic Topics

- [ ]  AuthN vs AuthZ — RBAC, ABAC, resource-level checks; where enforcement lives — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  OAuth2 and OIDC — authorization code + PKCE, why implicit is dead, scopes, refresh-token rotation — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Sessions vs JWTs — the revocation problem, short-lived access plus refresh, client storage — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Service-to-service auth — mTLS, signed tokens, least privilege — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Encryption in transit and at rest; key management; secrets handling — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Abuse defenses — rate limiting, bot detection, replay protection, input validation — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Multi-tenancy isolation — row-level, schema, database per tenant — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Privacy design inputs — PII minimization, retention, audit logs — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 RFC 8252 — OAuth 2.0 for Native Apps, and the OAuth 2.0 Security Best Current Practice — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  🛠️ Implement authorization code + PKCE against a local identity provider — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*
- [ ]  📝 Threat-model one of your designs using STRIDE — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  When an application authenticates against multiple identity providers: where does each token live, how does refresh work, and what does a leaked token allow? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Why is JWT revocation hard, and what are the real mitigations? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---


---
