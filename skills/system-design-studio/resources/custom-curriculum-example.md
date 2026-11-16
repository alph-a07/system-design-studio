# Tier 1: Hardware Sympathy & Kernel Bypass

## 1. [1.1] Low-Level Mechanics & Hardware Sympathy
- [ ] Memory alignment, cache lines (64-byte), and false sharing — L1/L2/L3 cache coherence — *Tick off when: you can derive cache bouncing cold.*
- [ ] CPU core pinning, thread isolation, and isolcpus — scheduler jitter elimination — *Tick off when: you can explain context switch overhead cold.*
- [ ] Non-Uniform Memory Access (NUMA) topologies and socket affinity — cross-socket latency penalty — *Tick off when: you can calculate NUMA interconnect tax cold.*
- [ ] Linux network stack bypass: DPDK, Solarflare OpenOnload, and io_uring — kernel copy elimination — *Tick off when: you can trace ring buffer polling cold.*
- [ ] Zero-copy circular ring buffers and single-producer single-consumer (SPSC) lockless queues — memory barriers — *Tick off when: you can verify acquire-release semantics cold.*

# Tier 2: Order Matching & Market Data Protocols

## 2. [2.1] Financial Protocols & Serialization
- [ ] FIX protocol vs binary Simple Binary Encoding (SBE) — zero-copy framing — *Tick off when: you can benchmark parsing overhead cold.*
- [ ] ITCH/OUCH market data dissemination and order entry feeds — multicast UDP feeds — *Tick off when: you can handle gap recovery cold.*
- [ ] Deterministic order matching algorithms: price-time priority vs pro-rata — matching engine invariants — *Tick off when: you can trace limit order book updates cold.*
- [ ] Microsecond timestamping: PTP (IEEE 1588) hardware clocks vs NTP — clock drift bounds — *Tick off when: you can explain sub-microsecond skew cold.*
- [ ] Tick-to-trade latency measurement and kernel hardware timestamp tap — packet capture NIC taps — *Tick off when: you can measure gateway-to-wire latency cold.*

# Tier 3: Risk Controls & Crash Resilience

## 3. [3.1] Risk Controls & High Durability
- [ ] Pre-trade sub-microsecond risk checks — credit limits and order throttles — *Tick off when: you can verify check latency bounds cold.*
- [ ] High-durability append-only transaction logging with NVMe kernel-bypass — SPDK write path — *Tick off when: you can trace fsync elimination cold.*
- [ ] Hot-standby active-passive failover with synchronous network replication — zero data loss bounds — *Tick off when: you can explain failover detection time cold.*
- [ ] Unwinding inventory risk and exchange disconnect recovery states — state machine reconciliation — *Tick off when: you can trace disconnect recovery cold.*
