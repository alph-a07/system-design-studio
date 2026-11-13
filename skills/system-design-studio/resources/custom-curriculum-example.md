# High-Frequency Trading & Low-Latency Systems Curriculum

## Cluster 1: Hardware Sympathy & Kernel Bypass
- [ ] Memory alignment, cache lines (64-byte), and false sharing
- [ ] CPU core pinning, thread isolation, and isolcpus
- [ ] Non-Uniform Memory Access (NUMA) topologies and socket affinity
- [ ] Linux network stack bypass: DPDK, Solarflare OpenOnload, and io_uring
- [ ] Zero-copy circular ring buffers and single-producer single-consumer (SPSC) lockless queues

## Cluster 2: Order Matching & Market Data Protocols
- [ ] FIX (Financial Information eXchange) protocol vs binary Simple Binary Encoding (SBE)
- [ ] ITCH/OUCH market data dissemination and order entry feeds
- [ ] Deterministic order matching algorithms: price-time priority vs pro-rata
- [ ] Microsecond timestamping: PTP (IEEE 1588) hardware clocks vs NTP
- [ ] Tick-to-trade latency measurement and kernel hardware timestamp tap

## Cluster 3: Risk Controls & Crash Resilience
- [ ] Pre-trade sub-microsecond risk checks (credit limits, fat-finger checks, order throttles)
- [ ] High-durability append-only transaction logging with NVMe kernel-bypass
- [ ] Hot-standby active-passive failover with synchronous network replication
- [ ] Unwinding inventory risk and exchange disconnect recovery states
