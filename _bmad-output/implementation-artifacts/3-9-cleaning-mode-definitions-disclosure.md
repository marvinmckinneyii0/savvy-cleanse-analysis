# Story 3.9: Cleaning Mode Definitions & In-Product Disclosure

Status: ready-for-dev

Sizing: M · Model: Sonnet · loop_eligible: true
PREREQUISITES: Story 3.4 (done), Story 3.5 (done)
<!-- Source: Epic 3 story note; Story 3.4 ACs/config contract; Story 3.5 client-safety boundary; sprint-status.yaml. The 3.9 copy is canonical for Story 4.11 to consume. -->

## Story

As an **SAINT user choosing whether and how to enable cleaning**,
I want **plain-language descriptions of the cleaning behavior and each available null-imputation method at the point where I configure it**,
so that **I can make an informed choice without needing to understand internal implementation terms**.

## Context and scope

Stories 3.4 and 3.5 are complete. Story 3.4 established cleaning as opt-in (off by default), the CleaningConfig/ImputationPolicyConfig contract, and the available methods: mean, median, mode, forward_fill, and policy-only leave_as_is. Its explicit out-of-scope list assigns client-facing copy and method descriptions to this story. Story 3.5 establishes that human-only findings remain untouched and that internal taxonomy must not leak into client-facing text.

This story provides one authoritative, reusable set of client-facing descriptions and surfaces them beside the existing cleaning enablement and imputation configuration controls. Locate those controls in the current CLI/config experience before implementation; do not create a new UI. Story 4.11 consumes the same copy for its capability display and must not maintain a duplicate set.

**In scope**

- Explain that enabling cleaning applies supported deterministic changes to a working copy, leaves the original input untouched, and records actions in the Healing Manifest.
- Describe the available imputation choices at the existing point where a user enables/configures cleaning.
- Use the existing method keys as stable internal lookup keys, with descriptive client-facing labels and concise explanations.
- Keep the copy in one reusable source that the existing enablement surface can render and Story 4.11 can consume.

**Out of scope**

- Changing the cleaning opt-in/default, policy resolution, available methods, execution order, or remediation behavior.
- Changing report data flow, Healing Manifest structure, schemas, database/config contracts, or report rendering.
- Implementing the Epic 4 web UI or Story 4.11's capability display.
- Promising that a chosen method is appropriate for a particular dataset or column.
- Exposing remediation tiers, enum values, or internal implementation labels to clients.

## Acceptance Criteria

1. **Cleaning behavior disclosed at enablement.** Beside the existing cleaning enablement control, concise client-facing text states that cleaning is optional and off by default, applies supported changes to a working copy, preserves the original input, and records actions in the Healing Manifest. Wording does not imply that enabling cleaning authorizes human-only/judgment-required findings to be changed.

2. **All configured imputation methods have accurate, plain-language descriptions.** The reusable copy covers each method supported by Story 3.4 and states its effect and a material limitation:
   - mean — fills gaps with the column's average; can be pulled by unusually high or low values and can reduce observed variation.
   - median — fills gaps with the middle value; less affected by unusually high or low values, but can understate variation.
   - mode — fills gaps with the most common value; can overrepresent the common category and conceal less frequent values.
   - forward_fill — carries the previous available value forward; assumes the earlier value remains a reasonable substitute and cannot fill leading gaps with no earlier value.
   - leave_as_is — preserves missing values; no values are filled.
   
   The descriptions do not claim certainty, suitability, or improved analytical accuracy.

3. **Displayed choices match the configured policy.** The descriptions are keyed to the exact Story 3.4 method identifiers. The enablement/configuration surface only presents choices the existing configuration accepts; leave_as_is is described as preserving missing values and is not presented as an execution primitive. Unknown identifiers fail closed and are never rendered as raw client-facing text.

4. **Client-safe language.** No client-facing label, help text, or rendered description contains tier numbers, remediation_class, internal enum names (including HUMAN_POLICY_AGENT_EXECUTION or HUMAN_ONLY), or internal policy/execution terminology. Describe outcomes in ordinary language. Do not expose column values, row data, exception text, or other dataset content in this copy.

5. **One source of truth for current and future surfaces.** There is a single reusable copy definition. The existing enablement surface reads from it, and the code/interface makes it reusable by Story 4.11 without copying strings. No capability-display UI is built here.

6. **No behavior or contract drift.** Cleaning remains opt-in and off by default. Existing method identifiers, config validation, policy resolution, cleaning actions, manifest contents, and report behavior are unchanged. The original input remains untouched. The copy does not suggest that Tier-3/human-only findings are cleaned.

7. **Meaningful tests.** Add tests that verify:
   - Every configured method has a non-empty client-facing label and explanation, and the mapping has no missing or extra method keys.
   - Each method description accurately states its effect and required limitation, including forward-fill's leading-gap limitation and leave_as_is's no-change behavior.
   - The enablement surface renders the cleaning disclosure and available method copy, while unknown values fail closed without exposing raw values.
   - Client-facing copy contains none of the prohibited internal/tier terms.
   - Story 4.11's consuming interface can use the same copy source (without a second copy definition).
   - Existing default-off and cleaning-policy behavior tests remain unchanged and pass.

8. **Definition of Done.** Targeted tests and the full backend suite pass. Run the repository's required security review and resolve Critical/High findings before marking the story done. Record test totals and review outcome in the implementation PR.

## Implementation notes

- Treat Epic 3 and the completed Stories 3.4/3.5 as the source of truth for scope and behavior. If the current enablement surface differs from its story documentation, document the observed path in the PR and adapt the presentation point without widening behavior.
- Keep the copy deterministic and independent of dataset contents.
- Preserve descriptive client-facing names; method identifiers may remain behind the reusable mapping for configuration compatibility.
- Story 4.11 consumes this mapping. Do not duplicate or fork its text.
- Do not change loop_eligible: true or any other ledger field as part of implementation.

## Tasks / Subtasks

- [ ] Verify the current cleaning enablement/configuration surface and the accepted method identifiers on main.
- [ ] Define the client-safe reusable description mapping and its consuming interface.
- [ ] Render the cleaning disclosure and method descriptions at the existing enablement/configuration point.
- [ ] Add the acceptance-criteria tests, including prohibited-term and fail-closed coverage.
- [ ] Run targeted and full tests; run the required security review and record results.
