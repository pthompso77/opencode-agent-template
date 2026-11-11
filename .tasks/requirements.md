# Requirements: US Congress Member Data Pipeline

**Status:** Draft (discovery complete through grilling Rounds 1-3)
**Source of truth for:** `/plan` task decomposition
**Related:** `CONTEXT.md` (glossary), `docs/adr/*` (decisions)

---

## 1. Goal

Build an automated, daily batch data pipeline that ingests **current US Congress members** from the Congress.gov v3 API (`https://api.congress.gov/v3/member`), lands raw payloads immutably, transforms them into an analytics-ready dimensional model with **dbt**, validates ingestion against an explicit **data contract** with **Great Expectations**, and orchestrates the whole thing with **Prefect** on a daily schedule. The project is a portfolio demonstration of production data-engineering practice: idempotency, observability, contract enforcement, and reproducible environments.

This project is built **alongside** the existing agent-harness repo, in a self-contained subdirectory.

---

## 2. Scope

### In scope
- Daily scheduled ingestion of **current members** (`currentMember=true`, ~539 records).
- Full-detail fetch per member (`/v3/member/{bioguideId}`).
- Immutable raw payload landing (bronze) in Postgres.
- Contract definition (YAML) + Great Expectations enforcement at bronze.
- dbt transformations: staging (silver) + dimensional marts (gold) with tests.
- SCD2 history for member attributes.
- Prefect orchestration (self-hosted server in Docker Compose, work pool + deployments).
- Docker Compose environment (Postgres + Prefect server + worker).
- pytest unit tests, Testcontainers integration tests, GitHub Actions CI.
- README with architecture diagram, Makefile task runner.

### Out of scope
- Historical members (non-current) — no backfill beyond the 2026 bootstrap window.
- Bills, votes, committees, or any endpoint other than member.
- BI dashboard / presentation layer.
- Full SCD2 on the entire payload (only scalar member attributes; arrays use natural grain).
- Cloud deployment (local/Compose only).

---

## 3. Verified data-source facts (probed live)

These were confirmed against the API and constrain the design:

| Fact | Value / Behavior |
|---|---|
| List endpoint | `GET /v3/member?format=json` |
| Detail endpoint | `GET /v3/member/{bioguideId}` |
| Pagination | `offset` + `limit`; **`limit` maxes at 250** (251 silently clamped to 250) |
| Rate limit | 20,000 requests/hour (`x-ratelimit-limit`); remaining exposed via header |
| `currentMember=true` | **539** members |
| `currentMember=false` | 2696 members |
| `updateDate` query param on list | **Ignored** — returns all 2696 for any date value |
| `fromDateTime` query param on list | Filters, but semantics not fully reliable (varies with other params) |
| List record fields | `bioguideId, name, partyName, state, district, terms.item, updateDate, url, depiction` |
| Detail record fields | adds `firstName, lastName, directOrderName, invertedOrderName, honorificName, birthYear, currentMember, partyHistory, terms[], addressInformation, officialWebsiteUrl, previousNames, sponsored/cosponsoredLegislation (counts)` |
| `partyName` enum | `Democratic`, `Republican`, `Independent` |
| `updateDate` | Present on both list and detail; sampled values match between endpoints |

**Consequence:** date-range query params are not a trustworthy incremental cursor for this endpoint. Change detection must be payload-derived (see ADR-0002).

---

## 4. Architecture (Medallion)

Postgres is the single warehouse. Layers are **schemas**:

| Layer | Schema | Contents |
|---|---|---|
| **Bronze** | `bronze` | Immutable raw JSON payloads (list + detail) + ingestion run metadata |
| **Silver** | `silver` | Cleaned / typed / deduplicated dbt staging models |
| **Gold** | `gold` | Conformed dimensional marts (dims + facts) served to consumers |

**Canonical layer names are `bronze` / `silver` / `gold`** (Q17). "raw/iron/copper" is explicitly rejected.

Flow: `API → Prefect extract/load → bronze (raw JSONB) → GE contract validation (fail-closed) → dbt run (silver) → dbt snapshot + run (gold) → GE/dbt gold checks (alert-only)`.

---

## 5. Component responsibilities

### 5.1 Prefect (orchestration)
- Self-hosted Prefect **server as its own Docker Compose service** (Q5/Q18), plus a worker service.
- **Work pool + deployment** model (not ephemeral, not bare `flow.serve()`).
- Two deployments:
  - **Daily**: cron schedule (daily) — full current-member sweep.
  - **Backfill**: manual, parameterized (bootstrap from `2026-01-01`).
- Tasks: enumerate members (paginated), fetch detail, land raw, run GE checkpoint, dbt run, dbt snapshot, gold checks, emit run summary.
- Integrations via `prefect-dbt` and `prefect-great-expectations` **where the needed feature is implemented in the collection**; fall back to subprocess/Python tasks otherwise (explicitly permitted — e.g. GX features absent from `prefect-great-expectations`) (Q19).

### 5.2 Ingestion (extract + load)
- **Full sweep**: enumerate all current members each run via pagination (`limit=250`).
- **Change detection**: compare a per-member signature (list `updateDate` first, detail payload hash authoritative) against the latest bronze state; **fetch detail only for new/changed members**.
- **Bootstrap (Q2)**: initial load covers current members with activity from `2026-01-01`; thereafter full current sweep.
- **Idempotent upsert** keyed on `bioguideId`.
- **Raw landing**: append-only ledger of every fetched payload (full JSONB) plus a latest-state convenience table.

### 5.3 Great Expectations (validation)
- Validates **bronze** immediately after load, against the checked-in **data contract**.
- **Fail-closed** at bronze: a contract breach halts the pipeline before silver/gold.
- Freshness is **not** a bronze contract clause; it is a gold/monitoring SLA check (alert-only).

### 5.4 dbt (transformation)
- Silver: staging models — typed, renamed, deduplicated, one row per member (current-state).
- Gold: dimensional marts:
  - `dim_member` — SCD2 on scalar attributes.
  - `member_terms` — term grain (member × term).
  - `member_party_history` — party-affiliation grain.
- dbt tests enforce silver/gold invariants: uniqueness, not-null, relationships, accepted values.
- Runs as Prefect tasks (`dbt run`, `dbt snapshot`, `dbt test`).

---

## 6. Domain model

### 6.1 Entities & grain
- **Member** — identified by **Bioguide ID** (`bioguideId`). Current-state snapshot in silver.
- **Term** — one continuous period of service in a chamber; natural grain `(bioguideId, congress, chamber, startYear)`. Source: detail `terms[]`.
- **Party History** — interval of party affiliation; grain `(bioguideId, partyAbbreviation, startYear)`. Source: detail `partyHistory[]`.
- **Raw Payload** — one row per fetch (append-only), keyed by run + bioguideId.

### 6.2 SCD2 (Q7/Q14)
- Full SCD2 on **scalar** member attributes (name fields, state, district, current party, `currentMember` flag, birth year, honorific).
- Change trigger: hash (e.g. `dbt_utils.generate_surrogate_key`) over the tracked scalar set; on hash change, close current version and open new.
- Array-valued history (`terms`, `partyHistory`) is **not** SCD2-tracked; it is modeled at its natural grain in separate marts.
- Exact tracked-attribute set is provisional (Q14 "go with default for now") and may be refined during implementation; the *pattern* (hash-based SCD2) is firm.

---

## 7. Data contract (Q8/Q15/Q16)

- **Format**: checked-in YAML (e.g. `contracts/bronze_members.yaml`) — vendor-neutral, single source of truth.
- A loader asserts the GE suite **covers every clause** in the contract; GE is the enforcement engine, the contract is the authority.
- **Bronze contract clauses**:
  - Required fields present (`bioguideId`, `name`, `partyName`, `state`, `updateDate`, `url`).
  - Type checks (strings, ints where applicable).
  - `partyName` ∈ `{Democratic, Republican, Independent}`.
  - `bioguideId` matches regex `^[A-Z]\d{6}$`.
  - `updateDate` parses as ISO-8601.
  - Pagination/count consistency (returned rows ≤ declared count; no truncation without a `next` cursor).
- **Not** in contract: freshness (→ gold SLA).
- **Boundary**: GE = bronze contract enforcement; dbt tests = silver/gold model invariants (no duplication).

---

## 8. Configuration & secrets (Q6)

- API key supplied via `.env` read with `pydantic-settings`; `.env.example` committed, `.env` git-ignored.
- **Action required:** the API key currently in `.mystuff/scratch.md` is exposed — rotate it and place the new key only in `.env`.
- Postgres connection + Prefect API URL are environment-driven defaults for Compose.

---

## 9. Repository & environment

### 9.1 Layout (Q1/Q11/Q20)
- Project lives in **`congress_pipeline/`** subdirectory; structured to be extractable to its own repo later. **Not** a git submodule (avoids clone/CI friction).
- Inside `congress_pipeline/`:
  - `src/congress_pipeline/` — importable Python package (flows, ingest, contracts loader, settings).
  - `dbt/` — dbt project.
  - `great_expectations/` — GE config + checkpoint/suite definitions.
  - `contracts/` — YAML data contracts.
  - `tests/` — pytest unit + integration.
  - `docker-compose.yml`, `pyproject.toml`, `Makefile`, `.env.example`, `README.md`.
- **Dependencies tracked via `uv`** (`pyproject.toml` + `uv.lock` committed; `.venv` ignored) (Q20).
- Root repo gains a `.gitignore` that excludes the pipeline's `.env`, `.venv`, and build artifacts.

### 9.2 Compose topology (Q5)
- `postgres` service (warehouse).
- `prefect-server` service (orchestration API/UI).
- `prefect-worker` service (runs deployments).
- Postgres default DB `congress`, port `5432`.
- Single-node local profile; CI uses Testcontainers instead of Compose.

---

## 10. Testing & CI (Q9/Q21)

- **Unit tests** (pytest): pagination, change detection, contract loader, payload flattening, settings.
- **Integration tests**: Postgres via **Testcontainers** (ephemeral, no port conflicts); run a real load → GE checkpoint → dbt build against a throwaway DB.
- **CI** (GitHub Actions): lint, typecheck, unit tests, integration tests, `dbt parse`.
- **Makefile**: `up`, `down`, `bootstrap`, `daily`, `dbt-build`, `ge-check`, `test`, `lint`.

### 10.1 Verification commands (for `/plan`)
- `uv run ruff check .`
- `uv run mypy src`
- `uv run pytest`
- `uv run dbt parse --project-dir dbt` (or `dbt build` in integration)
- `docker compose config` (topology sanity)

---

## 11. Non-functional requirements

- **Idempotency**: re-running any day's flow must not duplicate bronze or gold rows; upsert/snapshot semantics guarantee convergence.
- **Reproducibility**: every fetched payload retained immutably → replayable; environment pinned via `uv.lock`.
- **Rate limits**: respect 20,000/hr; full sweep + detail fetches stay far below (~1,100 requests worst case). Backoff on 429/5xx.
- **Fail-closed ingestion**: contract breach blocks downstream layers.
- **Observability**: Prefect run UI, GE validation results, structured logs, run summary artifact.
- **Maintainability**: layer boundaries enforced by schema isolation; contract decoupled from engine.

---

## 12. Open items (TBD)

- **Q3** Incremental/cursor semantics: exact daily change-detection cursor to be finalized during ingestion implementation (date params proven unreliable; signature/hash approach assumed).
- **Q13/Q14** Exact change signal + SCD2 attribute set: list `updateDate` as cheap pre-filter, detail payload hash as authoritative; tracked-attribute list provisional.
- **Q19** GE/dbt Prefect integration: use collections unless a required GX feature is missing → subprocess fallback.
- API key rotation (security, see §8).

---

## 13. Acceptance criteria

### Functional
1. `make up` brings up Postgres + Prefect server + worker via Docker Compose.
2. A daily Prefect deployment sweeps all current members (~539), landing raw payloads in `bronze` idempotently.
3. Detail payloads are fetched only for new/changed members; unchanged members produce no duplicate rows.
4. The YAML data contract exists and a loader verifies GE suite coverage of every clause.
5. The GE bronze checkpoint fails closed on a deliberately corrupted payload and halts the run.
6. dbt produces silver staging (one current row per member) and gold `dim_member` (SCD2), `member_terms`, `member_party_history`.
7. A simulated attribute change produces exactly one new SCD2 version with correct valid-from/valid-to.
8. A manual backfill deployment from `2026-01-01` loads the bootstrap set.
9. `uv` manages deps; `uv.lock` committed; `.venv` ignored.

### Non-functional
10. `uv run pytest` passes (unit + Testcontainers integration).
11. CI workflow runs lint, typecheck, tests, and `dbt parse` on push/PR.
12. README documents architecture (medallion diagram), contract, and run instructions.
13. Re-running a completed day's flow leaves row counts unchanged (idempotency test).
14. Pipeline stays within API rate limits.

---

## 14. Discovery provenance

- Round 1: repo layout, data scope, storage shape, topology, secrets, history, GE/dbt boundary, deliverables, naming.
- Round 2: repo boundary, bootstrap vs incremental, detail fetch, SCD2 attributes, contract format/clauses, layer naming, Prefect deployment, integrations, repo internals, integration testing, quality-gate semantics.
- Round 3: incremental cursor resolution, SCD2 trigger, contract authority, medallion adoption.
- Live API probes informed §3 and forced the payload-signature change-detection design (ADR-0002).
