# MIZA DataHub API Modernization Plan

**Status:** Draft
**Last updated:** 2026-11-11
**Owner:** API/Platform
**Source of truth:** This file for project execution. See `AGENTS.md` for repo
operating instructions and `doc/ARCHITECTURE_IMPLEMENTATION_PLAN.md` for the
original proposal (not the current implementation).

---

## How to use this document

- This is the single source of truth for scope, ordering, and progress.
- Work top-to-bottom unless a phase is explicitly marked parallel.
- Update task checkboxes and phase status as work lands.
- Do not start a phase until its dependencies meet their exit gates.
- Add new work to the relevant phase; do not create ad-hoc checklists elsewhere.

### Status legend

| Marker | Meaning |
|---|---|
| `[ ]` | Not started |
| `[~]` | In progress |
| `[x]` | Done |
| `[!]` | Blocked |
| `[-]` | Cancelled / descoped |

### Phase status

| Status | Meaning |
|---|---|
| Not started | No implementation work merged |
| In progress | At least one task active |
| Blocked | Waiting on an open decision or dependency |
| Done | Exit gate verified |

---

## Locked decisions

| Area | Decision |
|---|---|
| Primary consumer | Web dashboard |
| Authentication | OAuth2 / JWT |
| Authorization | Scoped tokens plus per-factory/line object authorization |
| Long-running imports | External queue + worker; `202 Accepted` + `Import` resource |
| Idempotency | Mandatory `Idempotency-Key` for all import creation |
| API versioning | URI `/v1` |
| Production day | Configurable per line; one canonical config source |
| PII exposure | Full quality data only with an admin/PII scope |
| Postgres report module | Delete; it is dead and broken |
| Legacy endpoints | Keep temporarily, marked deprecated, then remove |

---

## Current-state summary

- Public surface: `POST /excel/read`, `POST /excel/upload`, `GET /daily`
  (`src/app.py`).
- No request/response schemas, versioning, auth, pagination, or idempotency.
- Ad-hoc error handling; unsupported files can return `200 null` or crash with
  `500` because `ReaderFactory.create` may return `None`.
- Ingestion is synchronous and writes directly to InfluxDB.
- `OEEService.calculate_pq` currently zeroes the Q column.
- Production-day boundaries are inconsistent (`06:00` vs `07:00`).
- The Postgres report writer imports modules and constants that do not exist.

---

## Phase overview

| Phase | Name | Priority | Depends on | Status |
|---|---|---|---|---|
| 0 | Correctness and safety fixes | P0 | None | Not started |
| 1 | `/v1` contract and resource model | P0/P1 | Phase 0 | Not started |
| 2 | Security foundation | P0 | Phase 0, parallel with Phase 1 | Not started |
| 3 | External queue and durable idempotency | P1 | Phases 1 and 2 | Not started |
| 4 | Dashboard query ergonomics | P1 | Phases 1 and 2 | Not started |
| 5 | Versioning and compatibility governance | P2 | Phases 1-4 | Not started |
| 6 | Scale, persistence, and operations | P3 | Phase 5 | Not started |

### Dependency graph

```
Phase 0 (correctness + production-day config)
   |
   +-- Phase 1 (v1 contract) --+-- Phase 3 (queue + idempotency)
   |                           +-- Phase 4 (query ergonomics)
   |
   +-- Phase 2 (auth/scopes/PII) [parallel, gates public exposure]

Phase 1 + 2 -> Phase 5 (contract governance) -> Phase 6 (scale)
```

---

## Phase 0 - Correctness and safety fixes

**Goal:** Stop silent data corruption and unhandled failures before exposing or
expanding the API.

**Depends on:** None
**Status:** Not started
**Exit gate:** No `200 null` responses, no 500s on malformed input, no
unhandled `None` reader, and production-day behavior covered by tests.

### Tasks

- [ ] **P0-1** Make `detect_file_types` raise a domain error instead of
  returning `ValueError`.
- [ ] **P0-2** Make `ReaderFactory.create` return a typed result or raise; never
  allow `None` to reach `.write()`.
- [ ] **P0-3** Fix `OEEService.calculate_pq` so the supplied quality DataFrame
  is preserved and Q is not zeroed.
- [ ] **P0-4** Add Pydantic request/response models; reject unknown fields where
  appropriate.
- [ ] **P0-5** Add one error envelope and global exception handlers with stable
  error codes and HTTP status mapping.
- [ ] **P0-6** Sanitize uploads: reject missing filenames, UUID server names,
  path containment, MIME/magic validation, size/page/sheet limits.
- [ ] **P0-7** Remove server filesystem paths and internal identifiers from
  responses.
- [ ] **P0-8** Centralize the production-day boundary in one config source and
  use it for OEE, quality, and Influx queries.
- [ ] **P0-9** Add `/healthz`, `/readyz`, and request IDs.
- [ ] **P0-10** Add HTTP-level tests with the library mocked.

---

## Phase 1 - `/v1` contract and resource model

**Goal:** Replace action-based endpoints with stable, versioned resources and
explicit DTOs.

**Depends on:** Phase 0 (may start in parallel once P0-1 to P0-5 land)
**Status:** Not started
**Exit gate:** The dashboard can integrate against `/v1` only; legacy endpoints
are deprecated but functional.

### Tasks

- [ ] **P1-1** Introduce a `/v1` router and mount all new endpoints under it.
- [ ] **P1-2** Define the `Import` resource and state machine:
  `PENDING -> RUNNING -> SUCCEEDED | FAILED | CANCELLED`.
- [ ] **P1-3** Implement `POST /v1/imports` for Telegram sources and multipart
  uploads; return `202 Accepted` with an import resource.
- [ ] **P1-4** Abstract job execution behind an interface; an in-process runner
  is allowed until Phase 3.
- [ ] **P1-5** Implement `GET /v1/imports` and `GET /v1/imports/{import_id}`.
- [ ] **P1-6** Implement the daily OEE hierarchy:
  `GET /v1/factories/{factory}/lines/{line}/machines/{machine}/daily-oee`
  and `.../{production_day}`.
- [ ] **P1-7** Add a DTO mapping layer from Vietnamese pandas columns and Influx
  fields to stable English API fields.
- [ ] **P1-8** Replace display-name tags with stable factory/line/machine IDs;
  expose display names as fields.
- [ ] **P1-9** Define the `Idempotency-Key` header and auth scopes in the
  OpenAPI contract.
- [ ] **P1-10** Delete `postgres/writers/daily_production_reports.py` and update
  `AGENTS.md`.
- [ ] **P1-11** Mark `/excel/read`, `/excel/upload`, and `/daily` deprecated with
  `Deprecation`, `Sunset`, and successor `Link` headers.

---

## Phase 2 - Security foundation

**Goal:** Ensure no public endpoint is reachable without authentication and
that PII is scope-gated.

**Depends on:** Phase 0
**Execution:** Parallel with Phase 1; must gate any external exposure.
**Status:** Not started
**Exit gate:** Dashboard flow works end-to-end with valid tokens; missing or
insufficient tokens return the standard security status codes.

### Tasks

- [ ] **P2-1** Validate OAuth2/JWT bearer tokens with cached JWKS.
- [ ] **P2-2** Implement dashboard login via Authorization Code + PKCE, or a
  backend-for-frontend if tokens must stay off the browser.
- [ ] **P2-3** Define and enforce scopes: `oee.read`, `imports.read`,
  `imports.write`, and a PII/admin scope (see open decisions).
- [ ] **P2-4** Enforce per-factory/line object-level authorization.
- [ ] **P2-5** Configure a CORS allowlist for dashboard origins.
- [ ] **P2-6** Gate full quality data behind the PII/admin scope; return
  aggregated DTOs otherwise.
- [ ] **P2-7** Add audit logging for imports and PII reads.
- [ ] **P2-8** Return `401 UNAUTHENTICATED`, `403 PERMISSION_DENIED`,
  `404 NOT_FOUND`, and `429 RESOURCE_EXHAUSTED` consistently.
- [ ] **P2-9** Add baseline rate limiting; back it with Redis in Phase 3.

---

## Phase 3 - External queue and durable idempotency

**Goal:** Make imports retry-safe, observable, and duplicate-free.

**Depends on:** Phases 1 and 2
**Status:** Not started
**Exit gate:** A timed-out client retry produces exactly one logical import; a
reused key with a different payload returns `409`.

### Tasks

- [ ] **P3-1** Select and deploy the queue/worker stack (see open decisions).
- [ ] **P3-2** Replace the in-process runner without changing the public
  contract.
- [ ] **P3-3** Require `Idempotency-Key` on all `POST /v1/imports`.
- [ ] **P3-4** Persist request fingerprint and response; replay the original
  response for duplicates.
- [ ] **P3-5** Return `409 ABORTED` for same key plus different payload.
- [ ] **P3-6** Add content-hash deduplication for uploads.
- [ ] **P3-7** Add retries with backoff, dead-letter handling, and timeouts.
- [ ] **P3-8** Add optional `POST /v1/imports/{id}:cancel`.
- [ ] **P3-9** Move rate limiting and idempotency storage to Redis.

---

## Phase 4 - Dashboard query ergonomics

**Goal:** Let the dashboard fetch ranges efficiently without over-fetching.

**Depends on:** Phases 1 and 2
**Status:** Not started
**Exit gate:** A week/month range loads with stable pagination, bounded payloads,
and correct empty/missing semantics.

### Tasks

- [ ] **P4-1** Add `start_date` and `end_date` with explicit timezone and
  inclusive/exclusive semantics.
- [ ] **P4-2** Add `page_size` and opaque `page_token` pagination.
- [ ] **P4-3** Add allow-listed `order_by` values with a stable default.
- [ ] **P4-4** Add `fields` sparse fieldsets/read masks.
- [ ] **P4-5** Return production-day metadata and configurable boundary info.
- [ ] **P4-6** Add `ETag`/`Last-Modified` and conditional `GET`.
- [ ] **P4-7** Return empty collections for empty ranges and `404` for absent
  days; never `200 null`.

---

## Phase 5 - Versioning and compatibility governance

**Goal:** Evolve the API without breaking the dashboard.

**Depends on:** Phases 1-4
**Status:** Not started
**Exit gate:** CI rejects breaking OpenAPI changes and the deprecation policy is
documented and exercised.

### Tasks

- [ ] **P5-1** Add OpenAPI snapshot/diff checks to CI.
- [ ] **P5-2** Add golden-response contract tests for key payloads.
- [ ] **P5-3** Document additive-only evolution rules.
- [ ] **P5-4** Document the deprecation and sunset policy.
- [ ] **P5-5** Align root `0.1.0` and library `1.0.0`; define a compatible
  version range.
- [ ] **P5-6** Add a changelog with migration notes.

---

## Phase 6 - Scale, persistence, and operations

**Goal:** Support production load and reduce dependence on Influx-only state.

**Depends on:** Phase 5
**Status:** Not started
**Exit gate:** Import metadata is durable, dashboards meet agreed SLOs, and load
tests are part of CI or a documented runbook.

### Tasks

- [ ] **P6-1** Persist import metadata in Postgres or Redis.
- [ ] **P6-2** Add caching for daily/monthly aggregates.
- [ ] **P6-3** Add load tests for concurrent imports and range queries.
- [ ] **P6-4** Define SLOs, dashboards, and alerting.
- [ ] **P6-5** Evaluate gRPC/protobuf only for internal high-throughput
  ingestion.

---

## Open decisions

| ID | Question | Options | Blocks | Status |
|---|---|---|---|---|
| OD-1 | Queue/worker library | RQ / Celery / Arq | Phase 3 | TBD |
| OD-2 | Identity provider | Keycloak / Auth0 / Entra ID / existing IdP | Phase 2 | TBD |
| OD-3 | Browser token flow | PKCE in SPA / backend-for-frontend | Phase 2 | TBD |
| OD-4 | Deployment target | Docker VM / Kubernetes / existing platform | Phases 2-3 | TBD |
| OD-5 | PII scope | Dedicated `quality.pii.read` / broad `admin` | Phase 2 | TBD |
| OD-6 | Production-day config storage | Props file / database / per-line config service | Phase 0 | TBD |
| OD-7 | Legacy endpoint sunset | Remove after `/v1` / one release cycle | Phase 1 | TBD |

---

## Out of scope

- Frontend dashboard implementation.
- Replacing InfluxDB or redesigning the time-series schema.
- Repairing the deleted Postgres report writer.
- gRPC for the public dashboard API.

---

## Progress rules

1. Only mark a phase `Done` after its exit gate is verified.
2. Only mark a task `[x]` after its change is merged and tested.
3. If an open decision blocks a task, mark it `[!]` and link the decision ID.
4. Keep this file updated in the same change as the implementation.
