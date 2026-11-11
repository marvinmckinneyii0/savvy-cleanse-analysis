# Draft Story: Shared Coding Memory for Claude Code and Codex

**Status:** Draft for Marvin's review. Not listed in `sprint-status.yaml`; not approved for implementation.
**Scope:** Developer tooling for Savvy Analytics code repositories, including SAINT/SavvyClean.
**Date:** 2026-10-16

## User outcome

When Marvin starts work in a Savvy Analytics code repository, Claude Code and Codex can retrieve durable, relevant project context from a shared, searchable memory store instead of relying only on one tool's local session history. Repository-specific facts remain reviewable alongside the code.

## Proposed approach

- Keep authoritative implementation instructions and codebase facts in each repository: `AGENTS.md`, architecture docs, decision records, and current-status notes.
- Use a separate private Markdown knowledge vault for cross-repository decisions and shared product context. Evaluate SilverBullet as the open-source Obsidian-style vault.
- Expose only scoped search/read tools to Claude Code and Codex through an MCP bridge. Select and verify the specific bridge, auth model, and client configuration before implementation.
- Keep Claude Code's built-in auto-memory as a personal per-repository aid, not the shared source of truth.
- Start with curated memory updates. Do not capture full transcripts or let an agent silently promote untrusted repository/web content into canonical memory.

## Acceptance criteria

1. The same approved memory notes can be searched from both Claude Code and Codex across at least two repositories.
2. Search results identify the source note and relevant section so an agent can verify the retrieved context.
3. Repository-specific instructions point agents to the shared-memory search workflow without duplicating sensitive cross-project notes in public repositories.
4. Memory is read-only by default. Any write or update requires explicit user direction and preserves reviewable Markdown history.
5. Secrets, API keys, customer data, and raw session transcripts are excluded from the shared vault.
6. If the memory service is unavailable, coding work can continue from repository documentation without silently treating stale or missing memory as authoritative.
7. Setup instructions cover local development on Windows and document how each coding tool connects without committing credentials or machine-specific paths.

## Out of scope

- Changing SAINT runtime behavior, database schemas, authentication, or product APIs.
- Giving an agent autonomous write access to the central vault.
- Replacing the repository's BMAD status/approval gates or its existing project documentation.
- Adding Claude-Mem, Mem0, or another automatic transcript-capture service unless separately approved after a privacy and maintenance review.

## Decisions required before implementation

- Confirm SilverBullet as the central vault, or choose another Markdown vault.
- Choose the supported MCP bridge and verify maintenance, transport, access control, and data flow.
- Decide whether Codex and Claude Code connect locally on Marvin's Windows machine or through a private hosted endpoint.
- Define where the private vault is hosted and how it is backed up.

## Gate

This draft does not change the canonical BMAD ledger. Before implementation, review and approve the architecture and acceptance criteria, then add an appropriately sized story to `sprint-status.yaml` with dependencies and eligibility set by the human project owner.
