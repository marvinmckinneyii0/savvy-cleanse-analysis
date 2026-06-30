# Sprint Change Proposal
**Date:** 2026-06-30
**Project:** SavvyCortex
**Classification:** Minor — Direct dev implementation, no epic restructuring
**Triggered by:** Issue #24 (Story 1.4 DoD / `/security-review` follow-up)
**Branch:** `security/issue-24-xlsx-server-side-migration`
**PR:** #27

---

## Section 1: Issue Summary

### Problem Statement

Story 1.4 (LLM Narrative Generation) was marked done after PR #23 cleared 13 of 16 npm audit advisories. The `xlsx` (SheetJS) package was the final outstanding carve-out — the only remaining HIGH-severity npm advisory group. Post-merge `npm audit` continued to surface two unpatched HIGH CVEs against the frozen SheetJS package:

| CVE / Advisory | Type | Status |
|---|---|---|
| GHSA-4r6h-8v6p-xvw6 | Prototype Pollution | No upstream fix available |
| GHSA-5pgg-2g8v-p4x9 | ReDoS | No upstream fix available |

SheetJS (`xlsx`) has been effectively unmaintained on npm since a 2023 license/publish dispute and the CVEs have no patch path on the public registry. The library was the sole `.xlsx` parse mechanism, running **client-side** in the browser bundle.

Story 1.4's Definition of Done explicitly requires `/security-review` to resolve all Critical and High findings before closure. This change resolves that remaining gate.

---

## Section 2: Impact Analysis

### Epic Impact

| Epic | Impact |
|---|---|
| Epic 1 (done) | Story 1.4 DoD closes. No other stories affected. |
| Epic 3 (backlog) | FR11 (xlsx parse) responsibility partially lands ahead of schedule — server-side endpoint created as a minimal host, not the full Epic 3 API layer. Epic 3 scope unchanged. |
| Epics 2, 4–7 | No impact. |

### Architectural Branch Analysis

Two candidate paths were evaluated:

**Path A — Client-side parse with alternative library**
- Original candidate: ExcelJS
- **Rejected:** ExcelJS is a Node.js library that requires a server-side execution context. It cannot run in the browser and is not compatible with the Vite/browser bundle. Bringing it in would require either a fake shim or a bundler polyfill that defeats the purpose of client-side parse.

**Path B — Server-side parse (selected)**
- Python equivalent: `openpyxl`
- `openpyxl` is already an **indirect dependency** via `pandas` — same pip/Dependabot audit-graph posture, no new supply-chain surface.
- Parse moves to a new FastAPI endpoint; client submits the raw file and receives structured JSON.
- Eliminates ExcelJS/browser-bundling risk entirely.
- Aligns with Phase 10/11 enterprise compliance posture (financial, healthcare verticals) where raw file custody server-side matters for audit trail and PII/PHI handling.

**Path B selected.** `openpyxl` is called directly rather than via `pandas.read_excel()` to preserve detect-don't-fix semantics — `pandas.read_excel()` silently coerces dtypes and fills NaN before inspection, which would mask data quality issues that the pipeline is designed to surface.

### Story Impact

| Story | Impact |
|---|---|
| 1-4 (LLM Narrative Generation) | DoD security gate clears. Story closes. |
| All other Sprint 1 stories | No impact — parse contract (`ParsedData` interface) unchanged. |

### Artifact Conflicts

| Artifact | Change Required |
|---|---|
| PRD | None — xlsx parse is an implementation detail within existing FR11 scope. |
| Architecture | No structural change — backend/api/app.py is documented as a minimal host, explicitly not the Epic 3 API layer, to avoid implying Epic 3 build-out is complete. |
| UX Design | None — file upload UX unchanged; server-side parse is transparent to the user. |
| Sprint Status | Issue #24 → resolved; link Sprint Change Proposal. |

### Technical Impact

**New files:**
- `backend/models/parsed_file.py` — `ParsedFile` Pydantic response model
- `backend/api/parse_file.py` — `/api/parse-file` FastAPI endpoint (openpyxl parse logic)
- `backend/api/app.py` — minimal FastAPI host for the endpoint; **not** the Epic 3 API layer
- `backend/tests/test_parse_file.py` — 12 tests covering xlsx parse, error paths, and contract compliance

**Modified files:**
- `src/utils/fileParser.ts` — SheetJS removed; xlsx delegated to server endpoint; 0 `XLSX.` calls remaining
- `src/components/dashboard/DataPreview.tsx` — async parse flow; client submits file, awaits JSON
- `vite.config.ts` — SheetJS bundle exclusion removed (no longer needed)

**Contract changes:**
- `ParsedData` interface: **unchanged** (structural contract preserved across all parse paths)
- New optional field: `parseErrors?: string[]` — surfaced from server on partial parse failures

**Related narrow fix (scoped to CSV, primary path):**
- CSV empty-cell handling aligned to `null` preservation (`?? null`) — detect-don't-fix consistency fix. Scoped narrowly to CSV; parseTXT/parseJSON null-consistency pass deferred (see out-of-scope follow-ups).

**Legacy format:**
- `.xls` (legacy binary Excel) support dropped. Resolved as Option 1 in PR #27 follow-up commit — users must supply `.xlsx`. No existing test data or pipeline inputs used `.xls`.

---

## Section 3: Recommended Approach

**Direct Adjustment — implement within current sprint, no backlog reorganization.**

- SheetJS replaced by server-side openpyxl endpoint.
- No new epics, stories, or PRD changes required.
- Epic 3 scope and ordering unchanged — `backend/api/app.py` is a stub host, not an Epic 3 deliverable. The Epic 3 API layer will subsume this endpoint at the appropriate time.

**Effort:** Completed. PR #27 ready for review/merge.
**Risk:** Low. `ParsedData` contract unchanged; 12 new backend tests + 123 total backend tests passing; `tsc --noEmit` clean; `npm run build` green; 0 SheetJS imports in `src/`.
**Timeline impact:** None. Sprint 1 closes on schedule.

---

## Section 4: Detailed Change Proposals

All changes are already implemented in PR #27. No further edit proposals required. Change summary for record:

### Backend — New Endpoint

```
backend/api/parse_file.py
POST /api/parse-file
  Accepts: multipart/form-data (file: UploadFile)
  Returns: ParsedFile (rows, columns, parseErrors?)
  Parser: openpyxl (direct, not pandas.read_excel)
  Rationale: pandas silently coerces/fills; direct openpyxl call preserves
             raw cell values for detect-don't-fix inspection
```

### Frontend — SheetJS Removal

```
src/utils/fileParser.ts

OLD (xlsx paths):
  import * as XLSX from 'xlsx';
  const wb = XLSX.read(buffer, { type: 'array' });
  ...

NEW:
  // xlsx delegated to server; client sends raw file, receives ParsedData JSON
  const response = await fetch('/api/parse-file', { method: 'POST', body: formData });
  const data: ParsedData = await response.json();

Rationale: Eliminates SheetJS entirely. No patched version available on npm.
```

### CSV Null Consistency (scoped fix)

```
src/utils/fileParser.ts (CSV path only)

OLD: cell || ''
NEW: cell ?? null

Rationale: Empty string masked missing values from pipeline quality checks.
           Scoped to CSV (primary path); parseTXT/parseJSON deferred.
```

---

## Section 5: Implementation Handoff

### Classification: Minor

> Direct implementation by dev team. No PO/SM/PM/Architect escalation required.

### Handoff

| Recipient | Action |
|---|---|
| Dev (Marvin) | Review PR #27, confirm .xls follow-up commit landed, merge to main |
| SM | Update `sprint-status.yaml` — Issue #24 resolved, Story 1.4 DoD closed |
| PM / Architect | No action required |

### Success Criteria

- [ ] `npm audit` reports 0 HIGH findings for `xlsx` / SheetJS
- [ ] `tsc --noEmit` exits clean
- [ ] `npm run build` green
- [ ] 0 `import * as XLSX` / `XLSX.` calls in `src/`
- [ ] 123 backend tests passing (12 new)
- [ ] PR #27 merged to main
- [ ] `sprint-status.yaml` updated — Issue #24 resolved

---

## Section 6: Epic 3 / FR11 Annotation

`backend/api/app.py` introduced in this PR is a **minimal FastAPI host** created solely to serve the `POST /api/parse-file` endpoint needed to replace client-side SheetJS. It is **not** the Epic 3 API layer and does not imply that Epic 3 work has begun or is complete.

Epic 3 (`3-2-file-upload-pipeline-integration` and related stories) will build the full web backend, authentication layer, and proper API surface. At that point the minimal host will be subsumed or replaced. Epic 3 status remains `backlog` and its scope is unchanged.

FR11 (xlsx parse capability) is now partially served by a server-side implementation ahead of Epic 3 schedule. This is intentional — a security gate required it — and the PRD framing of FR11 as a backend responsibility is actually more correct after this change than before.

---

## Section 7: Out-of-Scope Follow-Ups (Carried Forward)

The following were identified during this PR but are **not resolved here**. They are logged for future sprint planning:

| Item | Advisory / Context | Recommended Action |
|---|---|---|
| vite/esbuild moderate→high | GHSA-67mh-4wv8-2f99 | Requires breaking `vite` major version bump — schedule for Epic 3 frontend setup story |
| parseTXT / parseJSON null-consistency | Only CSV path aligned in this PR | Add narrow `?? null` fix to remaining parse paths in a future story |
| RFC 7807 Problem Details | `/api` error responses are currently unstructured | Lands with Epic 3 API layer build-out |

---

## Section 8: Sign-Off

**Classification confirmed:** Minor — no further BMad workflow gates required before merge.

**PR #27** (`security/issue-24-xlsx-server-side-migration` → `main`) is ready for review and merge, contingent on confirmation that the `.xls` follow-up commit is included.

**Story 1.4 DoD:** All criteria met. Security gate (Issue #24) resolved. Story closes.

**Sprint 1 (Epic 1):** Remains `done`. No regressions to existing parse paths. No epic restructuring.

---

*Sprint Change Proposal generated 2026-06-30 — SavvyCortex / bmad-correct-course workflow*

---

## Merge Note — Squash-Merge Branch-Deletion Race (2026-06-30)

**What happened:** PR #27 was merged via `gh pr merge --squash --delete-branch`. This command squashed the remote branch state into main and simultaneously deleted both the remote and local branch — before two local commits had been pushed to the remote:

| Orphaned SHA | Commit |
|---|---|
| `c6d99d5` | `fix(security): drop legacy .xls support from upload UI (#24 follow-up)` |
| `5bef3bd` | `test(frontend): configure Vitest + cover Issue #24 migration surfaces` |

**Recovery:** Both commits were recovered from `git reflog` and cherry-picked onto main as:

| Live SHA on main | Description |
|---|---|
| `2511998` | Squash of original PR #27 scope (server-side xlsx migration) |
| `4b8c91c` | Cherry-pick of `c6d99d5` — .xls UI rejection fix |
| `df7d6d5` | Cherry-pick of `5bef3bd` — Vitest setup + 18 tests |

**Post-recovery validation (2026-06-30):**
- `tsc --noEmit` — clean (exit 0)
- `npm run build` — green (exit 0)
- `npx vitest run` — 18/18 passed
- `npm audit --audit-level=high` — 0 new HIGH findings; only pre-existing GHSA-67mh-4wv8-2f99 (vite/esbuild, logged follow-up)
- `git diff c6d99d5 main -- src/components/dashboard/UploadArea.tsx` — no output (zero drift)
- `git diff 5bef3bd main -- src/test/ vite.config.ts tsconfig.app.json package.json` — no output (zero drift)

**Archive tags** (permanent rollback anchors, will not expire like reflog):
- `archive/issue-24-pre-cherrypick-xls` → `c6d99d5`
- `archive/issue-24-pre-cherrypick-vitest` → `5bef3bd`

**Squash commit message gap:** GitHub generated the squash commit message from the PR body at merge time. The PR body had since been updated (`.xls` "Resolved" sub-heading, Vitest test note) but those updates post-date the snapshot. The squash commit message (2511998) therefore covers only the original PR scope. The two cherry-pick commits carry accurate, independent messages. This is a documentation-only gap — code on main is verified correct.
