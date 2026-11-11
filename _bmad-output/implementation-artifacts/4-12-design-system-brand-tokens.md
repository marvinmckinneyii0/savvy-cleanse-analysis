# Story 4.12 — SAINT Design System & Brand Tokens (DRAFT)

> **Governance:** Draft specification for owner review; no approved status change.
> Canonical `sprint-status.yaml`: `backlog`, `loop_eligible: false` as of 2026-11-10.
> This file does not authorize Codex/Claude/Work to implement, change status,
> edit agent policy, merge, or deploy. Requires explicit human promotion and
> supervised execution because scope is L and visual/brand judgment is needed.

## Goal

Bring the approved **Black & Amber** SAINT identity into a single accessible
and maintainable frontend design system used consistently by marketing pages,
the eventual customer SaaS, and admin UI.

## Reference and scope

- Visual intent: `docs/design/saint-black-amber.md` (human-approved direction
  from 2026-11-10 SAINT screenshot). The original screenshot is in the owner
  conversation, **not** checked into this repository.
- Existing planned token source: `saint-design-tokens.css` (locate/verify
  actual path first; do not assume a file exists).
- Relevant design epic: `epic-4-web-application.md`, section 4.12.
- New design work must not promise functionality absent from the product.
- Friday 2026-11-13 concierge beta remains the priority; full 4.12 rollout
  is post-beta and is not part of its launch gates.

## Acceptance criteria (to refine and approve before promotion)

1. **Token inventory:** Survey existing CSS/theme/tailwind/component tokens;
   document the source of truth and remove contradictory duplicates only within
   approved scope. Do not drift other product branding.
2. **Color system:** Establish near-black/charcoal surface ramp, restrained
   metallic amber primary/highlight state, accessible neutral typography,
   borders, severity colors, and focus/hover/disabled states. Visual hex samples
   in the reference document are starting points, not falsely exact samples.
3. **Gloss:** Give cards/CTAs a slight controlled sheen/reflective edge, no heavy
   glass blur or neon effects. Verify light/dark contrast and performance.
4. **Core components:** Define header/nav, hero, buttons, cards, data tables,
   inputs, upload states, alerts, empty/loading/error states, report previews
   and responsive navigation using semantic reusable components.
5. **Typography and logo:** Resolve the display font and compact/full wordmark
   with human approval. Never embed unlicensed fonts/assets or a placeholder logo.
6. **Truthful demo:** Replace fabricated SDK, notebook, chart or upload
   demonstrations with accurate current functionality. Concierge CTAs remain
   request-a-report until a self-serve product actually ships.
7. **Accessibility:** Meet WCAG 2.2 AA text contrast targets, visible keyboard
   focus, reduced-motion preference, usable labels and responsive behavior
   at 360px, 768px, 1440px.
8. **Verification:** Capture before/after desktop/mobile screenshots (when a
   screenshot asset is accessible), run `uv run pytest`, `npm test`,
   `npm run build`, and applicable accessibility checks. Log results and
   accepted remaining deltas.
9. **Review boundaries:** Independent review at exact commit SHA. No marketing
   content/pricing/schema/security policy changes outside story scope.
10. **Release:** Only human-approved merge; don't promote `done` before all
    acceptance criteria and the repository's security review requirements pass.

## Non-goals

- Redesign Savvy Analytics corporate site or WARFOX
- Add self-serve upload, authentication, billing or agent features
- Modify the canonical sprint ledger or agent contract autonomously
- Block or destabilize Friday's concierge beta

## Blocking owner checks

- Final sampled brand tokens and confirmed SAINT logo/wordmark asset
- Approved display typeface and font licensing
- Whether to expose a functioning alternate/light theme
- Final screenshot review at desktop and mobile widths

## Proposed bounded implementation approach

After owner approval: inventory → token baseline → shared primitives → page
adoption in small reviewable batches → accessibility/visual regressions →
independent review → draft PR → human merge. Any single automation invocation
must do only one approved canonical story; this spec alone is not a new
automation permission.
