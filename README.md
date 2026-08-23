<div align="center">

<picture><source media="(prefers-color-scheme: dark)" srcset="./assets/banner-dark.svg"><img src="./assets/banner-light.svg" alt="A quiet moonscape: a small robot with a telescope watches a constellation shaped like a rising chart draw itself across the sky, with a star for each of Rust, Python, Go, TypeScript, SQL, PostgreSQL, GraphQL, Docker, Kafka, Redpanda, Ansible, Kubernetes, Proxmox and Solidity, and the caption reads: star chart, not price chart"></picture>

# Samuel Metcalfe

**Software engineer: reliable distributed systems, payments infrastructure and blockchain protocols**

Open to remote software engineering roles. Reach me by email: `contact[at]samuelmetcalfe[dot]com`.

</div>

I'm a software engineer who has specialised in backend infrastructure for blockchain protocols. Most of my recent public work has been building Direct Indexing Payments (DIPs) for The Graph, a network of independent operators, called indexers, who run the servers that index on-chain data and serve billions of API queries per year.

DIPs is a recurring per-second fee that pays indexers to keep particular datasets, called subgraphs, indexed and ready to answer queries. One service, `dipper`, makes and prices the offers, the indexer's own service receives, verifies and accepts these offers, and a shared view of the on-chain record keeps both sides in step. I worked on all 3 components, and separately built the rewards eligibility oracle that decides which indexers earn The Graph's indexing rewards. All of the code is public and linked below.

---

## Selected work

### Paying side: [dipper](https://github.com/edgeandnode/dipper) (Rust)

I took over development of dipper after the original contributors moved to a new project. Between December 2025 and August 2026 I was effectively dipper's only engineer, writing 113 of the 119 human-authored changes merged in that window (the rest of its history is automated dependency updates). dipper offers indexing agreements to indexers and manages each offer from proposal through settlement and withdrawal. I designed and built the on-chain side of that lifecycle: the state machine, the chain listener that follows acceptances and cancellations, and the services that keep a subgraph served when an indexer never answers, rejects an offer, or quietly stops indexing. I moved dipper from off-chain signed payment vouchers to on-chain escrow-backed payments, coordinating the change across 4 repositories. [Merged changes](https://github.com/edgeandnode/dipper/pulls?q=is%3Apr+author%3AMoonBoi9001+is%3Amerged).

### Who gets paid: [subgraph-dips-indexer-selection](https://github.com/edgeandnode/subgraph-dips-indexer-selection) (Python)

This service picks which indexers are offered indexing agreements. I initially prototyped the algorithmic scoring model as a Jupyter notebook, then created this repository and moved the algorithm into an always-on HTTP API on Kubernetes. The repo runs a heavy daily data pipeline job that replays about 1.7 billion gateway query records from a Redpanda topic. I designed the indexer selection behaviour this repository runs: taking into account indexer service price and service quality, and ensured that the algorithm has a preference for indexers that are already synced, so consumers have access to query their data faster. [Merged changes](https://github.com/edgeandnode/subgraph-dips-indexer-selection/pulls?q=is%3Apr+author%3AMoonBoi9001+is%3Amerged).

### Receiving side: [indexer-rs](https://github.com/graphprotocol/indexer-rs) (Rust)

In January 2026 I took over the DIPs code in indexer-rs. This is the service indexers run to receive, verify and answer indexing agreement proposals over gRPC. I wrote 25 of the 26 merged changes made to it between January and August 2026; the rest of the repository is other people's work. I rebuilt its trust model: it now works out who signed each proposal from the signature itself and accepts it only if that signer is in the protocol's on-chain list of approved payers, instead of trusting a sender field anyone could fill in. I also designed the gRPC replies with specific rejection reasons that dipper knows how to handle. [The trust-model change](https://github.com/graphprotocol/indexer-rs/pull/1048) is a good 60-second read; [all merged changes](https://github.com/graphprotocol/indexer-rs/pulls?q=is%3Apr+author%3AMoonBoi9001+is%3Amerged).

### Accepting side: [indexer](https://github.com/graphprotocol/indexer) (TypeScript)

I moved on-chain acceptance onto its own parallel loop, so agreements stopped expiring unaccepted under a backlog. I then fixed 3 ways the agent quietly cost indexers money: it dropped the final payment when the payer cancelled first, it left allocations indexing unpaid, and it let a live agreement be destroyed by closing a stale allocation. [Merged changes](https://github.com/graphprotocol/indexer/pulls?q=is%3Apr+author%3AMoonBoi9001+is%3Amerged).

### Shared record: [indexing-payments-subgraph](https://github.com/graphprotocol/indexing-payments-subgraph) (AssemblyScript)

I created the shared view of the on-chain record that both sides read: this subgraph indexes agreement and offer events from The Graph's contracts and serves them from a single GraphQL endpoint, so the paying service (dipper) can reconcile and backfill events into its PostgreSQL database without calling the contracts via RPC on every catch-up pass. [Merged changes](https://github.com/graphprotocol/indexing-payments-subgraph/pulls?q=is%3Apr+author%3AMoonBoi9001+is%3Amerged).

### Who earns rewards: [rewards-eligibility-oracle](https://github.com/graphprotocol/rewards-eligibility-oracle) (Python)

This oracle decides which indexers qualify for The Graph's indexing rewards and records the decision into the [RewardsEligibilityOracle contract](https://arbiscan.io/address/0x02753bae61c08abd4351bce7f48524935c2cc78e) on Arbitrum. I built the service and wrote the eligibility criteria it enforces: a rolling 28-day window counting the days an indexer served queries that met published thresholds for response status, latency and data freshness. I then took it to production: RPC failover and gas bounds so the daily submission survives unreliable providers, a circuit breaker so a failing run cannot loop into expensive retries, and Slack and Opsgenie alerting. [Merged changes](https://github.com/graphprotocol/rewards-eligibility-oracle/pulls?q=is%3Apr+author%3AMoonBoi9001+is%3Amerged).

---

<div align="center">
<a href="https://gitroll.io/profile/u4zzWIZNh81XISOBbHHDCgSkU2om2"><picture><source media="(prefers-color-scheme: dark)" srcset="https://gitroll.io/api/badges/profiles/v1/u4zzWIZNh81XISOBbHHDCgSkU2om2?theme=dark"><img src="https://gitroll.io/api/badges/profiles/v1/u4zzWIZNh81XISOBbHHDCgSkU2om2" alt="GitRoll profile card for MoonBoi9001: overall rating and code quality scores" width="440"></picture></a>
</div>
