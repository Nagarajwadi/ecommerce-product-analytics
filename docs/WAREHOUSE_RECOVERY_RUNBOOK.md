# Warehouse and ETL Recovery Runbook

## Purpose and scope

This runbook covers local development and portfolio demonstrations. The CSV
ETL pipeline performs file I/O. The warehouse, reconciliation, incremental
loading, and ingestion workflow modules are in-memory prototypes. None should
be treated as production-ready recovery infrastructure.

## Environment setup

Run commands from the repository root.

Activate the existing virtual environment:

- Codespaces, macOS, or Linux: `source .venv/bin/activate`
- Windows PowerShell: `.venv\Scripts\Activate.ps1`

Install dependencies only if needed:

    python -m pip install -r requirements.txt

## Pre-run validation

Run focused tests for changed components:

    python -m pytest tests/test_etl_quality.py -q
    python -m pytest tests/test_warehouse_layers.py -q
    python -m pytest tests/test_warehouse_quality.py -q
    python -m pytest tests/test_incremental_loading.py -q
    python -m pytest tests/test_ingestion_workflow.py -q

Validate the complete branch with:

    PYTHONPATH=. python -m pytest -q

A test failure is not, by itself, a reason to regenerate data or rebuild the
database.

## Running the ETL pipeline

Input: `data/raw/raw_events.csv`

Output: `data/processed/clean_events.csv`

Run from the repository root:

    python etl/etl_pipeline.py

The pipeline validates columns and event types, parses timestamps, removes
exact duplicate rows, normalizes selected categorical fields, sorts events,
and checks data quality.

**Overwrite warning:** a successful run overwrites the processed CSV. Preserve
any output that must be retained before rerunning.

Do not run `python src/generate_data.py` as a generic recovery step because it
can regenerate raw data. Inspect `sql/setup_database.py` before running it;
do not rebuild the SQLite database merely because a test fails.

## Failure and recovery procedures

### Missing input or path error

1. Confirm the current directory is the repository root.
2. Check whether `data/raw/raw_events.csv` exists.
3. Do not generate replacement data until the missing input is confirmed and
   regeneration is intentional.

### Schema, event, timestamp, or quality failure

1. Preserve the raw input and error output.
2. Inspect the specific reported columns or values.
3. Check the ingestion contract and accepted event types.
4. Correct the source or make a reviewed code change.
5. Run focused tests before rerunning ETL.

Do not bypass validation just to produce an output file.

### Interrupted run or unexpected output

1. Do not assume the processed CSV is complete or current.
2. Inspect the input, output, and console error.
3. Preserve any output needed for investigation.
4. Confirm the intended input and output paths before rerunning.
5. Verify the completion message, row count, and relevant quality tests.

The current ETL pipeline has no durable checkpoints, automated retries,
transactional file replacement, or automatic rollback. Recovery is manual.

## In-memory prototype checks

Run warehouse tests with:

    python -m pytest tests/test_warehouse_layers.py tests/test_warehouse_quality.py -q

These tests check prototype behavior and internal count consistency. They do
not prove source completeness, stable event identity, or persisted
source-to-target reconciliation.

Incremental loading uses a composite fingerprint, not a stable source event
ID. Identical legitimate events can be mistaken for duplicates. Do not rely
on this prototype as a production identity or retry contract.

## Production-readiness requirements

Before production use, implement and test:

- Stable event IDs and a historical backfill policy.
- Schema versioning and explicit timestamp/timezone rules.
- Late-arriving-event handling and backfills.
- Durable rejected-record quarantine, retries, monitoring, and alerts.
- Persistence and transaction boundaries.
- An isolated test database, backups, migration procedures, and tested
  recovery and rollback.
- Source-to-target reconciliation and operational ownership.

Until then, treat the warehouse and ingestion modules as prototypes.

## Related documentation

- `docs/WAREHOUSE_LAYERS_PROTOTYPE.md`
- `docs/WAREHOUSE_QUALITY_RECONCILIATION.md`
- `docs/INCREMENTAL_LOADING_PROTOTYPE.md`
- `docs/INGESTION_WORKFLOW_PROTOTYPE.md`
- `docs/INGESTION_CONTRACT.md`
- `docs/WAREHOUSE_AND_ETL_DESIGN.md`
