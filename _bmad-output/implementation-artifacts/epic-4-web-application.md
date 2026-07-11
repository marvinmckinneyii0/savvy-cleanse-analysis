# Epic 4 — Web Application & Customer Dashboard

<!-- Roadmap restructure 2026-07-09. PRD Phase 3. RENUMBERED from Epic 3. 13 stories
     (was 9). Read-only narrative; sprint-status.yaml is authoritative. Day counts: TBD. -->

**PRD mapping:** Phase 3 (Interface). Renumbered from Epic 3.

## Stories

| # | Story | Size | Model | loop_eligible | Note |
|---|---|---|---|---|---|
| 4.1 | Database Schema & Auth Foundation | L | Opus | false | AMENDED: includes the `project` entity (Task 4c), designed alongside tenant isolation |
| 4.1a | Config-to-Project Migration | M | Opus | false | NET-NEW |
| 4.2 | File Upload & Pipeline Integration | — | — | false | unchanged from existing Epic 3 def; pending individual review |
| 4.3 | Analysis Configuration UI | — | — | false | unchanged; pending review |
| 4.4 | Report Viewer & History | — | — | false | unchanged; pending review |
| 4.5 | Alert Dashboard & Timeline | — | — | false | unchanged; pending review |
| 4.6 | Alert Configuration UI | — | — | false | unchanged; pending review |
| 4.7 | Pipeline Health Dashboard | — | — | false | unchanged; pending review |
| 4.8 | Drift History View | — | — | false | unchanged; pending review |
| 4.9 | Usage Meter | — | — | false | unchanged; pending review |
| 4.10 | Onboarding Flow & Activation Definition | L | Sonnet | false | NET-NEW |
| 4.11 | Tier Capability Display | S | Sonnet | true | NET-NEW |
| 4.12 | Design System & Brand Tokens | L | Sonnet | false | NET-NEW |

## Story notes

**4.1 (AMENDED)** — Includes the `project` entity (schema-extensions-spec.md Task 4c):
`tenant_id → project_id → run_id`, designed alongside `org_id`/`user_id` multi-tenancy from
the start. Retrofitting after Epic 6 is expensive; doing it here is nearly free.

**4.1a (NET-NEW)** — Epics 1–3 are CLI and have no projects. Story 2.1's Configuration Layer
and Epic 3's cleaning policy both write config that becomes project-scoped here. This is a
migration (config file → project row), not greenfield. Small but real; not a footnote.

**4.10 (NET-NEW)** — Sequences registration → plan selection → first upload → guided
configuration → first report, with sensible defaults at every step so a tenant reaches a
generated report WITHOUT making a single configuration decision. Defines the `activated`
event explicitly and emits it. Epic 7's Story 7.7 CONSUMES this definition; it does not
invent its own. Rationale: every onboarding capability exists, scattered across Epics 3/4/5;
the PATH through them does not — no epic owns the sequence.
DoD addition: a new tenant reaches a generated report from registration WITHOUT consulting
documentation.

**4.11 (NET-NEW)** — Expandable capability descriptions on the in-app plan/upgrade surface.
CONSUMES Story 3.9's copy. Single source of truth — the pricing page and the in-app upgrade
prompt must not diverge.

**4.12 (NET-NEW)** — Implements Task 5 in full (see saint-design-tokens.css): two-token
accent, warm neutral ramp, severity palette, hero-gradient fix, wordmark lockup (full +
compact), type system. Uses ui-ux-pro-max-skill against savyanalytics.info, 21st.dev
components, Motionsites templates. HALT and ask on any brand-color ambiguity.
OPEN ITEM: the display typeface must be resolved from savvyanalytics.info before this ships
(not raster-matched); currently blocked in saint-design-tokens.css (`--font-display`).

## NAMING (do not blur)

"Guided setup" refers to 4.10 ONLY. Epic 11's 11.8–11.10 is "Governance Advisory." 4.10 gets
a tenant to their first report; 11.8–11.10 stops an Enterprise tenant from making an
expensive mistake. Different problems, different tiers, different epics.
