"""ExtractionClient — INTERFACE SPEC ONLY (backlog: Unstructured Data / Extraction).

STATUS: specification only. No implementation, no provider named, not wired into
any pipeline. Blocked on the Eval Harness (Epic 11). Do not implement here — this
file exists to fix the *interface shape* so the backlogged extraction epic and the
`extraction_fidelity` DQA category (schema-extensions-spec.md) have a stable contract.

Why an interface now, implementation never (yet):
  Extraction is the ONLY component whose failure mode is invisible to the system
  consuming it. A bad PDF/scan extraction produces structurally valid, consistently
  typed, non-duplicated data that passes all six existing DQA categories and is
  wrong. Every other component has a detectable failure mode. Therefore the output
  contract MUST carry PER-FIELD CONFIDENCE SCORES — that requirement is a HARD FILTER
  on eventual library/provider selection. Without it, `extraction_fidelity` DQA
  cannot exist and extraction failures are silent.

Provider-agnostic by construction. Mirrors the ``backend.core.llm_client`` abstraction
pattern already enforced: the architecture must not care which extractor is used, and
no provider is named here (Mistral OCR, Tesseract, VLM extractors, commercial APIs are
all deferred — anything chosen now would be stale by the time this ships).

    input:  document bytes + declared type
    output: structured data + PER-FIELD CONFIDENCE SCORES + extraction metadata
"""

from __future__ import annotations

from typing import Protocol


class FieldExtraction(Protocol):
    """One extracted field with its confidence. SPEC ONLY.

    ``value`` — the extracted value (str/number/date; type resolved downstream).
    ``confidence`` — model/provider confidence in [0.0, 1.0]. REQUIRED and per-field:
      this is the signal ``extraction_fidelity`` DQA consumes. A field with no
      confidence is not a valid extraction under this contract.
    ``source_ref`` — provenance locator (e.g. page/bbox/char span) for audit.
    """

    value: object
    confidence: float
    source_ref: str | None


class ExtractionResult(Protocol):
    """Result of extracting structured data from one document. SPEC ONLY.

    ``records`` — the structured rows/fields extracted, each carrying per-field
      confidence (see :class:`FieldExtraction`).
    ``metadata`` — extraction metadata: document type, page count, engine identifier
      (opaque string; never provider-branded in the contract), timing, warnings.
    ``min_field_confidence`` — the floor across all fields; a convenience the
      DQA ``extraction_fidelity`` category can threshold on without walking every field.
    """

    records: list[dict[str, "FieldExtraction"]]
    metadata: dict[str, object]
    min_field_confidence: float


class ExtractionClient(Protocol):
    """Provider-agnostic extraction interface. SPEC ONLY — do not implement here.

    A concrete client is introduced only by the (eval-gated) extraction epic, behind
    the Eval Harness (Epic 11). The interface deliberately says nothing about *how*
    extraction happens — only that it consumes document bytes + a declared type and
    returns structured data with per-field confidence and extraction metadata.
    """

    def extract(self, document: bytes, doc_type: str) -> "ExtractionResult":
        """Extract structured data from ``document`` of declared ``doc_type``.

        MUST return per-field confidence scores (see :class:`ExtractionResult`).
        Implementations are provider-agnostic; provider SDK imports (if any) stay
        lazy inside the concrete client, exactly as ``llm_client`` keeps its provider
        imports lazy. SPEC ONLY — raises here.
        """
        raise NotImplementedError("ExtractionClient is an interface spec — not yet implemented (blocked on Epic 11 eval harness).")
