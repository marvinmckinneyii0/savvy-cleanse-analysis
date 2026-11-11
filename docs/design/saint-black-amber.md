# SAINT — Black & Amber Visual Direction

**Approved visual direction:** 2026-11-10, from the owner-supplied SAINT homepage screenshot in the project conversation. This document describes the reference in text so a context-reset development loop can recover the direction. The screenshot binary is not yet committed to the repository; do not claim otherwise.

**Product boundary:** Applies to SAINT (Savvy Analytics Intelligence): marketing site, customer SaaS workspace and admin. It is distinct from the Savvy Analytics corporate website and WARFOX. Style direction is approved; implementing new features or changing pricing is not.

## Design intent
- Premium, technical, restrained, quietly polished. Black navigation and near-black charcoal panels with warm metallic amber highlights.
- A **slight gloss**, not exaggerated glassmorphism: subtle tonal gradients, thin reflective top edges, soft shadows and limited semi-transparent layering.
- Large high-contrast white typography; amber selectively emphasizes important words and primary calls to action.
- Low-noise composition with consistent spacing, rounded dark panels and deliberate hierarchy; avoid neon, glowing outlines, busy particle effects or decorative animation.
- The terminal/report preview should look like a real SAINT workflow, not an invented SDK or feature demo.

## Proposed initial token palette (visual approximations, not pixel-sampled)
| Token | Initial value | Intended use |
|---|---|---|
| `--saint-bg` | `#050505` | Global dark background |
| `--saint-nav` | `#000000` | Navigation |
| `--saint-surface` | `#0D0D0F` | Main panels |
| `--saint-surface-raised` | `#171719` | Raised cards |
| `--saint-accent` | `#B5792E` | Amber brand / primary CTA |
| `--saint-accent-hover` | `#CD8C3B` | Accessible amber hover |
| `--saint-text` | `#F8FAFC` | Primary text |
| `--saint-text-muted` | `#B4BBC6` | Supporting text |
| `--saint-border` | `#34302B` | Subtle separators |

Keep a *single* source of design tokens. Reconcile these proposed values against existing `saint-design-tokens.css` during Epic 4.12; do not create competing token systems. Warm amber and black are the approved direction, while final sampled hex values, typeface and implementation details require story review.

## Component standards
- **Header:** Black, crisp amber mark/wordmark, legible white navigation, amber primary CTA; interactive controls must work rather than imply unavailable features.
- **Hero:** Preserve the screenshot's expansive headline and slight sheen, but replace the low-contrast gray wash with a dark tonal gradient or adjust text colors until contrast is comfortably legible.
- **Buttons:** Amber primary; dark/outlined secondary; restrained gradient and hover lift. Always include visible keyboard focus and disabled/loading states.
- **Cards and forms:** Charcoal surface, gentle upper-edge highlight, controlled corner radius, clear labels and error/success feedback. No decorative blur that reduces readability.
- **Report / terminal mock:** Only demonstrate supported CLI or report content. Avoid fabricated `import saint` API, notebook export, self-serve upload, charts, AI output or file types until shipped.
- **SaaS surfaces:** Apply to auth, project lists, upload flow, jobs, reports, usage and admin, with dense, readable data states and accessible tables.
- **Themes:** If a light/dark toggle is shown, both themes must actually work and preserve contrast; otherwise hide the toggle.

## Accessibility, QA and truthful copy
- Target WCAG 2.2 AA for text contrast, keyboard navigation, focus visibility, touch targets and forms.
- Honor `prefers-reduced-motion`; avoid animated glow/blur causing performance issues.
- Capture desktop and mobile screenshots during implementation and review at 360px, 768px and 1440px (or equivalent).
- Do not make the launch site's CTAs promise features not implemented. For Friday 2026-11-13 concierge beta, use the real request-a-report workflow with CSV only and no self-serve login/upload/billing.
- Preserve existing verified site functionality and pass `uv run pytest`, `npm test`, `npm run build` plus applicable accessibility/visual checks.

## Delivery sequencing and authority
- **Friday concierge beta:** No major redesign or distraction from launch-critical PRs, intake, report verification, privacy and deployment. Only low-risk contrast/content corrections after approved merge reconciliation.
- **Epic 4.12:** Implement the full reusable token and component system as an explicitly approved, supervised story. Story 4.12 remains `backlog`, `loop_eligible: false` until Marvin changes canonical state.
- Treat this file as visual guidance, **not** authorization to edit pricing, security policy, authentication, billing or the canonical sprint ledger.
- A resume-capable Work loop must re-read this file together with `AGENTS.md`, the authoritative story and `sprint-status.yaml` before choosing frontend work.
