# Malicious-IOC Auto-Block — TOR / Malicious IP Feed Ingestion for Perimeter Firewall

![Status](https://img.shields.io/badge/status-proposal%2FPoC-blue)
![Category](https://img.shields.io/badge/category-SOC%20%7C%20Threat%20Intel-orange)
![License](https://img.shields.io/badge/license-Idea%20Doc%20Only-lightgrey)

**Author / Idea Owner:** Amit Ambekar
**Status:** Proposal / Proof-of-Concept
**Category:** SOC — Threat Intelligence, Network Defense, Firewall Automation

---

## 1. Overview

This project proposes an automated pipeline that ingests publicly available **Tor exit-node** and **malicious IP / IOC feeds**, and pushes them into our **SOC-controlled perimeter firewall** as a dynamic block/deny list.

The core idea: any inbound or outbound traffic that hits the firewall is checked against these live threat feeds. If a source/destination IP matches a known Tor exit node, proxy, spam bot, or abuse-reported IP, the firewall automatically **blocks/denies** the connection before it reaches internal systems — reducing manual SOC triage effort and closing the window of exposure.

Once validated, we can evaluate feeding the same matched-traffic logs into **ELK (via Logstash)** for visibility, alerting, and long-term trend analysis — pending internal review of licensing, data volume, and infra impact.

---

## 2. Problem Statement

- Malicious actors frequently route attack traffic through Tor exit nodes, open proxies, and known-abusive IP ranges to mask origin.
- Today this traffic is caught reactively (post-incident) rather than proactively at the perimeter.
- We currently have no automated, continuously-refreshed IOC feed integrated into the firewall.

## 3. Goal

Build a lightweight, scheduled fetcher that:
1. Pulls IOC/IP lists from trusted, free threat-intel sources.
2. Normalizes/dedupes them.
3. Publishes them as firewall-consumable objects (address groups / dynamic lists).
4. Refreshes on a safe interval that respects each source's rate limits.
5. (Phase 2, pending internal review) Ships match/deny logs to ELK via Logstash for dashboards & alerting.

---

## 4. Data Sources

### 4.1 Tor Exit Nodes

| Source | URL | Notes |
|---|---|---|
| Official Tor Project | https://check.torproject.org/exit-addresses | Only direct/official Tor exit list we've identified so far. Need to explore more direct sources. |
| dan.me.uk Tor Node List (All + Exit) | https://www.dan.me.uk/tornodes | Full node + exit node list. |
| dan.me.uk raw list (exit only) | https://www.dan.me.uk/torlist/?exit | **Rate-limited — see constraint below.** |
| dan.me.uk raw list (full) | https://www.dan.me.uk/torlist/?full | **Rate-limited — see constraint below.** |

**Important constraint (dan.me.uk):** Their data is updated only every 30 minutes, and repeated/aggressive polling results in a **minimum 30-minute IP suspension**, with permanent blocking risk for repeat offenders. Per their own notice:

> "You can only fetch the data every 30 minutes... If you keep trying to download this list too often, you may get blocked from accessing it completely."

**Decision:** We will **not** poll dan.me.uk directly at high frequency. Minimum fetch interval must be **≥120 minutes** to stay well under their limit and avoid suspension. This needs to be enforced at the scheduler/cron level.

### 4.2 FireHOL IP Lists (Primary recommended source)

GitHub project (updates roughly every 5–10 hours): https://github.com/firehol/blocklist-ipsets
Landing page: https://iplists.firehol.org/

Suggested lists to ingest initially:

1. `abuseipdb_30d.ipset` — https://github.com/firehol/blocklist-ipsets/blob/master/abuseipdb_30d.ipset
2. `botscout_30d.ipset` — https://github.com/firehol/blocklist-ipsets/blob/master/botscout_30d.ipset
3. `cleantalk_30d.ipset` — https://github.com/firehol/blocklist-ipsets/blob/master/cleantalk_30d.ipset
4. `cleantalk_new_30d.ipset` — https://github.com/firehol/blocklist-ipsets/blob/master/cleantalk_new_30d.ipset
5. `dshield_30d.netset` — https://github.com/firehol/blocklist-ipsets/blob/master/dshield_30d.netset
6. `firehol_abusers_30d.netset` — https://github.com/firehol/blocklist-ipsets/blob/master/firehol_abusers_30d.netset
7. `sslproxies_30d.ipset` — https://github.com/firehol/blocklist-ipsets/blob/master/sslproxies_30d.ipset
8. `stopforumspam_30d.ipset` — https://github.com/firehol/blocklist-ipsets/blob/master/stopforumspam_30d.ipset
9. `socks_proxy_30d.ipset` — https://github.com/firehol/blocklist-ipsets/blob/master/socks_proxy_30d.ipset
10. `tor_exits_30d.ipset` — https://github.com/firehol/blocklist-ipsets/blob/master/tor_exits_30d.ipset

### 4.3 AbuseIPDB Community Blocklist (via borestad mirror)

GitHub: https://github.com/borestad/blocklist-abuseipdb/tree/main
Recommended raw list: https://raw.githubusercontent.com/borestad/blocklist-abuseipdb/main/abuseipdb-s100-30d.ipv4

**Usage guidance from the maintainers:**
- Use lists with a **30-day or shorter** window to avoid false positives.
- **Do not** use `abuseipdb-s100-all.ipv4` — that one is for statistical use only, not enforcement.
- `s100` = ~100% confidence rating.
- IPv6 coverage/blocking from this list is considered "almost useless" per the maintainers — treat as low priority.
- **All underlying credit belongs to AbuseIPDB** (https://www.abuseipdb.com/) — this repo is a curated mirror/derivative.

---

## 5. Refresh Interval Strategy

| Source | Minimum Safe Interval | Reason |
|---|---|---|
| dan.me.uk (`?exit`, `?full`) | 120 minutes (their data itself refreshes every 30 min, but we buffer 4x for safety) | Aggressive polling → temporary/permanent IP suspension |
| check.torproject.org/exit-addresses | 60 minutes (proposed — to validate) | No documented hard limit found; be conservative regardless |
| FireHOL ipsets (GitHub) | 60 minutes (source itself updates every 5–10 hrs) | GitHub raw file limits; no benefit polling faster than source updates |
| AbuseIPDB (borestad mirror) | 60 minutes (source updates ~daily) | Same — respect upstream update cadence |

> All intervals are proposed starting points — to be tuned after we observe real match/hit volume during the SOC-controlled pilot (see Section 7).

---

## 6. Proposed Architecture (High Level)

```
[Scheduler / Cron Job]
        │
        ▼
[Fetcher Script] ── pulls & normalizes IOC/IP lists (Tor + FireHOL + AbuseIPDB)
        │
        ▼
[Dedup / Validate / Format] ── convert to firewall-native object format
        │
        ▼
[SOC-Controlled Firewall] ── dynamic address group / deny list, auto-applied
        │
        ▼
  Traffic hits firewall → matched against IOC list
        │
   ┌────┴─────┐
   ▼          ▼
 Match      No Match
   │            │
 DENY/BLOCK   Allow (normal flow)
   │
   ▼
[Logstash] → [ELK] (Phase 2 — pending internal review)
   → Dashboards, alerting, historical trend analysis
```

---

## 7. Phased Rollout Plan

1. **Phase 0 — Pilot (this proposal):** Deploy on a **SOC-controlled/observation firewall only** (not production-wide) to validate feed quality, false-positive rate, and match volume.
2. **Phase 1 — Tuning:** Review pilot data, tune refresh intervals and source selection, drop noisy lists if needed.
3. **Phase 2 — ELK Integration (pending internal check):** Forward matched/denied traffic logs via Logstash into ELK for dashboarding and alerting. Requires confirming ELK capacity/licensing internally before proceeding.
4. **Phase 3 — Production Rollout:** Extend to broader firewall estate once validated.

---

## 8. Infrastructure Note — Firewall Separation

We recommend a **dedicated/separate firewall for SOC operations**, distinct from the firewall handling **client communication traffic** (including traffic destined for Logstash). This separation:
- Prevents SOC threat-intel/testing traffic from impacting client-facing paths.
- Keeps Logstash ingestion traffic isolated and easier to monitor/troubleshoot.
- Reduces blast radius if a feed ever causes an unexpected false-positive block.

---

## 9. Credits / Attribution

- Tor Project — https://www.torproject.org/
- dan.me.uk Tor Node List — https://www.dan.me.uk/tornodes
- FireHOL / blocklist-ipsets — https://github.com/firehol/blocklist-ipsets
- AbuseIPDB (all underlying abuse data credit) — https://www.abuseipdb.com/
- borestad/blocklist-abuseipdb (curation/mirroring) — https://github.com/borestad/blocklist-abuseipdb

## 10. License / Usage Note

This repository only documents the **idea, architecture, and data-source references**. No proprietary firewall configs, credentials, or internal infra details are stored here. Any implementation scripts should respect each upstream source's rate limits and terms of use.

---

*See `CONTRIBUTING.md` for how to propose changes to this idea/document.*
