"""Business-logic rules layer (Story 3.4).

Home of the Tier-2 cleaning *policy* — the "human sets policy once, agent
executes" half of the four-tier ownership model. Unlike the Tier-1
:class:`~backend.pipeline.cleaning_engine.CleaningEngine` (which acts
autonomously on a frozen registry), this layer executes a human-supplied
imputation policy against the *only* Tier-2 defect it is scoped to
(``null_values``), driving the policy-less
:func:`~backend.pipeline.cleaning_primitives.impute_nulls` primitive.

Architecture: this package may import ``models/``, ``errors/`` and
``pipeline/`` primitives; it must never import ``api/``, ``agents/``, legacy
modules, or a database. The Tier-1 engine is composed here (via the
coordinator) but never modified.
"""
