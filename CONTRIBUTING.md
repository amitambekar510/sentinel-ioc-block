# Contributing

This is a SOC-internal proposal repository. It currently holds a single idea document (`README.md`) describing a plan to auto-block Tor/malicious IPs at the firewall level. These are **suggested** guidelines from the original author (Amit Ambekar) — adjust to match your team's actual workflow before adopting.

## How to Propose Changes

1. **Open an Issue first** for anything non-trivial (new data source, changed refresh interval, architecture change) so it can be discussed before edits are made.
2. **Fork or branch + open a Pull Request** for all changes to `README.md` — no direct pushes to `main`.
3. Keep one logical change per PR (e.g., "add new FireHOL list" separate from "update refresh interval table").

## What to Include When Proposing a New Feed/Source

- Source URL and whether it's official/direct or a community mirror.
- Update frequency of the source (how often *they* refresh data).
- Any documented rate limits or usage restrictions (quote them directly, like we did for dan.me.uk).
- Recommended safe polling interval for us, with reasoning.
- Attribution / credit requirements, if any.

## Review Checklist (before merging a PR)

- [ ] Source is reputable and actively maintained.
- [ ] Rate limits / ToS are documented and respected in the proposed interval.
- [ ] No credentials, internal IPs, firewall rules, or infra-identifying details are added to this repo.
- [ ] Attribution added to the Credits section if a new external source is introduced.
- [ ] At least one other SOC team member has reviewed and approved the PR.

## Reporting Issues with the Idea/Approach

If you spot a flaw in the approach (e.g., a source likely to cause false positives, a better direct feed than what's listed, a safer architecture), please open a GitHub Issue describing:
- What you observed / are concerned about
- Why it matters (false positive risk, legal/ToS risk, ops burden, etc.)
- A suggested alternative, if you have one

## Code of Conduct

Standard professional conduct applies — this is an internal security proposal, keep discussion constructive and focused on technical merit.
