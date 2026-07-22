# PLAN_Library

Runbook and tracking for Plan Library's MongoDB Atlas Search POC on GCP.

## What is here

- [`Atlas-Search-Test-Plan.md`](./Atlas-Search-Test-Plan.md) - the working runbook
  executed by the Plan Library + MongoDB team against the lower (non-prod) Atlas
  cluster.

## Use cases in scope

| # | Use case | Atlas feature |
|---|---------|---------------|
| 1 | Lexical search on Market Mandates (must-pass) | Atlas Search |
| 2 | Filtered / faceted Plan Library UI queries | Atlas Search with filter clauses |
| 3 | Semantic similarity on mandate descriptions (stretch) | Atlas Vector Search auto-embedder (Voyage AI `voyage-4-large`) |
| 4 | Hybrid search for the Mandy chatbot (stretch) | `$rankFusion` on 8.0+ |

## Quick start

1. Confirm Atlas admin prerequisites in section 3.4.1 of the runbook (auto-embedder
   integration + Voyage AI credentials vaulted).
2. Load the sample dataset described in section 3.2 into a fresh `planlibrary_test`
   database.
3. Run sections 4-7 against the cluster, capturing results into the section 8
   performance table.
4. Fill in the section 10 reporting template and share with the steering team.

## Stack

- Atlas cluster: 7.0+ on GCP (8.0 preferred for vector + hybrid)
- Java services: JDK 17 or 21, Spring Boot 3.2+, Spring Data MongoDB 4.x
- Containerization: Docker, eventually K8s via the modernization roadmap
- Embeddings: Atlas Vector Search auto-embedder with Voyage AI `voyage-4-large`
  (no app-side embedding SDK)

## Status

- Lexical scope on Market Mandate Library is the must-pass POC for FY.
- Vector and hybrid are stretch goals that size the broader Elastic
  decommissioning opportunity.

## Owners

- Plan Library: Connor Rippley, Jignesh Patel, Rajat Bhatnagar
- MongoDB: search SME contact (add once assigned)
