# Supabase Issues Analysis

Date: 2026-05-02

## Scope reviewed
- `supabase/migrations/20241228000001_create_live_data_stream.sql`
- `supabase/migrations/20241228000002_add_user_security.sql`
- `supabase/migrations/20250714001951-0ddb6f34-f4bc-4e09-9123-d8075eac9a14.sql`
- `supabase/functions/live-data/index.ts`
- `src/integrations/supabase/client.ts`

## Findings

### 1) Migration failure risk from duplicate policy creation (High)
The migration `20250714001951-0ddb6f34-f4bc-4e09-9123-d8075eac9a14.sql` creates policy names that are already created in `20241228000002_add_user_security.sql`:
- `Users can view their own live data`
- `Users can insert their own live data`
- `Users can view their own API keys`
- `Users can insert their own API keys`
- `Users can update their own API keys`
- `Users can delete their own API keys`

Because the later migration uses plain `CREATE POLICY` (without `IF NOT EXISTS` or prior `DROP POLICY`), applying migrations sequentially on a fresh project will fail once it hits existing policy names.

**Impact:** fresh environment bootstrap can break during migration.

### 2) Table schema drift between migrations for `live_data_stream` (High)
The initial migration defines `live_data_stream` columns:
- `timestamp`, `source`, `metrics`, `raw_data`, `created_at`

But `20250714001951...` defines a different structure for the same table name:
- `data`, `processed_data`, `status`, `created_at`, `updated_at`

Since it uses `CREATE TABLE IF NOT EXISTS`, no schema reconciliation occurs if table already exists. The repository then carries two competing schemas for the same table.

**Impact:** engineers reading migrations can build against the wrong shape; long-term maintainability and onboarding risk.

### 3) Edge function payload contract tied to one schema variant (Medium)
`supabase/functions/live-data/index.ts` inserts:
- `timestamp`, `source`, `metrics`, `raw_data`, `user_id`

This matches the 2024 schema variant but not the 2025 variant (`data`, `processed_data`, `status`).

**Impact:** if a new environment is provisioned from an edited migration chain or via manual DDL following the newer schema intent, the edge function can fail at insert-time.

### 4) Realtime publication add is not idempotent-safe across environments (Low/Medium)
`ALTER PUBLICATION supabase_realtime ADD TABLE public.live_data_stream;` can error in some setups if table already in publication (depending on deployment history).

**Impact:** migration replay/import in non-pristine environments may fail.

## Recommended remediation plan

1. **Consolidate table contract (single source of truth).**
   Pick one `live_data_stream` schema and create an explicit forward migration that transforms old to new (or vice versa).

2. **Harden policy migrations.**
   Use `DROP POLICY IF EXISTS ...` before `CREATE POLICY ...`, or guarded `DO $$` blocks checking `pg_policies`.

3. **Split concerns:**
   - migration for structural changes
   - migration for policy updates
   - migration for trigger/function updates

4. **Align edge function with final schema.**
   Update `live-data/index.ts` to insert exactly the canonical columns.

5. **Add migration smoke test in CI.**
   Run `supabase db reset` (or equivalent local Postgres apply) to catch duplicate-policy and drift issues early.

## Quick wins
- Edit `20250714001951...` to avoid recreating existing policies.
- Add a dedicated migration that renames/maps fields if moving to `data/processed_data/status` model.
- Add comments in migrations to indicate deprecation path for old columns.
