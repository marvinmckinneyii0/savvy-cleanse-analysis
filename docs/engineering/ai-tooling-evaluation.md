# AI coding assistant tooling evaluation (2026-10-16)

Status: **candidate integrations only; not installed or approved for runtime use**.

## Scope
Evaluate the five repositories shared by Nick Saraev for SAINT/SavvyClean development. This is developer tooling, not customer-facing SAINT functionality.

| Candidate | Upstream | Intended role | Decision |
|---|---|---|---|
| Agent Skills | https://github.com/addyosmani/agent-skills | Reusable coding/review instructions | Evaluate first; adopt selected, pinned skills only |
| Context7 | https://github.com/upstash/context7 | Version-aware library documentation for coding agents | Pilot read-only, with explicit network/data boundaries |
| Graphify | https://github.com/Graphify-Labs/graphify | Codebase knowledge graph and repository comprehension | Evaluate offline on a limited code subset |
| Magic MCP | https://github.com/21st-dev/magic-mcp | UI component generation for React frontend | Optional frontend-only experiment |
| Strix | https://github.com/usestrix/strix | Security assessment assistance | Evaluate only in isolated, authorized staging environment |

All upstream capabilities, licenses, maintenance, security and compatibility require verification before installation. No external scripts should be executed directly from unpinned remote URLs.

## Project structure (proposed)
- `docs/engineering/ai-tooling-evaluation.md`: this inventory and adoption gates.
- `docs/engineering/ai-tooling-assessment/`: one assessment per approved candidate.
- `agent-system/skills/`: vetted, vendored and pinned agent skills only.
- `agent-system/mcp/`: reviewed MCP configurations with no embedded credentials.
- `docs/security/`: scoped security findings, redacted logs, remediation decisions.

## Implementation sequence
1. Inventory existing Claude/Codex instructions, MCP configs, memory, CI and current story status. Avoid duplicating existing components.
2. Evaluate Agent Skills and Context7 in a throwaway branch; record licenses, commit pins, tool permissions, data egress and rollback.
3. Benchmark Graphify against the existing repository-context workflow, checking indexing quality, secrets exposure, CPU/storage cost and freshness.
4. Try Magic MCP only on an isolated UI component; require accessibility, dependency and design-system review.
5. Assess Strix only with explicit authorization, test accounts and an isolated staging target. No production scans or destructive tests.
6. Add reproducible smoke tests and document configuration only after each candidate passes its review.

## Acceptance and security gates
- Existing SAINT cleaning semantics, story contracts, and production behavior remain unchanged.
- Never commit tokens, .env files, private customer data, or unredacted agent traces.
- MCP integrations default to least privilege; prohibit unapproved writes, shell execution, external uploads and production access.
- Pin versions/commits; review license, dependency vulnerabilities, supply-chain provenance and maintenance.
- Benchmark against baseline for accuracy, latency, cost, token usage, privacy and reproducibility.
- Each tool has an owner, opt-in activation, documented rollback and explicit human approval.
- No automatic story eligibility changes, branch merges or production deployment.
- Respect `AGENTS.md` and canonical sprint-status/story dependencies. This document does not authorize the autonomous loop to execute new work.

## Proposed backlog
- TOOL-01 Inventory current context/memory/skills/MCP setup (research only).
- TOOL-02 Agent Skills pilot (approval required).
- TOOL-03 Context7 read-only pilot (approval required).
- TOOL-04 Graphify benchmark (approval required).
- TOOL-05 Magic MCP UI spike (approval required).
- TOOL-06 Strix staging-only security assessment (approval required).

Maker School mentioned in the screenshot is a training offering, not a repository integration; consider separately for learning/business development.
