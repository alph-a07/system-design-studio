const CURRICULUM_CLUSTERS = [
  {
    "id": "cluster.0.1",
    "code": "0.1",
    "title": "1. [0.1] APIs & Network Transport for Design",
    "order": 1,
    "topics": [
      {
        "id": "topic.0.1.tcp-vs-udp",
        "title": "TCP vs UDP",
        "status": "unseen"
      },
      {
        "id": "topic.0.1.http-1-1-vs-http-2-vs-http-3",
        "title": "HTTP/1.1 vs HTTP/2 vs HTTP/3",
        "status": "unseen"
      },
      {
        "id": "topic.0.1.tls-handshake-cost-and-session-resu",
        "title": "TLS handshake cost and session resumption",
        "status": "unseen"
      },
      {
        "id": "topic.0.1.rest-vs-grpc-vs-graphql",
        "title": "REST vs gRPC vs GraphQL",
        "status": "unseen"
      },
      {
        "id": "topic.0.1.polling-vs-long-polling-vs-sse-vs-w",
        "title": "Polling vs long-polling vs SSE vs WebSocket",
        "status": "unseen"
      },
      {
        "id": "topic.0.1.pagination-offset-vs-cursor-keyset",
        "title": "Pagination: offset vs cursor/keyset",
        "status": "unseen"
      },
      {
        "id": "topic.0.1.idempotency",
        "title": "Idempotency",
        "status": "unseen"
      },
      {
        "id": "topic.0.1.api-versioning-and-backward-compati",
        "title": "API versioning and backward compatibility",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.0.2",
    "code": "0.2",
    "title": "2. [0.2] Databases: Indexes, Transactions & Isolation",
    "order": 2,
    "topics": [
      {
        "id": "topic.0.2.b-tree-index",
        "title": "B-tree index",
        "status": "unseen"
      },
      {
        "id": "topic.0.2.lsm-tree",
        "title": "LSM tree",
        "status": "unseen"
      },
      {
        "id": "topic.0.2.composite-indexes",
        "title": "Composite indexes",
        "status": "unseen"
      },
      {
        "id": "topic.0.2.reading-a-query-plan",
        "title": "Reading a query plan",
        "status": "unseen"
      },
      {
        "id": "topic.0.2.acid",
        "title": "ACID",
        "status": "unseen"
      },
      {
        "id": "topic.0.2.isolation-levels",
        "title": "Isolation levels",
        "status": "unseen"
      },
      {
        "id": "topic.0.2.optimistic-vs-pessimistic-concurren",
        "title": "Optimistic vs pessimistic concurrency control; version columns; lost updates",
        "status": "unseen"
      },
      {
        "id": "topic.0.2.normalization-vs-denormalization",
        "title": "Normalization vs denormalization",
        "status": "unseen"
      },
      {
        "id": "topic.0.2.sql-vs-nosql",
        "title": "SQL vs NoSQL",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.0.3",
    "code": "0.3",
    "title": "3. [0.3] Caching Fundamentals",
    "order": 3,
    "topics": [
      {
        "id": "topic.0.3.cache-aside-vs-read-through-vs-writ",
        "title": "Cache-aside vs read-through vs write-through vs write-back vs write-around",
        "status": "unseen"
      },
      {
        "id": "topic.0.3.eviction",
        "title": "Eviction",
        "status": "unseen"
      },
      {
        "id": "topic.0.3.invalidation",
        "title": "Invalidation",
        "status": "unseen"
      },
      {
        "id": "topic.0.3.cache-stampede-thundering-herd",
        "title": "Cache stampede / thundering herd",
        "status": "unseen"
      },
      {
        "id": "topic.0.3.cache-penetration-nonexistent-keys",
        "title": "Cache penetration (nonexistent keys)",
        "status": "unseen"
      },
      {
        "id": "topic.0.3.http-caching",
        "title": "HTTP caching",
        "status": "unseen"
      },
      {
        "id": "topic.0.3.cdn-basics",
        "title": "CDN basics",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.0.4",
    "code": "0.4",
    "title": "4. [0.4] Queues, Async Messaging & Delivery Semantics",
    "order": 4,
    "topics": [
      {
        "id": "topic.0.4.queue-competing-consumers-vs-pub-su",
        "title": "Queue (competing consumers) vs pub/sub (fan-out)",
        "status": "unseen"
      },
      {
        "id": "topic.0.4.at-most-once-vs-at-least-once-vs-ex",
        "title": "At-most-once vs at-least-once vs exactly-once",
        "status": "unseen"
      },
      {
        "id": "topic.0.4.acknowledgement-visibility-timeout-",
        "title": "Acknowledgement, visibility timeout, redelivery, poison messages, dead-letter queues",
        "status": "unseen"
      },
      {
        "id": "topic.0.4.ordering-guarantees",
        "title": "Ordering guarantees",
        "status": "unseen"
      },
      {
        "id": "topic.0.4.backpressure",
        "title": "Backpressure",
        "status": "unseen"
      },
      {
        "id": "topic.0.4.why-async-at-all",
        "title": "Why async at all",
        "status": "unseen"
      },
      {
        "id": "topic.0.4.outbox-pattern-concept-level",
        "title": "Outbox pattern (concept level)",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.0.5",
    "code": "0.5",
    "title": "5. [0.5] Estimation, Latency Numbers & Availability Math",
    "order": 5,
    "topics": [
      {
        "id": "topic.0.5.latency-orders-of-magnitude",
        "title": "Latency orders of magnitude",
        "status": "unseen"
      },
      {
        "id": "topic.0.5.back-of-envelope-method",
        "title": "Back-of-envelope method",
        "status": "unseen"
      },
      {
        "id": "topic.0.5.powers-of-two-and-rounding-discipli",
        "title": "Powers of two and rounding discipline",
        "status": "unseen"
      },
      {
        "id": "topic.0.5.availability-nines",
        "title": "Availability nines",
        "status": "unseen"
      },
      {
        "id": "topic.0.5.sli-slo-sla-error-budget",
        "title": "SLI / SLO / SLA / error budget",
        "status": "unseen"
      },
      {
        "id": "topic.0.5.throughput-vs-latency-percentiles-p",
        "title": "Throughput vs latency; percentiles (p50/p95/p99); tail-latency amplification under fan-out",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.1.1",
    "code": "1.1",
    "title": "6. [1.1] From Requirements to Model: Entities, Invariants & Ownership",
    "order": 6,
    "topics": [
      {
        "id": "topic.1.1.extract-nouns-and-verbs-then-separa",
        "title": "Extract nouns and verbs, then separate real entities from attributes and from behaviors",
        "status": "unseen"
      },
      {
        "id": "topic.1.1.value-object-vs-entity",
        "title": "Value object vs entity",
        "status": "unseen"
      },
      {
        "id": "topic.1.1.invariants",
        "title": "Invariants",
        "status": "unseen"
      },
      {
        "id": "topic.1.1.aggregate-boundary",
        "title": "Aggregate boundary",
        "status": "unseen"
      },
      {
        "id": "topic.1.1.state-ownership",
        "title": "State ownership",
        "status": "unseen"
      },
      {
        "id": "topic.1.1.make-illegal-states-unrepresentable",
        "title": "Make illegal states unrepresentable",
        "status": "unseen"
      },
      {
        "id": "topic.1.1.clarifying-questions-before-modelin",
        "title": "Clarifying questions before modeling",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.1.2",
    "code": "1.2",
    "title": "7. [1.2] Designing for Change: Cohesion, Coupling & Variation Points",
    "order": 7,
    "topics": [
      {
        "id": "topic.1.2.cohesion-and-coupling",
        "title": "Cohesion and coupling",
        "status": "unseen"
      },
      {
        "id": "topic.1.2.find-the-axis-of-change-first-and-a",
        "title": "Find the axis of change first and abstract only what varies",
        "status": "unseen"
      },
      {
        "id": "topic.1.2.composition-over-inheritance-as-a-d",
        "title": "Composition over inheritance as a default",
        "status": "unseen"
      },
      {
        "id": "topic.1.2.depend-on-abstractions-at-boundarie",
        "title": "Depend on abstractions at boundaries you own, on concretes inside a module",
        "status": "unseen"
      },
      {
        "id": "topic.1.2.dependency-direction-and-layering",
        "title": "Dependency direction and layering",
        "status": "unseen"
      },
      {
        "id": "topic.1.2.law-of-demeter-and-tell-don-t-ask-a",
        "title": "Law of Demeter and tell-don't-ask as coupling reducers",
        "status": "unseen"
      },
      {
        "id": "topic.1.2.over-engineering-signals",
        "title": "Over-engineering signals",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.1.3",
    "code": "1.3",
    "title": "8. [1.3] Patterns in Context I: Choosing by Problem Shape",
    "order": 8,
    "topics": [
      {
        "id": "topic.1.3.strategy",
        "title": "Strategy",
        "status": "unseen"
      },
      {
        "id": "topic.1.3.state",
        "title": "State",
        "status": "unseen"
      },
      {
        "id": "topic.1.3.observer-in-process-pub-sub",
        "title": "Observer / in-process pub-sub",
        "status": "unseen"
      },
      {
        "id": "topic.1.3.command",
        "title": "Command",
        "status": "unseen"
      },
      {
        "id": "topic.1.3.decorator",
        "title": "Decorator",
        "status": "unseen"
      },
      {
        "id": "topic.1.3.factory-method-abstract-factory-bui",
        "title": "Factory Method / Abstract Factory / Builder",
        "status": "unseen"
      },
      {
        "id": "topic.1.3.for-every-pattern-the-force-that-ju",
        "title": "For every pattern: the force that justifies it, and the cost it adds",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.1.4",
    "code": "1.4",
    "title": "9. [1.4] Patterns in Context II: Structure, Pipelines & Their Misuse",
    "order": 9,
    "topics": [
      {
        "id": "topic.1.4.chain-of-responsibility",
        "title": "Chain of Responsibility",
        "status": "unseen"
      },
      {
        "id": "topic.1.4.template-method-vs-strategy",
        "title": "Template Method vs Strategy",
        "status": "unseen"
      },
      {
        "id": "topic.1.4.adapter-vs-facade-vs-proxy",
        "title": "Adapter vs Facade vs Proxy",
        "status": "unseen"
      },
      {
        "id": "topic.1.4.mediator-vs-observer",
        "title": "Mediator vs Observer",
        "status": "unseen"
      },
      {
        "id": "topic.1.4.visitor-and-double-dispatch",
        "title": "Visitor and double dispatch",
        "status": "unseen"
      },
      {
        "id": "topic.1.4.flyweight-composite-memento-iterato",
        "title": "Flyweight / Composite / Memento / Iterator",
        "status": "unseen"
      },
      {
        "id": "topic.1.4.pattern-misuse",
        "title": "Pattern misuse",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.1.5",
    "code": "1.5",
    "title": "10. [1.5] State Machines & Workflows as First-Class Design",
    "order": 10,
    "topics": [
      {
        "id": "topic.1.5.explicit-states-events-transitions-",
        "title": "Explicit states, events, transitions, guards and actions",
        "status": "unseen"
      },
      {
        "id": "topic.1.5.illegal-transitions",
        "title": "Illegal transitions",
        "status": "unseen"
      },
      {
        "id": "topic.1.5.sealed-types-plus-a-pure-transition",
        "title": "Sealed types plus a pure transition function",
        "status": "unseen"
      },
      {
        "id": "topic.1.5.idempotent-transitions",
        "title": "Idempotent transitions",
        "status": "unseen"
      },
      {
        "id": "topic.1.5.persisting-a-state-machine",
        "title": "Persisting a state machine",
        "status": "unseen"
      },
      {
        "id": "topic.1.5.timeouts-and-expirations-as-events",
        "title": "Timeouts and expirations as events",
        "status": "unseen"
      },
      {
        "id": "topic.1.5.hierarchical-states-when-flat-table",
        "title": "Hierarchical states when flat tables explode",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.1.6",
    "code": "1.6",
    "title": "11. [1.6] API & Contract Design for Classes and Modules",
    "order": 11,
    "topics": [
      {
        "id": "topic.1.6.smallest-public-surface",
        "title": "Smallest public surface",
        "status": "unseen"
      },
      {
        "id": "topic.1.6.error-modeling",
        "title": "Error modeling",
        "status": "unseen"
      },
      {
        "id": "topic.1.6.validation-placement",
        "title": "Validation placement",
        "status": "unseen"
      },
      {
        "id": "topic.1.6.immutability-and-defensive-copying-",
        "title": "Immutability and defensive copying at API edges",
        "status": "unseen"
      },
      {
        "id": "topic.1.6.builders-defaults-and-named-argumen",
        "title": "Builders, defaults and named arguments vs constructor explosion",
        "status": "unseen"
      },
      {
        "id": "topic.1.6.backward-compatible-evolution",
        "title": "Backward-compatible evolution",
        "status": "unseen"
      },
      {
        "id": "topic.1.6.naming-and-abstraction-level",
        "title": "Naming and abstraction level",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.1.7",
    "code": "1.7",
    "title": "12. [1.7] Concurrency in Class Design",
    "order": 12,
    "topics": [
      {
        "id": "topic.1.7.shared-mutable-state-is-the-problem",
        "title": "Shared mutable state is the problem",
        "status": "unseen"
      },
      {
        "id": "topic.1.7.check-then-act-and-read-modify-writ",
        "title": "Check-then-act and read-modify-write races",
        "status": "unseen"
      },
      {
        "id": "topic.1.7.lock-granularity",
        "title": "Lock granularity",
        "status": "unseen"
      },
      {
        "id": "topic.1.7.composing-thread-safe-operations-is",
        "title": "Composing thread-safe operations is not automatically thread-safe",
        "status": "unseen"
      },
      {
        "id": "topic.1.7.producer-consumer-with-bounded-queu",
        "title": "Producer-consumer with bounded queues; blocking vs suspending designs",
        "status": "unseen"
      },
      {
        "id": "topic.1.7.choosing-concurrent-collections-by-",
        "title": "Choosing concurrent collections by access pattern",
        "status": "unseen"
      },
      {
        "id": "topic.1.7.kotlin-tools",
        "title": "Kotlin tools",
        "status": "unseen"
      },
      {
        "id": "topic.1.7.visibility-and-safe-publication",
        "title": "Visibility and safe publication",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.1.8",
    "code": "1.8",
    "title": "13. [1.8] Data Structure Selection for Design Problems",
    "order": 13,
    "topics": [
      {
        "id": "topic.1.8.choose-by-operations-needed",
        "title": "Choose by operations needed",
        "status": "unseen"
      },
      {
        "id": "topic.1.8.hashmap-doubly-linked-list-for-o-1-",
        "title": "HashMap + doubly linked list for O(1) LRU; LinkedHashMap access-order shortcut and its limits",
        "status": "unseen"
      },
      {
        "id": "topic.1.8.heap-priorityqueue",
        "title": "Heap / PriorityQueue",
        "status": "unseen"
      },
      {
        "id": "topic.1.8.trie",
        "title": "Trie",
        "status": "unseen"
      },
      {
        "id": "topic.1.8.sorted-maps-and-interval-structures",
        "title": "Sorted maps and interval structures (TreeMap floor/ceiling)",
        "status": "unseen"
      },
      {
        "id": "topic.1.8.sliding-window-and-deque-structures",
        "title": "Sliding window and deque structures",
        "status": "unseen"
      },
      {
        "id": "topic.1.8.bitsets-bloom-filters-and-counting-",
        "title": "Bitsets, bloom filters and counting structures at LLD scale",
        "status": "unseen"
      },
      {
        "id": "topic.1.8.complexity-under-real-constraints",
        "title": "Complexity under real constraints",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.1.9",
    "code": "1.9",
    "title": "14. [1.9] Testability, Time & Randomness as Design Inputs",
    "order": 14,
    "topics": [
      {
        "id": "topic.1.9.seams",
        "title": "Seams",
        "status": "unseen"
      },
      {
        "id": "topic.1.9.fakes-over-mocks-for-stable-contrac",
        "title": "Fakes over mocks for stable contracts",
        "status": "unseen"
      },
      {
        "id": "topic.1.9.deterministic-tests-for-time-based-",
        "title": "Deterministic tests for time-based logic (TTL, rate limits) via an injected clock",
        "status": "unseen"
      },
      {
        "id": "topic.1.9.testing-concurrency",
        "title": "Testing concurrency",
        "status": "unseen"
      },
      {
        "id": "topic.1.9.designing-for-observability",
        "title": "Designing for observability",
        "status": "unseen"
      },
      {
        "id": "topic.1.9.property-based-testing-for-state-ma",
        "title": "Property-based testing for state machines and data structures",
        "status": "unseen"
      },
      {
        "id": "topic.1.9.contract-tests-shared-between-real-",
        "title": "Contract tests shared between real and fake implementations",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.1.10",
    "code": "1.10",
    "title": "15. [1.10] Classic LLD I: Caches, Limiters, Stores & Loggers",
    "order": 15,
    "topics": [
      {
        "id": "topic.1.10.lru-lfu-cache-with-ttl-thread-safe-",
        "title": "LRU/LFU cache with TTL, thread-safe, with a pluggable eviction policy",
        "status": "unseen"
      },
      {
        "id": "topic.1.10.rate-limiter",
        "title": "Rate limiter",
        "status": "unseen"
      },
      {
        "id": "topic.1.10.in-memory-kv-store-with-ttl",
        "title": "In-memory KV store with TTL",
        "status": "unseen"
      },
      {
        "id": "topic.1.10.logger-framework",
        "title": "Logger framework",
        "status": "unseen"
      },
      {
        "id": "topic.1.10.event-bus",
        "title": "Event bus",
        "status": "unseen"
      },
      {
        "id": "topic.1.10.extension-questions-to-expect",
        "title": "Extension questions to expect",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.1.11",
    "code": "1.11",
    "title": "16. [1.11] Classic LLD II: State-Heavy Machines (Parking Lot, Elevator, Vending, ATM)",
    "order": 16,
    "topics": [
      {
        "id": "topic.1.11.parking-lot",
        "title": "Parking lot",
        "status": "unseen"
      },
      {
        "id": "topic.1.11.elevator",
        "title": "Elevator",
        "status": "unseen"
      },
      {
        "id": "topic.1.11.vending-machine-atm",
        "title": "Vending machine / ATM",
        "status": "unseen"
      },
      {
        "id": "topic.1.11.the-recurring-move-separate-state-p",
        "title": "The recurring move: separate state, policy and orchestration",
        "status": "unseen"
      },
      {
        "id": "topic.1.11.edge-cases-interviewers-probe",
        "title": "Edge cases interviewers probe",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.1.12",
    "code": "1.12",
    "title": "17. [1.12] Classic LLD III: Booking, Splitting & Money",
    "order": 17,
    "topics": [
      {
        "id": "topic.1.12.seat-slot-booking",
        "title": "Seat/slot booking",
        "status": "unseen"
      },
      {
        "id": "topic.1.12.splitwise",
        "title": "Splitwise",
        "status": "unseen"
      },
      {
        "id": "topic.1.12.money",
        "title": "Money",
        "status": "unseen"
      },
      {
        "id": "topic.1.12.ledger-thinking",
        "title": "Ledger thinking",
        "status": "unseen"
      },
      {
        "id": "topic.1.12.idempotent-operations-for-retries-a",
        "title": "Idempotent operations for retries; audit trail",
        "status": "unseen"
      },
      {
        "id": "topic.1.12.library-reservation-systems",
        "title": "Library / reservation systems",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.1.13",
    "code": "1.13",
    "title": "18. [1.13] Classic LLD IV: Editors, Games, File Systems & Schedulers",
    "order": 18,
    "topics": [
      {
        "id": "topic.1.13.text-editor",
        "title": "Text editor",
        "status": "unseen"
      },
      {
        "id": "topic.1.13.tic-tac-toe-chess",
        "title": "Tic-tac-toe / chess",
        "status": "unseen"
      },
      {
        "id": "topic.1.13.file-system",
        "title": "File system",
        "status": "unseen"
      },
      {
        "id": "topic.1.13.task-scheduler",
        "title": "Task scheduler",
        "status": "unseen"
      },
      {
        "id": "topic.1.13.notification-system",
        "title": "Notification system",
        "status": "unseen"
      },
      {
        "id": "topic.1.13.turn-based-games",
        "title": "Turn-based games",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.1.14",
    "code": "1.14",
    "title": "19. [1.14] LLD Interview Execution & Review Loop",
    "order": 19,
    "topics": [
      {
        "id": "topic.1.14.time-plan",
        "title": "Time plan",
        "status": "unseen"
      },
      {
        "id": "topic.1.14.order-of-delivery",
        "title": "Order of delivery",
        "status": "unseen"
      },
      {
        "id": "topic.1.14.narrating-tradeoffs",
        "title": "Narrating tradeoffs",
        "status": "unseen"
      },
      {
        "id": "topic.1.14.handling-a-new-requirement-live-wit",
        "title": "Handling a new requirement live without a rewrite",
        "status": "unseen"
      },
      {
        "id": "topic.1.14.self-review-checklist",
        "title": "Self-review checklist",
        "status": "unseen"
      },
      {
        "id": "topic.1.14.post-mortem-habit",
        "title": "Post-mortem habit",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.2.1",
    "code": "2.1",
    "title": "20. [2.1] Scalability Fundamentals & Load Balancing",
    "order": 20,
    "topics": [
      {
        "id": "topic.2.1.vertical-vs-horizontal-scaling",
        "title": "Vertical vs horizontal scaling",
        "status": "unseen"
      },
      {
        "id": "topic.2.1.stateless-services",
        "title": "Stateless services",
        "status": "unseen"
      },
      {
        "id": "topic.2.1.load-balancer-l4-vs-l7",
        "title": "Load balancer L4 vs L7",
        "status": "unseen"
      },
      {
        "id": "topic.2.1.algorithms",
        "title": "Algorithms",
        "status": "unseen"
      },
      {
        "id": "topic.2.1.health-checks-connection-draining-s",
        "title": "Health checks, connection draining, sticky sessions and why they hurt",
        "status": "unseen"
      },
      {
        "id": "topic.2.1.autoscaling-signals-lag-thrash-and-",
        "title": "Autoscaling signals, lag, thrash and warm-up",
        "status": "unseen"
      },
      {
        "id": "topic.2.1.single-points-of-failure",
        "title": "Single points of failure",
        "status": "unseen"
      },
      {
        "id": "topic.2.1.bottleneck-analysis",
        "title": "Bottleneck analysis",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.2.2",
    "code": "2.2",
    "title": "21. [2.2] Data Partitioning & Consistent Hashing",
    "order": 21,
    "topics": [
      {
        "id": "topic.2.2.why-partition",
        "title": "Why partition",
        "status": "unseen"
      },
      {
        "id": "topic.2.2.range-vs-hash-vs-directory-based-pa",
        "title": "Range vs hash vs directory-based partitioning",
        "status": "unseen"
      },
      {
        "id": "topic.2.2.consistent-hashing-and-virtual-node",
        "title": "Consistent hashing and virtual nodes",
        "status": "unseen"
      },
      {
        "id": "topic.2.2.hot-keys-and-hot-partitions",
        "title": "Hot keys and hot partitions",
        "status": "unseen"
      },
      {
        "id": "topic.2.2.rebalancing-strategies",
        "title": "Rebalancing strategies",
        "status": "unseen"
      },
      {
        "id": "topic.2.2.secondary-indexes-in-sharded-stores",
        "title": "Secondary indexes in sharded stores",
        "status": "unseen"
      },
      {
        "id": "topic.2.2.cross-shard-queries-and-transaction",
        "title": "Cross-shard queries and transactions",
        "status": "unseen"
      },
      {
        "id": "topic.2.2.choosing-a-shard-key",
        "title": "Choosing a shard key",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.2.3",
    "code": "2.3",
    "title": "22. [2.3] Replication, Consistency Models & CAP/PACELC",
    "order": 22,
    "topics": [
      {
        "id": "topic.2.3.leader-follower-multi-leader-leader",
        "title": "Leader-follower, multi-leader, leaderless",
        "status": "unseen"
      },
      {
        "id": "topic.2.3.sync-vs-async-replication",
        "title": "Sync vs async replication",
        "status": "unseen"
      },
      {
        "id": "topic.2.3.replication-lag-anomalies",
        "title": "Replication-lag anomalies",
        "status": "unseen"
      },
      {
        "id": "topic.2.3.quorums-w-r-n",
        "title": "Quorums (W+R>N)",
        "status": "unseen"
      },
      {
        "id": "topic.2.3.conflict-resolution",
        "title": "Conflict resolution",
        "status": "unseen"
      },
      {
        "id": "topic.2.3.consistency-spectrum",
        "title": "Consistency spectrum",
        "status": "unseen"
      },
      {
        "id": "topic.2.3.cap",
        "title": "CAP",
        "status": "unseen"
      },
      {
        "id": "topic.2.3.split-brain-failover-and-fencing",
        "title": "Split brain, failover and fencing",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.2.4",
    "code": "2.4",
    "title": "23. [2.4] Distributed Coordination & Transactions",
    "order": 23,
    "topics": [
      {
        "id": "topic.2.4.why-distributed-transactions-are-ha",
        "title": "Why distributed transactions are hard",
        "status": "unseen"
      },
      {
        "id": "topic.2.4.2pc",
        "title": "2PC",
        "status": "unseen"
      },
      {
        "id": "topic.2.4.saga",
        "title": "Saga",
        "status": "unseen"
      },
      {
        "id": "topic.2.4.outbox-plus-idempotent-consumers",
        "title": "Outbox plus idempotent consumers",
        "status": "unseen"
      },
      {
        "id": "topic.2.4.idempotency-keys-end-to-end-dedupli",
        "title": "Idempotency keys end to end; deduplication windows",
        "status": "unseen"
      },
      {
        "id": "topic.2.4.distributed-locks",
        "title": "Distributed locks",
        "status": "unseen"
      },
      {
        "id": "topic.2.4.leader-election-and-consensus-at-co",
        "title": "Leader election and consensus at concept level",
        "status": "unseen"
      },
      {
        "id": "topic.2.4.time",
        "title": "Time",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.2.5",
    "code": "2.5",
    "title": "24. [2.5] Storage Engines & Choosing the Right Database",
    "order": 24,
    "topics": [
      {
        "id": "topic.2.5.b-tree-vs-lsm-in-practice",
        "title": "B-tree vs LSM in practice",
        "status": "unseen"
      },
      {
        "id": "topic.2.5.row-vs-columnar",
        "title": "Row vs columnar",
        "status": "unseen"
      },
      {
        "id": "topic.2.5.key-value-document-wide-column-rela",
        "title": "Key-value, document, wide-column, relational, graph, time-series, search",
        "status": "unseen"
      },
      {
        "id": "topic.2.5.query-first-modeling-dynamodb-cassa",
        "title": "Query-first modeling (DynamoDB/Cassandra) vs entity-first modeling (relational)",
        "status": "unseen"
      },
      {
        "id": "topic.2.5.polyglot-persistence",
        "title": "Polyglot persistence",
        "status": "unseen"
      },
      {
        "id": "topic.2.5.blob-object-storage",
        "title": "Blob/object storage",
        "status": "unseen"
      },
      {
        "id": "topic.2.5.choosing-by-consistency-need-query-",
        "title": "Choosing by consistency need, query shapes, scale, ops cost, team skill",
        "status": "unseen"
      },
      {
        "id": "topic.2.5.schema-evolution-at-scale",
        "title": "Schema evolution at scale",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.2.6",
    "code": "2.6",
    "title": "25. [2.6] Caching at Scale & CDNs",
    "order": 25,
    "topics": [
      {
        "id": "topic.2.6.distributed-cache-topology",
        "title": "Distributed cache topology",
        "status": "unseen"
      },
      {
        "id": "topic.2.6.hot-keys-big-keys-and-cache-avalanc",
        "title": "Hot keys, big keys and cache avalanche (mass expiry)",
        "status": "unseen"
      },
      {
        "id": "topic.2.6.multi-layer-caching",
        "title": "Multi-layer caching",
        "status": "unseen"
      },
      {
        "id": "topic.2.6.write-patterns-at-scale",
        "title": "Write patterns at scale",
        "status": "unseen"
      },
      {
        "id": "topic.2.6.redis-structures-as-design-tools",
        "title": "Redis structures as design tools",
        "status": "unseen"
      },
      {
        "id": "topic.2.6.cache-db-consistency",
        "title": "Cache/DB consistency",
        "status": "unseen"
      },
      {
        "id": "topic.2.6.cdn",
        "title": "CDN",
        "status": "unseen"
      },
      {
        "id": "topic.2.6.capacity-planning",
        "title": "Capacity planning",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.2.7",
    "code": "2.7",
    "title": "26. [2.7] Messaging, Streaming & Event-Driven Design",
    "order": 26,
    "topics": [
      {
        "id": "topic.2.7.kafka-model",
        "title": "Kafka model",
        "status": "unseen"
      },
      {
        "id": "topic.2.7.ordering",
        "title": "Ordering",
        "status": "unseen"
      },
      {
        "id": "topic.2.7.delivery-semantics",
        "title": "Delivery semantics",
        "status": "unseen"
      },
      {
        "id": "topic.2.7.consumer-lag-rebalancing-poison-mes",
        "title": "Consumer lag, rebalancing, poison messages, replay",
        "status": "unseen"
      },
      {
        "id": "topic.2.7.event-sourcing",
        "title": "Event sourcing",
        "status": "unseen"
      },
      {
        "id": "topic.2.7.cqrs",
        "title": "CQRS",
        "status": "unseen"
      },
      {
        "id": "topic.2.7.change-data-capture",
        "title": "Change data capture",
        "status": "unseen"
      },
      {
        "id": "topic.2.7.stream-vs-batch-processing-windowin",
        "title": "Stream vs batch processing; windowing and late data at concept level",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.2.8",
    "code": "2.8",
    "title": "27. [2.8] Reliability Patterns & Failure Handling",
    "order": 27,
    "topics": [
      {
        "id": "topic.2.8.timeouts-everywhere",
        "title": "Timeouts everywhere",
        "status": "unseen"
      },
      {
        "id": "topic.2.8.retries",
        "title": "Retries",
        "status": "unseen"
      },
      {
        "id": "topic.2.8.circuit-breaker",
        "title": "Circuit breaker",
        "status": "unseen"
      },
      {
        "id": "topic.2.8.bulkheads",
        "title": "Bulkheads",
        "status": "unseen"
      },
      {
        "id": "topic.2.8.load-shedding-and-rate-limiting",
        "title": "Load shedding and rate limiting",
        "status": "unseen"
      },
      {
        "id": "topic.2.8.backpressure-propagation-vs-unbound",
        "title": "Backpressure propagation vs unbounded queues",
        "status": "unseen"
      },
      {
        "id": "topic.2.8.graceful-degradation",
        "title": "Graceful degradation",
        "status": "unseen"
      },
      {
        "id": "topic.2.8.hedged-requests-and-request-coalesc",
        "title": "Hedged requests and request coalescing; why retries require idempotency",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.2.9",
    "code": "2.9",
    "title": "28. [2.9] Observability, Deployment & Operations",
    "order": 28,
    "topics": [
      {
        "id": "topic.2.9.metrics-logs-traces",
        "title": "Metrics, logs, traces",
        "status": "unseen"
      },
      {
        "id": "topic.2.9.distributed-tracing",
        "title": "Distributed tracing",
        "status": "unseen"
      },
      {
        "id": "topic.2.9.slos-and-error-budgets-as-the-brake",
        "title": "SLOs and error budgets as the brake on release pace",
        "status": "unseen"
      },
      {
        "id": "topic.2.9.alerting-on-symptoms-not-causes-avo",
        "title": "Alerting on symptoms, not causes; avoiding alert fatigue",
        "status": "unseen"
      },
      {
        "id": "topic.2.9.deployment",
        "title": "Deployment",
        "status": "unseen"
      },
      {
        "id": "topic.2.9.zero-downtime-schema-migrations",
        "title": "Zero-downtime schema migrations",
        "status": "unseen"
      },
      {
        "id": "topic.2.9.capacity-planning-load-testing-chao",
        "title": "Capacity planning, load testing, chaos testing (concept)",
        "status": "unseen"
      },
      {
        "id": "topic.2.9.disaster-recovery",
        "title": "Disaster recovery",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.2.10",
    "code": "2.10",
    "title": "29. [2.10] Security & Identity in System Design",
    "order": 29,
    "topics": [
      {
        "id": "topic.2.10.authn-vs-authz",
        "title": "AuthN vs AuthZ",
        "status": "unseen"
      },
      {
        "id": "topic.2.10.oauth2-and-oidc",
        "title": "OAuth2 and OIDC",
        "status": "unseen"
      },
      {
        "id": "topic.2.10.sessions-vs-jwts",
        "title": "Sessions vs JWTs",
        "status": "unseen"
      },
      {
        "id": "topic.2.10.service-to-service-auth",
        "title": "Service-to-service auth",
        "status": "unseen"
      },
      {
        "id": "topic.2.10.encryption-in-transit-and-at-rest-k",
        "title": "Encryption in transit and at rest; key management; secrets handling",
        "status": "unseen"
      },
      {
        "id": "topic.2.10.abuse-defenses",
        "title": "Abuse defenses",
        "status": "unseen"
      },
      {
        "id": "topic.2.10.multi-tenancy-isolation",
        "title": "Multi-tenancy isolation",
        "status": "unseen"
      },
      {
        "id": "topic.2.10.privacy-design-inputs",
        "title": "Privacy design inputs",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.2.11",
    "code": "2.11",
    "title": "30. [2.11] Architecture Styles & Service Boundaries",
    "order": 30,
    "topics": [
      {
        "id": "topic.2.11.monolith-vs-modular-monolith-vs-mic",
        "title": "Monolith vs modular monolith vs microservices",
        "status": "unseen"
      },
      {
        "id": "topic.2.11.service-boundaries-by-data-ownershi",
        "title": "Service boundaries by data ownership and change cadence (Conway's law)",
        "status": "unseen"
      },
      {
        "id": "topic.2.11.api-gateway-bff-service-mesh",
        "title": "API gateway, BFF, service mesh",
        "status": "unseen"
      },
      {
        "id": "topic.2.11.sync-rest-grpc-vs-async-events-betw",
        "title": "Sync (REST/gRPC) vs async (events) between services",
        "status": "unseen"
      },
      {
        "id": "topic.2.11.shared-database-anti-pattern-contra",
        "title": "Shared-database anti-pattern; contract and schema ownership",
        "status": "unseen"
      },
      {
        "id": "topic.2.11.serverless",
        "title": "Serverless",
        "status": "unseen"
      },
      {
        "id": "topic.2.11.the-distributed-monolith-smell",
        "title": "The distributed-monolith smell",
        "status": "unseen"
      },
      {
        "id": "topic.2.11.evolution-paths",
        "title": "Evolution paths",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.2.12",
    "code": "2.12",
    "title": "31. [2.12] Specialized Building Blocks: Search, Geo, Media & Probabilistic Structures",
    "order": 31,
    "topics": [
      {
        "id": "topic.2.12.inverted-index-tokenization-ranking",
        "title": "Inverted index, tokenization, ranking basics (TF-IDF/BM25), indexing-pipeline lag",
        "status": "unseen"
      },
      {
        "id": "topic.2.12.geospatial",
        "title": "Geospatial",
        "status": "unseen"
      },
      {
        "id": "topic.2.12.blob-storage-chunked-and-resumable-",
        "title": "Blob storage, chunked and resumable uploads, deduplication, content addressing",
        "status": "unseen"
      },
      {
        "id": "topic.2.12.video",
        "title": "Video",
        "status": "unseen"
      },
      {
        "id": "topic.2.12.bloom-filter-hyperloglog-count-min-",
        "title": "Bloom filter, HyperLogLog, Count-Min Sketch",
        "status": "unseen"
      },
      {
        "id": "topic.2.12.time-series-storage",
        "title": "Time-series storage",
        "status": "unseen"
      },
      {
        "id": "topic.2.12.batch-processing-basics",
        "title": "Batch processing basics",
        "status": "unseen"
      },
      {
        "id": "topic.2.12.unique-id-generation",
        "title": "Unique ID generation",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.2.13",
    "code": "2.13",
    "title": "32. [2.13] Real-Time Systems: Fan-out, Presence & Delivery",
    "order": 32,
    "topics": [
      {
        "id": "topic.2.13.websocket-gateway",
        "title": "WebSocket gateway",
        "status": "unseen"
      },
      {
        "id": "topic.2.13.pub-sub-backbone-between-gateways-r",
        "title": "Pub/sub backbone between gateways (Redis pub/sub, Kafka, NATS)",
        "status": "unseen"
      },
      {
        "id": "topic.2.13.fan-out-on-write-vs-on-read-vs-hybr",
        "title": "Fan-out on write vs on read vs hybrid",
        "status": "unseen"
      },
      {
        "id": "topic.2.13.presence-and-typing-indicators",
        "title": "Presence and typing indicators",
        "status": "unseen"
      },
      {
        "id": "topic.2.13.delivery-guarantees",
        "title": "Delivery guarantees",
        "status": "unseen"
      },
      {
        "id": "topic.2.13.push-notification-path",
        "title": "Push notification path",
        "status": "unseen"
      },
      {
        "id": "topic.2.13.reconnection-storms-and-thundering-",
        "title": "Reconnection storms and thundering herds after an outage",
        "status": "unseen"
      },
      {
        "id": "topic.2.13.per-connection-rate-limits-and-quot",
        "title": "Per-connection rate limits and quotas",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.2.14",
    "code": "2.14",
    "title": "33. [2.14] HLD Case Studies I: Foundations (URL Shortener, Pastebin, ID Generator, Distributed Rate Limiter, KV Store)",
    "order": 33,
    "topics": [
      {
        "id": "topic.2.14.url-shortener",
        "title": "URL shortener",
        "status": "unseen"
      },
      {
        "id": "topic.2.14.pastebin",
        "title": "Pastebin",
        "status": "unseen"
      },
      {
        "id": "topic.2.14.distributed-unique-id-generator",
        "title": "Distributed unique ID generator",
        "status": "unseen"
      },
      {
        "id": "topic.2.14.distributed-rate-limiter",
        "title": "Distributed rate limiter",
        "status": "unseen"
      },
      {
        "id": "topic.2.14.distributed-kv-store",
        "title": "Distributed KV store",
        "status": "unseen"
      },
      {
        "id": "topic.2.14.the-reusable-pattern-requirements-a",
        "title": "The reusable pattern: requirements, API, data, scaling, failure modes",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.2.15",
    "code": "2.15",
    "title": "34. [2.15] HLD Case Studies II: Feeds, Notifications, Chat & Typeahead",
    "order": 34,
    "topics": [
      {
        "id": "topic.2.15.news-feed",
        "title": "News feed",
        "status": "unseen"
      },
      {
        "id": "topic.2.15.notification-service",
        "title": "Notification service",
        "status": "unseen"
      },
      {
        "id": "topic.2.15.chat-1-1-and-group",
        "title": "Chat (1:1 and group)",
        "status": "unseen"
      },
      {
        "id": "topic.2.15.typeahead",
        "title": "Typeahead",
        "status": "unseen"
      },
      {
        "id": "topic.2.15.social-graph-storage",
        "title": "Social graph storage",
        "status": "unseen"
      },
      {
        "id": "topic.2.15.metrics-that-matter",
        "title": "Metrics that matter",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.2.16",
    "code": "2.16",
    "title": "35. [2.16] HLD Case Studies III: Media & Sync (Video, File Sync, Crawler, Search)",
    "order": 35,
    "topics": [
      {
        "id": "topic.2.16.video-platform",
        "title": "Video platform",
        "status": "unseen"
      },
      {
        "id": "topic.2.16.file-sync",
        "title": "File sync",
        "status": "unseen"
      },
      {
        "id": "topic.2.16.web-crawler",
        "title": "Web crawler",
        "status": "unseen"
      },
      {
        "id": "topic.2.16.search-engine",
        "title": "Search engine",
        "status": "unseen"
      },
      {
        "id": "topic.2.16.cost-modeling",
        "title": "Cost modeling",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.2.17",
    "code": "2.17",
    "title": "36. [2.17] HLD Case Studies IV: Marketplace & Money (Ride Matching, Payments, Flash Sales, Schedulers, Metrics)",
    "order": 36,
    "topics": [
      {
        "id": "topic.2.17.ride-matching",
        "title": "Ride matching",
        "status": "unseen"
      },
      {
        "id": "topic.2.17.payments-wallet",
        "title": "Payments/wallet",
        "status": "unseen"
      },
      {
        "id": "topic.2.17.ticketing-flash-sale",
        "title": "Ticketing / flash sale",
        "status": "unseen"
      },
      {
        "id": "topic.2.17.distributed-job-scheduler",
        "title": "Distributed job scheduler",
        "status": "unseen"
      },
      {
        "id": "topic.2.17.metrics-monitoring-system",
        "title": "Metrics/monitoring system",
        "status": "unseen"
      },
      {
        "id": "topic.2.17.reconciliation-as-a-first-class-des",
        "title": "Reconciliation as a first-class design element",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.2.18",
    "code": "2.18",
    "title": "37. [2.18] HLD Interview Execution & Tradeoff Narration",
    "order": 37,
    "topics": [
      {
        "id": "topic.2.18.framework",
        "title": "Framework",
        "status": "unseen"
      },
      {
        "id": "topic.2.18.driving-the-conversation",
        "title": "Driving the conversation",
        "status": "unseen"
      },
      {
        "id": "topic.2.18.choosing-two-deep-dives-and-justify",
        "title": "Choosing two deep dives and justifying them",
        "status": "unseen"
      },
      {
        "id": "topic.2.18.tradeoff-language",
        "title": "Tradeoff language",
        "status": "unseen"
      },
      {
        "id": "topic.2.18.common-pitfalls",
        "title": "Common pitfalls",
        "status": "unseen"
      },
      {
        "id": "topic.2.18.evolving-a-design-when-requirements",
        "title": "Evolving a design when requirements change mid-session",
        "status": "unseen"
      },
      {
        "id": "topic.2.18.time-budgeting-for-45-and-60-minute",
        "title": "Time budgeting for 45- and 60-minute sessions",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.3.1",
    "code": "3.1",
    "title": "38. [3.1] Mobile Framing: Constraints & Client/Server Responsibility",
    "order": 38,
    "topics": [
      {
        "id": "topic.3.1.constraint-set",
        "title": "Constraint set",
        "status": "unseen"
      },
      {
        "id": "topic.3.1.what-belongs-on-the-client-vs-the-s",
        "title": "What belongs on the client vs the server",
        "status": "unseen"
      },
      {
        "id": "topic.3.1.answer-structure",
        "title": "Answer structure",
        "status": "unseen"
      },
      {
        "id": "topic.3.1.lifecycle-as-a-design-input",
        "title": "Lifecycle as a design input",
        "status": "unseen"
      },
      {
        "id": "topic.3.1.network-unreliable-by-default",
        "title": "Network unreliable by default",
        "status": "unseen"
      },
      {
        "id": "topic.3.1.backward-compatibility",
        "title": "Backward compatibility",
        "status": "unseen"
      },
      {
        "id": "topic.3.1.device-os-fragmentation-and-capabil",
        "title": "Device/OS fragmentation and capability tiers",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.3.2",
    "code": "3.2",
    "title": "39. [3.2] Offline-First & Local Data Design",
    "order": 39,
    "topics": [
      {
        "id": "topic.3.2.local-db-as-single-source-of-truth-",
        "title": "Local DB as single source of truth; the network is a sync mechanism",
        "status": "unseen"
      },
      {
        "id": "topic.3.2.schema-for-sync",
        "title": "Schema for sync",
        "status": "unseen"
      },
      {
        "id": "topic.3.2.read-path",
        "title": "Read path",
        "status": "unseen"
      },
      {
        "id": "topic.3.2.write-path",
        "title": "Write path",
        "status": "unseen"
      },
      {
        "id": "topic.3.2.workmanager-as-the-sync-engine",
        "title": "WorkManager as the sync engine",
        "status": "unseen"
      },
      {
        "id": "topic.3.2.local-migrations-and-data-lifecycle",
        "title": "Local migrations and data lifecycle",
        "status": "unseen"
      },
      {
        "id": "topic.3.2.web-parallel-indexeddb-plus-service",
        "title": "Web parallel: IndexedDB plus service worker as offline-first",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.3.3",
    "code": "3.3",
    "title": "40. [3.3] Sync Protocols & Conflict Resolution",
    "order": 40,
    "topics": [
      {
        "id": "topic.3.3.sync-strategies",
        "title": "Sync strategies",
        "status": "unseen"
      },
      {
        "id": "topic.3.3.tombstones-and-deletion-propagation",
        "title": "Tombstones and deletion propagation; garbage-collecting tombstones",
        "status": "unseen"
      },
      {
        "id": "topic.3.3.conflict-types",
        "title": "Conflict types",
        "status": "unseen"
      },
      {
        "id": "topic.3.3.resolution",
        "title": "Resolution",
        "status": "unseen"
      },
      {
        "id": "topic.3.3.version-vectors-crdts-and-operation",
        "title": "Version vectors, CRDTs and operational transform at concept level",
        "status": "unseen"
      },
      {
        "id": "topic.3.3.optimistic-ui-with-rollback-reconci",
        "title": "Optimistic UI with rollback; reconciliation when the server responds",
        "status": "unseen"
      },
      {
        "id": "topic.3.3.idempotent-client-requests-retry-qu",
        "title": "Idempotent client requests; retry-queue ordering and dependencies between queued ops",
        "status": "unseen"
      },
      {
        "id": "topic.3.3.partial-failure-of-batched-sync",
        "title": "Partial failure of batched sync",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.3.4",
    "code": "3.4",
    "title": "41. [3.4] Mobile Networking Layer Design",
    "order": 41,
    "topics": [
      {
        "id": "topic.3.4.api-shape-for-mobile",
        "title": "API shape for mobile",
        "status": "unseen"
      },
      {
        "id": "topic.3.4.http-caching-on-device",
        "title": "HTTP caching on device",
        "status": "unseen"
      },
      {
        "id": "topic.3.4.retry-policy",
        "title": "Retry policy",
        "status": "unseen"
      },
      {
        "id": "topic.3.4.auth",
        "title": "Auth",
        "status": "unseen"
      },
      {
        "id": "topic.3.4.connection-behavior",
        "title": "Connection behavior",
        "status": "unseen"
      },
      {
        "id": "topic.3.4.payload",
        "title": "Payload",
        "status": "unseen"
      },
      {
        "id": "topic.3.4.security",
        "title": "Security",
        "status": "unseen"
      },
      {
        "id": "topic.3.4.network-state-handling",
        "title": "Network-state handling",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.3.5",
    "code": "3.5",
    "title": "42. [3.5] Pagination, Feeds & List Performance",
    "order": 42,
    "topics": [
      {
        "id": "topic.3.5.cursor-keyset-pagination-as-a-contr",
        "title": "Cursor/keyset pagination as a contract; stable ordering; inserts and deletes while scrolling",
        "status": "unseen"
      },
      {
        "id": "topic.3.5.paging-3",
        "title": "Paging 3",
        "status": "unseen"
      },
      {
        "id": "topic.3.5.single-source-of-truth-paging",
        "title": "Single-source-of-truth paging",
        "status": "unseen"
      },
      {
        "id": "topic.3.5.prefetch-distance-and-page-size-tra",
        "title": "Prefetch distance and page-size tradeoffs; memory limits",
        "status": "unseen"
      },
      {
        "id": "topic.3.5.feed-freshness",
        "title": "Feed freshness",
        "status": "unseen"
      },
      {
        "id": "topic.3.5.ranking-on-server-vs-client-impress",
        "title": "Ranking on server vs client; impression logging",
        "status": "unseen"
      },
      {
        "id": "topic.3.5.list-rendering",
        "title": "List rendering",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.3.6",
    "code": "3.6",
    "title": "43. [3.6] Media Loading, Caching & Upload",
    "order": 43,
    "topics": [
      {
        "id": "topic.3.6.image-pipeline",
        "title": "Image pipeline",
        "status": "unseen"
      },
      {
        "id": "topic.3.6.image-url-design",
        "title": "Image URL design",
        "status": "unseen"
      },
      {
        "id": "topic.3.6.prefetching-and-cancellation-while-",
        "title": "Prefetching and cancellation while scrolling fast",
        "status": "unseen"
      },
      {
        "id": "topic.3.6.video-playback",
        "title": "Video playback",
        "status": "unseen"
      },
      {
        "id": "topic.3.6.upload",
        "title": "Upload",
        "status": "unseen"
      },
      {
        "id": "topic.3.6.permissions-and-scoped-storage-impl",
        "title": "Permissions and scoped-storage implications",
        "status": "unseen"
      },
      {
        "id": "topic.3.6.data-and-battery-cost-awareness",
        "title": "Data and battery cost awareness",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.3.7",
    "code": "3.7",
    "title": "44. [3.7] Real-Time & Push on Mobile",
    "order": 44,
    "topics": [
      {
        "id": "topic.3.7.fcm",
        "title": "FCM",
        "status": "unseen"
      },
      {
        "id": "topic.3.7.push-as-a-hint-to-sync-not-the-payl",
        "title": "Push as a hint to sync, not the payload of record",
        "status": "unseen"
      },
      {
        "id": "topic.3.7.websocket-on-mobile",
        "title": "WebSocket on mobile",
        "status": "unseen"
      },
      {
        "id": "topic.3.7.ordering-dedupe-acks-resume-from-la",
        "title": "Ordering, dedupe, acks, resume from last-seen cursor",
        "status": "unseen"
      },
      {
        "id": "topic.3.7.battery",
        "title": "Battery",
        "status": "unseen"
      },
      {
        "id": "topic.3.7.notification-ux",
        "title": "Notification UX",
        "status": "unseen"
      },
      {
        "id": "topic.3.7.token-lifecycle",
        "title": "Token lifecycle",
        "status": "unseen"
      },
      {
        "id": "topic.3.7.foreground-service-limits-and-justi",
        "title": "Foreground-service limits and justified use",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.3.8",
    "code": "3.8",
    "title": "45. [3.8] Mobile Case Studies I: Chat, Social Feed, Offline Notes",
    "order": 45,
    "topics": [
      {
        "id": "topic.3.8.chat-client",
        "title": "Chat client",
        "status": "unseen"
      },
      {
        "id": "topic.3.8.social-feed",
        "title": "Social feed",
        "status": "unseen"
      },
      {
        "id": "topic.3.8.notes-app",
        "title": "Notes app",
        "status": "unseen"
      },
      {
        "id": "topic.3.8.shared-structure",
        "title": "Shared structure",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.3.9",
    "code": "3.9",
    "title": "46. [3.9] Mobile Case Studies II: Uploads, Video, Maps, Payments, Tracking",
    "order": 46,
    "topics": [
      {
        "id": "topic.3.9.photo-video-upload",
        "title": "Photo/video upload",
        "status": "unseen"
      },
      {
        "id": "topic.3.9.video-player-feed",
        "title": "Video player/feed",
        "status": "unseen"
      },
      {
        "id": "topic.3.9.maps-and-location-tracking",
        "title": "Maps and location tracking",
        "status": "unseen"
      },
      {
        "id": "topic.3.9.payments-wallet-client",
        "title": "Payments/wallet client",
        "status": "unseen"
      },
      {
        "id": "topic.3.9.ride-delivery-tracking",
        "title": "Ride/delivery tracking",
        "status": "unseen"
      },
      {
        "id": "topic.3.9.security-and-privacy-as-design-inpu",
        "title": "Security and privacy as design inputs",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.3.10",
    "code": "3.10",
    "title": "47. [3.10] Client Observability, Release Engineering & Scale",
    "order": 47,
    "topics": [
      {
        "id": "topic.3.10.crash-and-anr-reporting-symbolicati",
        "title": "Crash and ANR reporting, symbolication, release health",
        "status": "unseen"
      },
      {
        "id": "topic.3.10.analytics",
        "title": "Analytics",
        "status": "unseen"
      },
      {
        "id": "topic.3.10.performance",
        "title": "Performance",
        "status": "unseen"
      },
      {
        "id": "topic.3.10.feature-flags-remote-config-kill-sw",
        "title": "Feature flags, remote config, kill switches, A/B tests, staged rollout, forced upgrade",
        "status": "unseen"
      },
      {
        "id": "topic.3.10.api-version-compatibility-strategy-",
        "title": "API/version compatibility strategy across app versions",
        "status": "unseen"
      },
      {
        "id": "topic.3.10.modularization-for-build-and-team-s",
        "title": "Modularization for build and team scale",
        "status": "unseen"
      },
      {
        "id": "topic.3.10.testing-strategy-at-scale",
        "title": "Testing strategy at scale",
        "status": "unseen"
      },
      {
        "id": "topic.3.10.incident-response-from-the-client-s",
        "title": "Incident response from the client side",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.3.11",
    "code": "3.11",
    "title": "48. [3.11] Mobile Design Execution & Framing",
    "order": 48,
    "topics": [
      {
        "id": "topic.3.11.structure-for-45-60-minutes",
        "title": "Structure for 45\u201360 minutes",
        "status": "unseen"
      },
      {
        "id": "topic.3.11.calling-out-client-vs-server-decisi",
        "title": "Calling out client-vs-server decisions explicitly",
        "status": "unseen"
      },
      {
        "id": "topic.3.11.offline-and-lifecycle-addressed-in-",
        "title": "Offline and lifecycle addressed in every answer",
        "status": "unseen"
      },
      {
        "id": "topic.3.11.tradeoff-narration-with-concrete-mo",
        "title": "Tradeoff narration with concrete mobile costs",
        "status": "unseen"
      },
      {
        "id": "topic.3.11.common-weak-answers",
        "title": "Common weak answers",
        "status": "unseen"
      },
      {
        "id": "topic.3.11.whiteboard-artifacts",
        "title": "Whiteboard artifacts",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.4.1",
    "code": "4.1",
    "title": "49. [4.1] Tradeoff Articulation, ADRs & Design Reviews at Work",
    "order": 49,
    "topics": [
      {
        "id": "topic.4.1.decision-records",
        "title": "Decision records",
        "status": "unseen"
      },
      {
        "id": "topic.4.1.naming-constraints-and-non-goals-up",
        "title": "Naming constraints and non-goals up front",
        "status": "unseen"
      },
      {
        "id": "topic.4.1.quantifying-tradeoffs",
        "title": "Quantifying tradeoffs",
        "status": "unseen"
      },
      {
        "id": "topic.4.1.reversible-vs-irreversible-decision",
        "title": "Reversible vs irreversible decisions (two-way vs one-way doors)",
        "status": "unseen"
      },
      {
        "id": "topic.4.1.reviewing-other-people-s-designs",
        "title": "Reviewing other people's designs",
        "status": "unseen"
      },
      {
        "id": "topic.4.1.presenting-to-different-audiences",
        "title": "Presenting to different audiences",
        "status": "unseen"
      },
      {
        "id": "topic.4.1.avoiding-resume-driven-design-the-s",
        "title": "Avoiding resume-driven design; the simplest thing that works, plus the trigger to evolve",
        "status": "unseen"
      }
    ]
  },
  {
    "id": "cluster.4.2",
    "code": "4.2",
    "title": "50. [4.2] Practice Loop, Spaced Review & Gap Tracking",
    "order": 50,
    "topics": [
      {
        "id": "topic.4.2.weekly-cadence",
        "title": "Weekly cadence",
        "status": "unseen"
      },
      {
        "id": "topic.4.2.divergence-log",
        "title": "Divergence log",
        "status": "unseen"
      },
      {
        "id": "topic.4.2.spaced-re-design",
        "title": "Spaced re-design",
        "status": "unseen"
      },
      {
        "id": "topic.4.2.teach-back",
        "title": "Teach-back",
        "status": "unseen"
      },
      {
        "id": "topic.4.2.reading-real-postmortems-and-engine",
        "title": "Reading real postmortems and engineering blogs; extract the design lesson",
        "status": "unseen"
      },
      {
        "id": "topic.4.2.gap-triage",
        "title": "Gap triage",
        "status": "unseen"
      }
    ]
  }
];