# System Design Mastery

# System Design Mastery Roadmap — LLD, HLD & Mobile

> **Scope:** low-level design, high-level design, and mobile system design, for both interviews and design discussions at work. Nothing trimmed.
> 
> 
> **Order, and why:** Tier 0 is a small HLD slice (APIs, databases, caching, queues, estimation) because LLD problems like rate limiters, schedulers and booking systems silently depend on it. Tier 1 (LLD) comes next because it builds on the OOP and Architecture work you already have. Tier 2 (HLD) then goes full depth. Tier 3 (mobile) comes after HLD because offline sync, push and pagination only make sense once consistency, messaging and caching are solid. Tier 4 runs alongside: start the practice loop (4.2) as soon as you begin Tier 1.
> 
> **Depends on:** each cluster lists the clusters (or Android-doc tiers) that must be solid first. Respect these; skipping them is how a design answer turns into diagram-matching.
> 
> **How to tick things off:** every checklist item states its own tick-off rule. Topics = explain aloud with the why and the cost. Reality Check = answer cold in under 30 seconds. A partial answer means leave it unchecked.
> 
> **The real risk in system design:** the illusion of fluency. A diagram you can recognize is not a design you can derive. The Reality Checks are the gate, not the topic lists.
> 
> Fold a cluster when it is actually done, not when it feels done.
> 

---

---

# Tier 0 — HLD Building Blocks (Prerequisite Slice)

*The minimum distributed-systems vocabulary LLD problems and everything after it lean on. Concept + contrast depth here; each reappears at full depth in Tier 2.*

## 🔁 1. [0.1] APIs & Network Transport for Design

*Depth: [concept][contrast][trap]  |  Depends on: none*

### Atomic Topics∂

- [ ]  TCP vs UDP — what reliability costs, and why real-time media often picks UDP — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  HTTP/1.1 vs HTTP/2 vs HTTP/3 — where head-of-line blocking lives at each layer and why QUIC moved to UDP — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
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

- [ ]  For each provider API Anchor calls, do you know whether it paginates by page number, cursor or link header — and what your loop does if the list shifts mid-fetch? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Explain how a retry after a timeout can double-charge without an idempotency key. Where exactly is the ambiguity: client, network, or server? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

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

- [ ]  Rival uses IndexedDB through Dexie — can you map its (compound) indexes onto the B-tree rules above, and say what a query that can't use an index costs? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Why doesn't 'I used a transaction' automatically prevent a lost update — which isolation level or pattern actually does? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

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

- [ ]  Rival is a PWA — which of its resources are governed by HTTP cache headers vs a service-worker cache, and who invalidates each? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Given a write-back cache and a crash, exactly what data is lost, and how would the design detect it? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

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

# Tier 1 — Low-Level Design (LLD)

*Modeling, change-resilient class design, patterns chosen by problem shape, concurrency inside a process, then the classic problems. Builds directly on your OOP/SOLID and Architecture tiers from the Android doc.*

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

- [ ]  In Anchor, what is the real variation axis across VCS providers, and does your provider interface abstract exactly that — or also things that never vary? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Name one abstraction you've written with exactly one implementation today and decide whether it earns its keep. — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

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

## 🔁 9. [1.4] Patterns in Context II: Structure, Pipelines & Their Misuse

*Depth: [pattern][contrast][trap]  |  Depends on: 1.3*

### Atomic Topics

- [ ]  Chain of Responsibility — middleware, OkHttp interceptors, event dispatch — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Template Method vs Strategy — inheritance vs composition for algorithm skeletons — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Adapter vs Facade vs Proxy — same wrapping shape, three different intents — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Mediator vs Observer — central coordination vs broadcast — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Visitor and double dispatch — and when sealed classes plus exhaustive when replace it — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Flyweight / Composite / Memento / Iterator — recognizing them in standard libraries — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Pattern misuse — singleton as global state, god factories, pattern soup — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  🛠️ Implement an interceptor chain (auth, logging, retry) and compare it with OkHttp's interceptor design — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*
- [ ]  🛠️ Rewrite a Visitor over a small AST as a Kotlin sealed hierarchy with exhaustive when; list what you gained and lost — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  Adapter vs Facade vs Proxy: for a wrapper in your codebase, which is it, and how do you know from intent rather than shape? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Where does a pattern you've used add indirection without any real variation point? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 10. [1.5] State Machines & Workflows as First-Class Design

*Depth: [mechanics][pattern][trap]  |  Depends on: 1.1, 1.3*

### Atomic Topics

- [ ]  Explicit states, events, transitions, guards and actions — a table, not scattered ifs — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Illegal transitions — reject, ignore, or error; why the choice is a product decision — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Sealed types plus a pure transition function — the same shape as an MVI reducer — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Idempotent transitions — retries and double taps must not corrupt state — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Persisting a state machine — current state plus event log; resuming after a crash — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Timeouts and expirations as events — reservation holds, pending payments — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Hierarchical states when flat tables explode — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📝 Model an order lifecycle (created, paid, shipped, delivered, cancelled, refunded) as a transition table, then code the pure transition function — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*
- [ ]  🛠️ Property-test it: random event sequences must never reach an illegal state — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  Your MVI reducer is a state machine — can you draw its transition table, and does it handle duplicate events safely? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  What happens to an order stuck in 'payment pending' when the process dies — and where in your design is that decided? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 11. [1.6] API & Contract Design for Classes and Modules

*Depth: [concept][pattern][trap]  |  Depends on: 1.1*

### Atomic Topics

- [ ]  Smallest public surface — what to expose, what to keep internal — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Error modeling — exceptions vs Result/sealed outcomes; expected failures vs bugs — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Validation placement — at the boundary vs in the constructor/factory; parse, don't validate — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Immutability and defensive copying at API edges — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Builders, defaults and named arguments vs constructor explosion — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Backward-compatible evolution — adding optional parameters or methods without breaking callers — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Naming and abstraction level — one level per function or class — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 Effective Java 3rd ed., Items 49–56 (the Methods chapter) — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  📝 Design the public API of a RateLimiter and a Cache before implementing either; review each method for what it leaks — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  Find a function in your code that returns null or throws for an expected failure — would a sealed result make the caller's obligations explicit? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  What does your Hilt-injected repository interface leak (DTOs, Flow types, exceptions) that its callers shouldn't depend on? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 12. [1.7] Concurrency in Class Design

*Depth: [mechanics][contrast][trap]  |  Depends on: 0.4; Android doc: Coroutines tier*

### Atomic Topics

- [ ]  Shared mutable state is the problem — isolate it, confine it, or make it immutable — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Check-then-act and read-modify-write races — atomic op vs lock vs single-writer actor — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Lock granularity — coarse vs fine vs striping; deadlock via lock ordering — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Composing thread-safe operations is not automatically thread-safe — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Producer-consumer with bounded queues; blocking vs suspending designs — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Choosing concurrent collections by access pattern — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Kotlin tools — Mutex, confinement via limitedParallelism(1), actor-style channel loop — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Visibility and safe publication — final fields, volatile, immutable snapshots — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 Java Concurrency in Practice (Goetz) — Ch1–3 and Ch5 — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  🛠️ Make inventory.reserve(item, qty) correct under 100 concurrent callers three ways — synchronized, Mutex, single actor — and measure each — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*
- [ ]  🛠️ Write a deliberate deadlock between two account transfers and fix it with lock ordering — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  Why is 'ConcurrentHashMap.get then put' still a race, and which single call fixes it? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  For a StateFlow updated from two coroutines, is `value = value.copy(...)` safe — and what is the correct primitive? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 13. [1.8] Data Structure Selection for Design Problems

*Depth: [mechanics][contrast][pattern]  |  Depends on: 1.7 (for the concurrent variants)*

### Atomic Topics

- [ ]  Choose by operations needed — lookup, ordered, range, top-K, membership, prefix — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  HashMap + doubly linked list for O(1) LRU; LinkedHashMap access-order shortcut and its limits — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Heap / PriorityQueue — top-K, time-ordered scheduling, lazy deletion — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Trie — prefix search and autocomplete; memory tradeoffs — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Sorted maps and interval structures (TreeMap floor/ceiling) — booking overlaps, time windows — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Sliding window and deque structures — rate limiting, moving metrics — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Bitsets, bloom filters and counting structures at LLD scale — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Complexity under real constraints — memory, cache locality, concurrency — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  🛠️ Implement LRU, O(1) LFU and a TTL cache; benchmark against LinkedHashMap — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*
- [ ]  🛠️ Build autocomplete with a trie, then with a sorted list plus binary search; compare memory and latency — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  Without notes: how does O(1) LFU work — which maps/lists, and why do ties need a recency order? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  When would a TreeMap beat a HashMap for you even though lookups are O(log n)? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 14. [1.9] Testability, Time & Randomness as Design Inputs

*Depth: [pattern][mechanics][trap]  |  Depends on: 1.6*

### Atomic Topics

- [ ]  Seams — constructor-injected collaborators, clock, ID generator, random source — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Fakes over mocks for stable contracts — and why — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Deterministic tests for time-based logic (TTL, rate limits) via an injected clock — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Testing concurrency — what can and can't be tested reliably; stress tests plus invariants — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Designing for observability — events and logs as part of the class design — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Property-based testing for state machines and data structures — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Contract tests shared between real and fake implementations — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  🛠️ Add an injected Clock to a token-bucket limiter and test refill timing with zero sleeps — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*
- [ ]  🛠️ Write one contract test suite and run it against both an in-memory and a Room-backed repository — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  Is there a System.currentTimeMillis() or UUID.randomUUID() buried in your business logic — can you test it deterministically today? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Why can a green test suite on a thread-safe class still not prove it's thread-safe? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 15. [1.10] Classic LLD I: Caches, Limiters, Stores & Loggers

*Depth: [pattern][mechanics][trap]  |  Depends on: 1.7, 1.8, 1.9*

### Atomic Topics

- [ ]  LRU/LFU cache with TTL, thread-safe, with a pluggable eviction policy — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Rate limiter — token bucket, leaky bucket, fixed window, sliding-window log/counter; boundary-burst behavior of each — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  In-memory KV store with TTL — lazy vs active expiration, background sweeper design — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Logger framework — levels, appenders, formatters, async appending, chain/observer usage — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Event bus — topics, subscribers, in-process delivery, isolating slow subscribers — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Extension questions to expect — distributed version, metrics, hot-reloaded config — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📝 Full design and implementation of a rate limiter with all four algorithms behind one interface, then extend with per-user limits — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*
- [ ]  🛠️ Write 5 tests including burst-at-window-boundary and concurrent consumers — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  Show with numbers how a fixed-window limiter allows ~2x the limit around a boundary, and which algorithm fixes it at what memory cost. — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  In your design, where does the lock live and what does it cost under contention? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 16. [1.11] Classic LLD II: State-Heavy Machines (Parking Lot, Elevator, Vending, ATM)

*Depth: [pattern][mechanics][trap]  |  Depends on: 1.3, 1.5*

### Atomic Topics

- [ ]  Parking lot — slot allocation strategy, pricing strategy, tickets, concurrency on allocation — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Elevator — scheduling algorithm as a Strategy, per-car state, request queues, direction logic — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Vending machine / ATM — State pattern, inventory/cash invariants, failure mid-transaction — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  The recurring move: separate state, policy and orchestration — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Edge cases interviewers probe — power loss, simultaneous requests, partial failure, refunds — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📝 Design a parking lot with strategy-based allocation and pricing; add EV slots and monthly passes without editing existing classes — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*
- [ ]  🛠️ Implement an elevator with SCAN scheduling and simulate 3 cars — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  When a new requirement arrives, does it land as a new class or an edit to a growing switch — and what does that say about your design? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  What invariant keeps cash/inventory consistent if the machine dies halfway through dispensing? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 17. [1.12] Classic LLD III: Booking, Splitting & Money

*Depth: [mechanics][trap][pattern]  |  Depends on: 0.2, 1.1, 1.7*

### Atomic Topics

- [ ]  Seat/slot booking — hold with expiry, confirm, release; double-booking prevention (lock vs optimistic version vs DB constraint) — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Splitwise — balance graph, debt simplification, exact vs percent vs equal splits, rounding — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Money — never floats; minor units or BigDecimal, currency, rounding rules, who absorbs the remainder cent — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Ledger thinking — append-only entries vs mutable balances — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Idempotent operations for retries; audit trail — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Library / reservation systems — holds, fines, availability queries — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📝 Design a movie-ticket booking core with seat holds and a payment timeout — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*
- [ ]  🛠️ Implement bill splitting so the shares always sum exactly to the total, verified with property tests — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  Why does a mutable balance with += fail audits and concurrency, and what does an append-only ledger buy you? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Where can double-booking still sneak in even with a lock — what about multiple app instances? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 18. [1.13] Classic LLD IV: Editors, Games, File Systems & Schedulers

*Depth: [pattern][mechanics]  |  Depends on: 1.3, 1.4, 1.8*

### Atomic Topics

- [ ]  Text editor — Command for undo/redo; buffer structures (gap buffer, rope, piece table) at concept level — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Tic-tac-toe / chess — board model, per-piece move validation, game state, win detection, adding new rules — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  File system — Composite, path resolution, permissions, links — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Task scheduler — time/priority ordering, delayed and recurring tasks, retries, cancellation, worker pool — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Notification system — channels, templates, preferences, retry, rate limiting, dedupe — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Turn-based games — turn engine, injected randomness — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📝 Design a task scheduler with delayed and recurring tasks and cancellation — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*
- [ ]  🛠️ Implement undo/redo with Command for a text buffer, including grouping of keystrokes — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  How does your scheduler avoid busy waiting, and what does it do when two tasks become due at once? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Chess: where does move legality live — piece, board or rules engine — and what makes adding a variant cheap? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 19. [1.14] LLD Interview Execution & Review Loop

*Depth: [pattern][concept]  |  Depends on: 1.10–1.13*

### Atomic Topics

- [ ]  Time plan — clarify, entities/API, core code, extensions — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Order of delivery — requirements, class list, key interfaces, flows, then code the core path — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Narrating tradeoffs — say the alternative you rejected and why — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Handling a new requirement live without a rewrite — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Self-review checklist — SRP, invariants, concurrency, testability, naming — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Post-mortem habit — compare against a reference and log divergences — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📝 Run 3 timed 45-minute LLD sessions on unseen problems (e.g., follow graph, food-delivery cart, meeting scheduler); log where the time went — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*
- [ ]  🛠️ Keep a divergence log in your personal notes: problem, what you did, what the reference did, why they differ — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  From an ambiguous two-line prompt, can you produce a defensible class model before writing code, under time? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  After a session, can you name the one decision you'd change and why? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

# Tier 2 — High-Level Design (HLD)

*Scaling, data, consistency, messaging, reliability, then case studies. Each case study is only a test of the clusters before it — never learn a design by memorizing its diagram.*

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

## 🔁 25. [2.6] Caching at Scale & CDNs

*Depth: [mechanics][pattern][trap]  |  Depends on: 0.3, 2.2*

### Atomic Topics

- [ ]  Distributed cache topology — client-side sharding, proxy, cluster; consistent hashing again — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Hot keys, big keys and cache avalanche (mass expiry) — mitigations — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Multi-layer caching — client, CDN, gateway, app, DB — and invalidation across layers — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Write patterns at scale — write-behind batching and its durability window — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Redis structures as design tools — sorted sets, HyperLogLog, streams, bitmaps — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Cache/DB consistency — double-write races, delete-after-write, CDC-based invalidation — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  CDN — push vs pull, cache-key design, signed URLs, edge compute — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Capacity planning — hit-ratio math and working-set size — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 Redis docs — data types (https://redis.io/docs/latest/develop/data-types/) — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  🛠️ Build a leaderboard on a Redis sorted set — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*
- [ ]  📝 Write out the race where a stale value is re-cached after an update, then design the fix — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  Walk through the exact interleaving where cache-aside serves stale data indefinitely, and what TTL or versioning stops it. — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  What hit ratio do you need for a cache to actually protect the database at your estimated load? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

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

## 🔁 27. [2.8] Reliability Patterns & Failure Handling

*Depth: [pattern][mechanics][trap]  |  Depends on: 0.1, 2.1*

### Atomic Topics

- [ ]  Timeouts everywhere — and budgets that shrink down the call chain (deadline propagation) — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Retries — exponential backoff with jitter, retry budgets, amplification across layers — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Circuit breaker — closed/open/half-open, and how it differs from just timing out — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Bulkheads — isolating resources per dependency — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Load shedding and rate limiting — refuse early, prioritize — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Backpressure propagation vs unbounded queues — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Graceful degradation — fallbacks, stale reads, kill switches — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Hedged requests and request coalescing; why retries require idempotency — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 Release It! (Nygard) — stability patterns — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  📖 Google SRE book — Handling Overload, and Addressing Cascading Failures chapters — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  🛠️ Build a client with timeout + backoff + jitter + circuit breaker against a flaky server and compare success rates to naive retries — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  Show how naive retries at three layers turn one failure into 27x load, and what stops it. — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  What does Anchor do on a 429 or 5xx from a provider — timeouts, backoff, does it honor Retry-After? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 28. [2.9] Observability, Deployment & Operations

*Depth: [concept][pattern][trap]  |  Depends on: 0.5, 2.8*

### Atomic Topics

- [ ]  Metrics, logs, traces — which question each answers; RED and USE methods — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Distributed tracing — context propagation, sampling tradeoffs — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  SLOs and error budgets as the brake on release pace — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Alerting on symptoms, not causes; avoiding alert fatigue — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Deployment — rolling, blue-green, canary, feature flags; rollback and DB-migration compatibility — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Zero-downtime schema migrations — expand/contract — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Capacity planning, load testing, chaos testing (concept) — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Disaster recovery — RPO/RTO, restore-tested backups, multi-AZ vs multi-region — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 Google SRE book — Monitoring Distributed Systems — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  📝 For one of your designs, write its SLOs, 5 alerts, the dashboards, and the rollback plan for a breaking schema change — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  What distinguishes an alert that pages a human from a dashboard signal, in your design? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  How do you roll out a column rename with zero downtime? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

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

- [ ]  Anchor authenticates against multiple providers: where does each token live, how does refresh work, and what does a leaked token allow? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Why is JWT revocation hard, and what are the real mitigations? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 30. [2.11] Architecture Styles & Service Boundaries

*Depth: [contrast][pattern][trap]  |  Depends on: 2.1, 2.4*

### Atomic Topics

- [ ]  Monolith vs modular monolith vs microservices — what actually gets better and worse — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Service boundaries by data ownership and change cadence (Conway's law) — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  API gateway, BFF, service mesh — responsibilities and cost — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Sync (REST/gRPC) vs async (events) between services — coupling and failure behavior — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Shared-database anti-pattern; contract and schema ownership — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Serverless — cold starts, limits, state, cost model — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  The distributed-monolith smell — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Evolution paths — strangler fig, extracting a service — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 Martin Fowler — 'Microservices' and 'MonolithFirst' (martinfowler.com) — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  📝 Propose service boundaries for a monolith e-commerce app, justify each split by data ownership, and defend one place you would NOT split — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  What is the first thing that breaks when you split a transactional monolith, and how do you handle it? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Which tradeoffs of your modular Android architecture map onto microservices, and which don't? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 31. [2.12] Specialized Building Blocks: Search, Geo, Media & Probabilistic Structures

*Depth: [mechanics][contrast][trap]  |  Depends on: 2.2, 2.5*

### Atomic Topics

- [ ]  Inverted index, tokenization, ranking basics (TF-IDF/BM25), indexing-pipeline lag — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Geospatial — geohash, quadtree, S2/H3; nearby-search tradeoffs — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Blob storage, chunked and resumable uploads, deduplication, content addressing — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Video — transcoding ladder, HLS/DASH adaptive bitrate, CDN delivery — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Bloom filter, HyperLogLog, Count-Min Sketch — what each answers and how it errs — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Time-series storage — downsampling, retention, high-cardinality dangers — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Batch processing basics — the MapReduce idea, when batch beats streaming — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Unique ID generation — UUID, Snowflake, ticket servers; ordering and clock issues — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  🛠️ Implement a bloom filter and measure false-positive rate against size — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*
- [ ]  🛠️ Implement geohash prefix search for nearby points — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*
- [ ]  📝 Design the upload pipeline for a 2GB video — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  In which direction can a bloom filter be wrong, and how do you use it safely in front of a DB? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Why can't you simply sort by timestamp across machines to order IDs? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 32. [2.13] Real-Time Systems: Fan-out, Presence & Delivery

*Depth: [mechanics][pattern][trap]  |  Depends on: 0.1, 2.7*

### Atomic Topics

- [ ]  WebSocket gateway — connection state, scaling stateful connections, routing a message to the right gateway — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Pub/sub backbone between gateways (Redis pub/sub, Kafka, NATS) — tradeoffs — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Fan-out on write vs on read vs hybrid — the celebrity problem — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Presence and typing indicators — heartbeat, TTL, accuracy vs cost — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Delivery guarantees — acks, per-conversation ordering, dedupe, offline queue — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Push notification path — APNs/FCM, collapse keys, best-effort delivery — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Reconnection storms and thundering herds after an outage — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Per-connection rate limits and quotas — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📝 Design a chat backend for 10M concurrent connections: gateway tier, message flow, storage, acks, offline sync — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*
- [ ]  🛠️ Build a WebSocket echo + broadcast server, connect 1k clients, kill and restart it, and observe reconnect behavior — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  How does a message from A's gateway reach B's gateway, and what if B is on three devices? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  What does FCM actually guarantee, and what must the app do to compensate? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 33. [2.14] HLD Case Studies I: Foundations (URL Shortener, Pastebin, ID Generator, Distributed Rate Limiter, KV Store)

*Depth: [pattern][contrast]  |  Depends on: 2.1–2.6*

### Atomic Topics

- [ ]  URL shortener — key generation (counter/base62 vs hash vs pre-generated), redirect latency, async analytics, expiry, abuse — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Pastebin — blob storage, metadata DB, TTL cleanup, CDN — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Distributed unique ID generator — Snowflake layout, clock-skew handling — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Distributed rate limiter — central Redis counter vs local approximations; atomic Lua; fail-open vs fail-closed — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Distributed KV store — partitioning, replication, quorums, hinted handoff, anti-entropy (Dynamo-style) — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  The reusable pattern: requirements, API, data, scaling, failure modes — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 Alex Xu — System Design Interview Vol. 1, matching chapters — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  📝 Design each of the five from scratch with estimates, then compare with a reference and log divergences — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  URL shortener: what is your collision story, and what does 301 vs 302 mean for analytics? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Distributed rate limiter: what happens when Redis is down? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 34. [2.15] HLD Case Studies II: Feeds, Notifications, Chat & Typeahead

*Depth: [pattern][contrast]  |  Depends on: 2.6, 2.7, 2.13*

### Atomic Topics

- [ ]  News feed — fan-out on write vs read vs hybrid, ranking, pagination, cache design — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Notification service — multi-channel, templating, preferences, dedupe, throttling, retry — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Chat (1:1 and group) — message storage model, ordering, receipts, media, multi-device sync — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Typeahead — trie vs prefix index, top-K precomputation, freshness, caching — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Social graph storage — adjacency lists, follower counts, celebrity handling — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Metrics that matter — fan-out latency, feed staleness, delivery success — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 Alex Xu — Vol. 1: news feed, notification system, chat, search autocomplete chapters — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  📝 Design the Twitter timeline and defend the hybrid fan-out threshold with numbers — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  At what follower count do you switch fan-out strategy, and how do you derive that number? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  How does chat preserve ordering across devices without a global clock? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 35. [2.16] HLD Case Studies III: Media & Sync (Video, File Sync, Crawler, Search)

*Depth: [pattern][contrast]  |  Depends on: 2.6, 2.7, 2.12*

### Atomic Topics

- [ ]  Video platform — upload, transcode pipeline, storage tiers, CDN, adaptive streaming, view counts at scale — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  File sync — chunking, content-hash dedupe, delta sync, metadata service, conflicts, change notification — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Web crawler — URL frontier, politeness, dedupe (URL and content hash), robots rules, crawler traps — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Search engine — crawl, index, rank, serve; index sharding; freshness — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Cost modeling — storage and egress dominate — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 Alex Xu — Vol. 1: YouTube, Google Drive, web crawler chapters — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  📝 Design file sync with conflict resolution; revisit it after the Mobile sync cluster (3.3) and note what changes — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  Why does chunk-level dedupe help, and what does it cost in metadata? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Where does a crawler get stuck, and how does your frontier prevent it? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 36. [2.17] HLD Case Studies IV: Marketplace & Money (Ride Matching, Payments, Flash Sales, Schedulers, Metrics)

*Depth: [pattern][contrast][trap]  |  Depends on: 2.4, 2.9, 2.12*

### Atomic Topics

- [ ]  Ride matching — location ingestion, geo index, matching, ETA, surge — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Payments/wallet — double-entry ledger, idempotency, reconciliation, PSP integration, state machine; never lose or duplicate money — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Ticketing / flash sale — inventory contention, queue-based admission, holds, fairness, bot control — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Distributed job scheduler — time wheel or DB polling, at-least-once, leases, retries, exactly-once effect — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Metrics/monitoring system — ingestion, TSDB, downsampling, alert evaluation, high cardinality — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Reconciliation as a first-class design element — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 Alex Xu — Vol. 2: payment system, digital wallet, hotel reservation, metrics monitoring chapters — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  📝 Design a wallet transfer with a ledger; walk through a crash at every step and state where the money is — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  Where is the money at each step if the process crashes between debit and credit, and how does reconciliation detect it? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  How do you admit 1M users to 10k tickets without melting the database? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 37. [2.18] HLD Interview Execution & Tradeoff Narration

*Depth: [pattern][concept]  |  Depends on: 2.1–2.17*

### Atomic Topics

- [ ]  Framework — requirements (functional/non-functional), estimates, API, data model, high-level design, deep dives, bottlenecks and tradeoffs — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Driving the conversation — propose, check in, go deep where the interviewer pulls — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Choosing two deep dives and justifying them — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Tradeoff language — 'X over Y because constraint Z; it costs W' — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Common pitfalls — buzzword dumping, skipping estimation, no failure modes, over-engineering v1 — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Evolving a design when requirements change mid-session — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Time budgeting for 45- and 60-minute sessions — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📝 Run 4 timed 45-minute mocks on unseen prompts; record and review each — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*
- [ ]  🛠️ Maintain a tradeoff cheat-sheet in your own words, one line per decision pair — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  Can you present the same design at three zoom levels — 30 seconds, 5 minutes, deep dive — from one diagram? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  In your last mock, where did you assert a choice without naming what you gave up? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

# Tier 3 — Mobile System Design

*Where your Android scar tissue pays off. Depends on Tier 0 and Tier 2 fundamentals, plus the Android doc's Architecture tier (offline, state, modularization).*

## 🔁 38. [3.1] Mobile Framing: Constraints & Client/Server Responsibility

*Depth: [concept][pattern][trap]  |  Depends on: 0.1; Android doc: Tiers 2–4*

### Atomic Topics

- [ ]  Constraint set — flaky networks, battery, process death, memory, storage, OS background limits, app size — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  What belongs on the client vs the server — validation, ranking, caching, business rules, source of truth — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Answer structure — requirements, API, data, client architecture, sync, failures, observability — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Lifecycle as a design input — what survives rotation, backgrounding, process death, reboot — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Network unreliable by default — offline, slow, captive portal, metered — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Backward compatibility — old app versions live forever — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Device/OS fragmentation and capability tiers — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 Android — Guide to app architecture (https://developer.android.com/topic/architecture) — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  📝 Pick a feature (uploading a post), list every failure and lifecycle interruption that can hit it, and write the designed response to each — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  For a screen you've shipped, what happens on airplane mode mid-request and after process death — verified or assumed? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Why must server APIs tolerate app versions from two years ago? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 39. [3.2] Offline-First & Local Data Design

*Depth: [mechanics][pattern][trap]  |  Depends on: 0.2, 3.1*

### Atomic Topics

- [ ]  Local DB as single source of truth; the network is a sync mechanism — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Schema for sync — client-generated stable IDs (UUID/ULID), updatedAt/version, soft deletes/tombstones, sync-state columns — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Read path — observe local data, refresh in the background — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Write path — write local first, enqueue in an outbox, reconcile — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  WorkManager as the sync engine — constraints, backoff, unique work, chaining — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Local migrations and data lifecycle — schema evolution, cache eviction, wipe on logout — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Web parallel: IndexedDB plus service worker as offline-first — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 Android — Offline-first guidance (https://developer.android.com/topic/architecture/data-layer/offline-first) — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  🛠️ Build a notes app with Room + outbox + WorkManager sync to a fake server and test with airplane mode toggles — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  Why client-generated IDs, and what breaks when the server assigns IDs and the client is offline? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  How does Rival's data layer differ from Room-based offline-first, and which guarantees are weaker? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 40. [3.3] Sync Protocols & Conflict Resolution

*Depth: [mechanics][contrast][trap]  |  Depends on: 2.3, 3.2*

### Atomic Topics

- [ ]  Sync strategies — full refresh, timestamp delta, cursor/changes feed, push-triggered pull — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Tombstones and deletion propagation; garbage-collecting tombstones — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Conflict types — concurrent edit, delete vs edit, operation ordering — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Resolution — last-write-wins (and clock-skew danger), field-level merge, server-authoritative, manual — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Version vectors, CRDTs and operational transform at concept level — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Optimistic UI with rollback; reconciliation when the server responds — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Idempotent client requests; retry-queue ordering and dependencies between queued ops — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Partial failure of batched sync — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 CRDT introduction (https://crdt.tech/) — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  🛠️ Two clients edit the same note offline; implement LWW then field-level merge and find a case where LWW loses data — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*
- [ ]  📝 Specify a sync protocol with cursors and tombstones, including the failure of each step — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  Why can LWW based on device wall clocks silently drop a user's edit? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  How does a queue handle op B depending on a server ID that op A hasn't created yet? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 41. [3.4] Mobile Networking Layer Design

*Depth: [mechanics][pattern][trap]  |  Depends on: 0.1, 2.8, 2.10*

### Atomic Topics

- [ ]  API shape for mobile — batching, field selection, pagination, avoiding chatty screens; GraphQL/BFF tradeoffs — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  HTTP caching on device — ETag, Cache-Control, OkHttp cache vs app-level cache — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Retry policy — which failures, backoff plus jitter, idempotency keys, Retry-After — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Auth — token refresh with single-flight, 401 handling, logout on refresh failure — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Connection behavior — HTTP/2 multiplexing, pooling, DNS and TLS cost on cellular, per-operation timeouts — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Payload — compression, protobuf vs JSON, image sizing, delta responses — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Security — pinning tradeoffs and rotation, network security config — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Network-state handling — metered, offline, captive portals — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  🛠️ Build an OkHttp stack whose Authenticator does single-flight token refresh; fire 20 parallel requests with an expired token and confirm exactly one refresh — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*
- [ ]  📝 Redesign a chatty screen's API calls into a single call and justify the new contract — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  What happens in your app when 10 concurrent calls hit 401 at once? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Why is certificate pinning an availability risk, and how do you ship rotation safely? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 42. [3.5] Pagination, Feeds & List Performance

*Depth: [mechanics][pattern][trap]  |  Depends on: 0.1, 3.2*

### Atomic Topics

- [ ]  Cursor/keyset pagination as a contract; stable ordering; inserts and deletes while scrolling — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Paging 3 — PagingSource, RemoteMediator, LoadState, invalidation, placeholders — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Single-source-of-truth paging — network to DB to UI with remote keys — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Prefetch distance and page-size tradeoffs; memory limits — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Feed freshness — pull-to-refresh vs new-items banner, gap handling, dedupe — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Ranking on server vs client; impression logging — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  List rendering — LazyColumn keys, stable item models, avoiding recomposition storms — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 Android — Paging 3 overview (https://developer.android.com/topic/libraries/architecture/paging/v3-overview) — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  🛠️ Build a RemoteMediator-backed feed with Room; simulate a server-side insert mid-scroll and handle dedupe and gaps — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  What is the failure mode of offset pagination on a feed with inserts, and how does your cursor design avoid it? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  How do remote keys survive process death? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 43. [3.6] Media Loading, Caching & Upload

*Depth: [mechanics][pattern][trap]  |  Depends on: 3.4*

### Atomic Topics

- [ ]  Image pipeline — request dedupe, memory cache (byte-sized LRU), disk cache, downsampling to target size, bitmap pooling — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Image URL design — server-side resizing/CDN variants, formats (WebP/AVIF), placeholders/blurhash — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Prefetching and cancellation while scrolling fast — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Video playback — Media3/ExoPlayer, adaptive streaming, caching, preloading the next item, buffering strategy — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Upload — chunked/resumable, background execution, compression, progress/cancel, resume across process death — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Permissions and scoped-storage implications — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Data and battery cost awareness — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  🛠️ Implement a minimal image loader with memory and disk LRU plus request coalescing — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*
- [ ]  📝 Design resumable upload for a 500MB video that resumes after process death — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  How does your image loader avoid decoding a 4000px image for a 100dp thumbnail? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Where is upload state persisted so resume works after the process is killed? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 44. [3.7] Real-Time & Push on Mobile

*Depth: [mechanics][pattern][trap]  |  Depends on: 2.13, 3.1*

### Atomic Topics

- [ ]  FCM — data vs notification messages, priority, Doze and App Standby effects, best-effort delivery — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Push as a hint to sync, not the payload of record — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  WebSocket on mobile — lifecycle (connect in foreground), heartbeats, reconnect with backoff + jitter, network changes — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Ordering, dedupe, acks, resume from last-seen cursor — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Battery — batching, avoiding wakeups, JobScheduler constraints — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Notification UX — channels, grouping, actions, deep links, runtime permission — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Token lifecycle — FCM token rotation, server mapping, stale-token cleanup — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Foreground-service limits and justified use — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  🛠️ Build a chat client that reconnects, resumes by cursor and dedupes after a forced disconnect — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*
- [ ]  📝 Design a notification pipeline from server event to a tapped deep link — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  If FCM drops a push, how does the app still become correct? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Which reconnection policy avoids a reconnect storm after a server restart? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 45. [3.8] Mobile Case Studies I: Chat, Social Feed, Offline Notes

*Depth: [pattern][contrast]  |  Depends on: 3.2–3.7*

### Atomic Topics

- [ ]  Chat client — local message store, send-queue states (pending/sent/delivered/read/failed), ordering, media, groups, search — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Social feed — paging, image-heavy lists, optimistic likes, offline reads, ranking signals — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Notes app — offline editing, sync, conflict resolution, attachments — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Shared structure — requirements, data model, API, sync, UI state, failures, telemetry — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📝 Do a full mobile design for each of the three; for each, list five failure scenarios and the designed behavior — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  Can you explain the chat message state machine and what the UI shows in each state? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  What does your design do about duplicated likes caused by retries? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 46. [3.9] Mobile Case Studies II: Uploads, Video, Maps, Payments, Tracking

*Depth: [pattern][contrast][trap]  |  Depends on: 2.10, 3.6, 3.7*

### Atomic Topics

- [ ]  Photo/video upload — queue, compression, resume, background execution — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Video player/feed — preload, caching, adaptive bitrate, memory — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Maps and location tracking — sampling, battery, geofencing, foreground service, batched uploads, privacy — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Payments/wallet client — idempotent submission, pending states, secure storage, biometric gating, receipts, reconciliation with server truth — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Ride/delivery tracking — live updates, interpolation, reconnect — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Security and privacy as design inputs — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📝 Design a payments client flow where the app is killed right after tapping Pay: define states, idempotency, and how the UI resolves on next launch — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  After 'Pay' is tapped and the app dies, how does the client learn whether the payment happened? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  What battery-vs-accuracy tradeoff did you choose for location sampling, and why? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 47. [3.10] Client Observability, Release Engineering & Scale

*Depth: [pattern][trap]  |  Depends on: 2.9; Android doc: Modularization*

### Atomic Topics

- [ ]  Crash and ANR reporting, symbolication, release health — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Analytics — event schema design, batching, privacy, sampling, offline buffering — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Performance — startup, jank, memory budgets; baseline profiles; macrobenchmark; vitals — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Feature flags, remote config, kill switches, A/B tests, staged rollout, forced upgrade — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  API/version compatibility strategy across app versions — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Modularization for build and team scale — module contracts and ownership — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Testing strategy at scale — pyramid, screenshot tests, CI gating — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Incident response from the client side — store-review constraints on hotfixes, server-side mitigation — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📝 Write a release plan for a risky change (a new sync engine): flags, staged rollout %, metric gates, rollback path — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*
- [ ]  🛠️ Add a remote kill switch to an existing code path and verify it flips behavior without a release — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*

### Reality Check — Illusion vs Actual

- [ ]  If a release shows a crash spike at 5% rollout, what's your sequence of actions, and what can't you undo? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  How do you keep analytics from becoming a battery, data or privacy liability? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 48. [3.11] Mobile Design Execution & Framing

*Depth: [pattern][concept]  |  Depends on: 3.1–3.10*

### Atomic Topics

- [ ]  Structure for 45–60 minutes — requirements, constraints, API, data, client architecture, sync/failure, scale/observability — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Calling out client-vs-server decisions explicitly — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Offline and lifecycle addressed in every answer — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Tradeoff narration with concrete mobile costs — battery, data, memory — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Common weak answers — UI layering only, ignoring offline, no failure modes — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Whiteboard artifacts — sync sequence diagram, send-queue state diagram — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📝 Run 3 timed mobile design mocks (Instagram feed, WhatsApp, Google Drive mobile); review divergences — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  Does each of your answers state what happens offline and on process death without being asked? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Can you draw the sync sequence diagram from memory? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

# Tier 4 — Applying It: Reviews, Decisions & the Practice Loop

*What turns knowledge into the ability to hold your own in a design discussion. Start the practice loop (4.2) as soon as Tier 1 starts — it runs alongside everything.*

## 🔁 49. [4.1] Tradeoff Articulation, ADRs & Design Reviews at Work

*Depth: [pattern][concept]  |  Depends on: any Tier 1–3 cluster*

### Atomic Topics

- [ ]  Decision records — context, options, decision, consequences, revisit triggers — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Naming constraints and non-goals up front — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Quantifying tradeoffs — latency, cost, complexity, team skill, reversibility — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Reversible vs irreversible decisions (two-way vs one-way doors) — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Reviewing other people's designs — questions on failure modes, scale limits, migration path, ownership — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Presenting to different audiences — engineers, PMs, leadership — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Avoiding resume-driven design; the simplest thing that works, plus the trigger to evolve — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  📖 ADR templates and guidance (https://adr.github.io/) — *Tick off when: you have read it AND can summarize its core point from memory with the link closed.*
- [ ]  📝 Write an ADR for a real decision in a current project (sync strategy, module split), including rejected options — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  Can you defend a decision in review by stating the strongest argument against it? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Which recent decision was a one-way door, and did you treat it like one? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

## 🔁 50. [4.2] Practice Loop, Spaced Review & Gap Tracking

*Depth: [pattern]  |  Depends on: start after 1.1; runs continuously*

### Atomic Topics

- [ ]  Weekly cadence — one LLD, one HLD, one mobile design, timed — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Divergence log — compare to references and record where your reasoning differed and why — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Spaced re-design — redo a past problem cold after 2–4 weeks — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Teach-back — explain a cluster to someone, or write it as a short doc — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Reading real postmortems and engineering blogs; extract the design lesson — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*
- [ ]  Gap triage — map recurring misses back to the cluster that owns them — *Tick off when: you can explain this out loud, unprompted, in your own words, including why it exists and what it costs.*

### Resource & Exercise

- [ ]  🛠️ Set up a practice log in your personal notes: problem, date, time taken, divergences, cluster to revisit — *Tick off when: you have built/run this yourself and seen the real output, not just read the steps.*
- [ ]  📝 Redo your first problem cold after three weeks and compare against your original — *Tick off when: you have written the full design on paper, compared it against a reference, and logged where yours diverged and why.*

### Reality Check — Illusion vs Actual

- [ ]  Which three clusters does your divergence log point to most, and have you actually revisited them? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*
- [ ]  Can you redo an earlier problem cold and measurably do better? — *Tick off when: you can answer this cold, in under 30 seconds, with no notes. A shaky or partial answer means leave it unchecked.*

---

# How to Actually Use This

1. **Do Tier 0 fast but honestly.** It is a prerequisite slice, not the destination. If a Reality Check there stumps you, it will stump you again inside a Tier 1 or Tier 2 problem.
2. **Start the practice loop (4.2) on day one of Tier 1.** One timed problem a week plus a divergence log beats reading ten clusters in a row.
3. **Never learn a case study by memorizing the diagram.** Design it first, then compare. The gap between your version and the reference is the actual learning.
4. **Revisit Tier 2 case studies after Tier 3.** Designs like file sync and chat look different once you've worked through client-side sync and conflict resolution.
5. **Re-answer Reality Checks cold weeks later**, without rereading the topics. Surviving a cold re-answer is the real retention signal, not the checkbox.