"""ParsedFile Pydantic models — server-side file-parse output contract.

The :class:`ParsedFileResponse` is produced by the file-parse endpoint
(``POST /api/parse-file``, see :mod:`backend.api.parse_file`) and consumed by
the frontend upload utility (``src/utils/fileParser.ts``). It is the typed
boundary that replaced the former client-side SheetJS (``xlsx``) parse, which
was removed to clear two HIGH advisories (GHSA-4r6h-8v6p-xvw6 prototype
pollution, GHSA-5pgg-2g8v-p4x9 ReDoS).

Why a dedicated contract
------------------------
Spreadsheet parsing now runs on the backend with ``openpyxl`` reading cells
directly — deliberately NOT through ``pandas.read_excel``, which silently
coerces types and fills nulls before the data is ever inspected. That would
violate the platform's detect-don't-fix constraint. This model is the shape
that crosses the wire after our own cell-iteration loop has run; it preserves
nulls as JSON ``null`` and records anything it could not represent faithfully
in :attr:`ParsedFileResponse.parse_errors` rather than dropping or coercing it.

The field shape intentionally mirrors the frontend ``ParsedData`` TypeScript
interface (``headers`` / ``rows`` / ``total_rows`` / ``file_type``) so the
client maps the response with a trivial rename. :attr:`parse_errors` is
additive — older consumers that ignore it remain valid.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# The set of conditions the cell-iteration loop surfaces instead of silently
# coercing. Kept as a Literal so an unexpected issue string fails validation
# at the contract boundary rather than leaking to the frontend.
#
# Note what is NOT here: a plain empty cell is not an error. Nulls are valid
# data — they are preserved as ``None`` in :attr:`ParsedFileResponse.rows` and
# left for the downstream completeness check to assess. Flagging every blank
# cell would drown the genuine signals below.
#
#   formula_cell -- a formula whose cached result was absent (workbook never
#                   recalculated), so no value could be read. raw_value holds
#                   the formula string.
#   error_cell   -- an Excel error literal (#REF!, #N/A, #DIV/0!, ...). The
#                   value is emitted as None; raw_value holds the error text.
CellIssueType = Literal[
    "formula_cell",
    "error_cell",
]


class CellParseError(BaseModel):
    """A single cell the parser could not represent faithfully.

    Emitted instead of mutating the value. ``raw_value`` is always the
    stringified original (``str(cell.value)``) so the payload is JSON-safe
    regardless of the offending cell's underlying type, and so the downstream
    DQA layer can surface the exact source value to the user.
    """

    row: int = Field(..., description="1-based row index in the source sheet.")
    column: str = Field(..., description="Header name, or column letter when headerless.")
    issue: CellIssueType
    raw_value: str = Field(..., description="str() of the original cell value.")


class ParsedFileResponse(BaseModel):
    """Typed result of a server-side file parse.

    Mirrors the frontend ``ParsedData`` interface. ``rows`` is jagged-safe
    (each inner list aligns to ``headers`` by position) and preserves nulls as
    ``None`` — never the empty string. Clean files carry an empty
    ``parse_errors`` list.
    """

    headers: list[str]
    rows: list[list[Any]]
    total_rows: int
    file_type: str
    parse_errors: list[CellParseError] = Field(default_factory=list)
