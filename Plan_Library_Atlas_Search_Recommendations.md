# Plan Library / MongoDB Atlas Search Recommendations

## Executive Summary

Plan Library is an enterprise platform for building, validating,
managing, and distributing benefit plan information. The application
ecosystem already stores benefit plan data in MongoDB and is moving from
on-premises MongoDB to MongoDB Atlas on GCP.

Search is a meaningful modernization opportunity. The current
requirements span traditional full-text search, mandate and rule
discovery, structured plan lookup, and future semantic and
natural-language experiences. Atlas Search and Atlas Vector Search can
provide these capabilities directly alongside the operational data,
reducing the need for a separate Elasticsearch search layer.

The recommended approach is to begin with the highest-value search
workflows and a deliberately scoped search index, validate the existing
document model for search, and then layer semantic and hybrid retrieval
onto the same platform.

------------------------------------------------------------------------

## 1. Current State

### Application

-   Plan Library is an enterprise asset for building and managing member
    benefit plans.
-   The ecosystem consists of roughly 15--16 applications/microservices.
-   Internal users include benefits and configuration teams across E&I
    and other business units.
-   Plan Library feeds downstream applications such as Cirrus and other
    consumers through APIs and streaming.
-   MongoDB is the primary data platform for plan structures.
-   The application is being modernized and migrated from on-premises
    MongoDB to Atlas on GCP.
-   Growth expectation is approximately 3x over five years as additional
    businesses and plan types are onboarded.
-   Plan Library is a P1 application with no tolerance for downtime.

### Existing Search

-   Parts of the application ecosystem are heavy users of Elasticsearch.
-   Elasticsearch cost is a stated concern.
-   Users want equivalent search functionality without maintaining a
    separate search platform where possible.
-   Market Mandate Library currently organizes rules with metadata, but
    rule discovery is limited.
-   Analysts need to find applicable business rules, state mandates, and
    federal mandates quickly.
-   Existing workflows rely heavily on filtering and
    exact/string-oriented lookup.
-   The team has also explored chatbot and natural-language experiences
    for retrieving plan information.

------------------------------------------------------------------------

## 2. Primary Search Use Cases

### Use Case 1 --- Traditional Plan Search

Allow users to search plan data using combinations of structured
attributes and text.

Examples:

-   Plan code
-   State
-   Product type
-   Benefit category
-   Deductible
-   Out-of-pocket values
-   Network information
-   Coverage attributes
-   Benefit descriptions

This is the most direct Elasticsearch replacement opportunity.

### Use Case 2 --- Mandate and Rule Search

Configuration analysts need to determine which rules and mandates apply
while configuring benefit plans.

Example:

> Find all Utah mandates related to copays.

Users should be able to search across:

-   State mandates
-   Federal mandates
-   Internal business rules
-   Rule descriptions
-   Mandate metadata
-   Product applicability
-   Effective dates

The system should return the most relevant rules while allowing the
analyst to constrain results using structured metadata.

### Use Case 3 --- Semantic Mandate Discovery

Users may understand the concept they are looking for without knowing
the exact terminology contained in the mandate.

Example:

> What Utah rules limit what a member pays for emergency care?

Vector and hybrid search can identify conceptually relevant mandates
while structured filters constrain retrieval to the appropriate
jurisdiction, product, dates, and rule types.

### Use Case 4 --- Natural-Language Plan Lookup

Plan Library has explored allowing business users to ask questions
rather than navigating multiple filtering screens and application tabs.

Examples:

> Give me the plan code and deductible information for this plan.

> Find Texas HMO plans with physical therapy benefits.

> Which plans have a \$4,000 individual deductible?

This experience can use Atlas Search / Vector Search as the retrieval
layer beneath an LLM or chatbot.

### Use Case 5 --- Benefit Summary / Plan Assistant

The team has explored chatbot POCs that identify plans, retrieve benefit
information, and assist with generating benefit summary PDFs.

Longer term, the same retrieval architecture could support assistance
during plan creation and configuration.

------------------------------------------------------------------------

## 3. Required MongoDB Search Capabilities

### Core Search

-   Full-text search
-   Phrase search
-   Fuzzy search
-   Autocomplete
-   Synonym support
-   Relevance scoring
-   Result highlighting
-   Compound search
-   Search across nested objects
-   Search within arrays

### Structured Search

-   Exact-match filtering
-   Faceted search
-   State/jurisdiction filtering
-   Product and plan-type filtering
-   Benefit-category filtering
-   Business-line filtering
-   Effective-date filtering
-   Numeric/range filtering
-   Boolean filtering
-   Multiple simultaneous filters

### Advanced Search

-   Vector search
-   Semantic search
-   Hybrid lexical + vector search
-   Metadata-filtered vector search
-   Natural-language retrieval
-   Retrieval for chatbot / RAG workflows

### User Experience

-   Saved searches/views
-   Autocomplete
-   Relevant result ranking
-   Matching-text highlighting
-   Filtered navigation
-   Search results that identify the matching benefit/rule rather than
    only the parent plan

------------------------------------------------------------------------

## 4. Data Model Considerations

A sample Plan Library record shows that a single plan document can
contain a substantial amount of nested information.

Representative structure:

``` text
Plan
├── planAssignmentID
├── version
├── planDetails
├── groupDetails
├── spendingAcctDetails
├── medicalDeductible
├── dentalAdultDeductible
├── dentalPedDeductible
├── medicalOutOfPocket
└── medicalBenefits[]
    ├── benefitCategory
    ├── benefitGroup
    ├── paymentLines[]
    │   ├── paymentLineDescription
    │   ├── benefitTiers[]
    │   └── limits[]
    └── ...
```

The `medicalBenefits` array can contain dozens of benefit structures,
each with nested payment lines, tiers, descriptions, limits, and output
values.

### Recommendation: Review the Search Retrieval Unit

The existing aggregate may remain appropriate for transactional plan
operations, but the optimal transactional document is not automatically
the optimal search document.

A data-model review should determine whether `medicalBenefits` should
remain embedded in the plan document or also be represented as a
separate search-oriented collection.

A potential model:

### `plans`

One document per plan/version containing:

-   `planAssignmentID`
-   `version`
-   Plan metadata
-   State
-   Product
-   Plan type
-   Organization
-   Deductible/OOP summary
-   Other plan-level attributes

### `planBenefits`

One document per logical benefit per plan containing:

-   `planAssignmentID`
-   `version`
-   State
-   Product
-   Plan type
-   `benefitCategory`
-   `benefitCategoryDisplayName`
-   `benefitGroup`
-   `paymentLines`
-   `benefitTiers`
-   `limits`
-   Searchable descriptions/output values

This provides a more precise retrieval unit for benefit search and
future vector search.

### Do Not Over-Normalize

The recommendation is **not** to create separate collections for every
payment line, tier, and limit.

A useful aggregate boundary is:

``` text
Plan
   ↓
Benefit
   ├── payment lines
   ├── tiers
   └── limits
```

Payment lines, tiers, and limits naturally belong to the benefit and can
remain embedded.

------------------------------------------------------------------------

## 5. Search Index Strategy

Avoid dynamically indexing the entire plan document by default.

The sample plan contains many fields that do not need full-text search.
Index only fields required by known search patterns.

### Likely Searchable Fields

Examples:

-   `planDetails.planCode`
-   `planDetails.product`
-   `planDetails.standard`
-   `planDetails.category`
-   `planDetails.description`
-   `planDetails.marketingName`
-   `medicalBenefits.benefitCategory`
-   `medicalBenefits.benefitCategoryDisplayName`
-   `medicalBenefits.benefitGroup`
-   `medicalBenefits.paymentLines.paymentLineDescription`
-   Benefit/limit output descriptions

### Likely Filter Fields

Examples:

-   `planAssignmentID`
-   `version`
-   `planDetails.stateAbbr`
-   `planDetails.planType`
-   `planDetails.productType`
-   `planDetails.license`
-   `planDetails.organization`
-   `planDetails.segment`
-   Effective dates
-   Coverage flags
-   Tier values
-   Benefit coverage status

The final field list should be driven by actual user queries collected
during the POC.

------------------------------------------------------------------------

## 6. Vector and Hybrid Search Strategy

Vector search should not embed an entire large plan document as a single
vector.

The plan contains multiple independent concepts. Embedding the complete
plan would create a broad representation that is poorly aligned with
precise benefit or mandate retrieval.

### Recommended Embedding Units

For plan search:

-   Individual benefit
-   Benefit description
-   Payment-line description
-   Logical benefit section

For mandate search:

-   Individual mandate
-   Rule
-   Logical mandate/rule section

Each vectorized unit should carry structured metadata that can be used
as pre-filters.

Example metadata:

``` text
planAssignmentID
version
state
productType
benefitCategory
benefitGroup
effectiveDate
```

### Hybrid Search

Hybrid search should combine:

**Lexical retrieval**

Useful when users know exact terminology such as:

> physical therapy

with:

**Semantic retrieval**

Useful when users describe the concept differently:

> rehabilitation services that help a member recover movement after an
> injury

Structured filters can then restrict results by state, product, plan
type, effective date, or other business criteria.

------------------------------------------------------------------------

## 7. Search Sizing Questions

### Data Volume

1.  What is the current total size of the collections that will be
    searched?
2.  How many plan documents exist?
3.  What is the average BSON document size?
4.  What are the P95 and P99 document sizes?
5.  How many historical versions of each plan are retained?
6.  Are historical versions searchable?
7.  What is the expected searchable data growth over the next five
    years?

### Nested Data

8.  What is the average number of `medicalBenefits` entries per plan?
9.  What is the maximum number of benefits in a plan?
10. What is the average number of payment lines per benefit?
11. What is the maximum number of tiers and limits associated with a
    benefit?

### Search Index

12. Which fields need full-text search?
13. Which fields only require exact-match filtering?
14. Which fields require faceting?
15. Which fields require range queries?
16. Which nested fields must be searchable?
17. How many Search indexes are expected?
18. Will multiple Plan Library applications use the same Search index?

### Query Workload

19. What is the expected average Search QPS?
20. What is the expected peak Search QPS?
21. How many concurrent users are expected?
22. What does a typical query look like?
23. How many filters are normally applied?
24. Are facets returned with each search?
25. How many results are normally returned?
26. Are users searching interactively while typing/autocompleting?

### Performance

27. What search latency is expected for the interactive UI?
28. Does the existing 8-second application SLA apply to Search?
29. Is there a more aggressive Search-specific target?
30. What are the expected P95/P99 latency targets?

### Update Workload

31. How frequently are plans created?
32. How frequently are plans updated?
33. How frequently do benefit structures change?
34. Are updates concentrated in batch windows?
35. How quickly must changes become searchable?

### Vector / Semantic Search

36. Is vector search required for the initial POC or a later phase?
37. Which content will be embedded?
38. What embedding model and vector dimensions will be used?
39. Will benefits be embedded individually?
40. Will mandates/rules be embedded individually?
41. What is the expected vector-search QPS?
42. Will vector queries always include metadata filters?
43. Is hybrid search expected for most semantic queries?

------------------------------------------------------------------------

## 8. POC Scope

The POC should validate business search quality and architecture rather
than simply prove that Atlas Search can return results.

### Phase 1 --- Traditional Search

Implement representative Plan Library queries using:

-   Full-text search
-   Phrase search
-   Fuzzy matching
-   Autocomplete
-   Synonyms
-   Structured filters
-   Facets
-   Relevance scoring
-   Highlighting

### Phase 2 --- Benefit Search

Demonstrate search against the deeply nested benefit data.

Representative query:

> Find Texas HMO plans that cover physical therapy and show the
> applicable visit limits.

Validate whether searching the existing plan aggregate provides the
desired result precision or whether a benefit-oriented collection
produces a better experience.

### Phase 3 --- Mandate Search

Demonstrate:

> Find Utah mandates related to copays.

Include:

-   Full-text retrieval
-   State filtering
-   Rule-type filtering
-   Highlighting
-   Relevance ranking

### Phase 4 --- Semantic / Hybrid Search

Demonstrate a concept-oriented query that does not use the exact
language in the source material.

Compare:

-   Lexical search
-   Vector search
-   Hybrid search

Evaluate relevance with business users.

### Phase 5 --- Natural-Language Retrieval

Optionally place a simple conversational interface over the search
layer.

Example:

> Show me Texas HMO plans with outpatient physical therapy and tell me
> the visit limit.

The LLM should use MongoDB retrieval results as grounded context rather
than attempting to answer from model knowledge.

------------------------------------------------------------------------

## 9. POC Success Criteria

### Functional

-   Users can search across plan and benefit content without relying on
    exact strings.
-   Users can combine text search with structured plan filters.
-   Relevant matching benefit/rule content is surfaced directly.
-   Search supports nested benefit structures.
-   Atlas Search can satisfy the targeted Elasticsearch search patterns.
-   Mandate search materially improves rule discovery.
-   Search results are understandable and explainable to business users.

### Relevance

-   Business users agree that top-ranked results are relevant.
-   Synonyms and fuzzy matching improve recall without materially
    degrading precision.
-   Hybrid search improves concept-based queries compared with lexical
    search alone.

### Performance

-   Search meets the agreed interactive latency target.
-   Search performance remains acceptable at representative concurrency.
-   Index updates become searchable within the required timeframe.

### Architecture

-   Search operates directly against MongoDB/Atlas data where
    appropriate.
-   Search indexes contain only fields required by the application.
-   Search workloads can be isolated/scaled independently where
    appropriate.
-   The POC determines whether the existing large plan aggregate or a
    benefit-oriented retrieval model is preferred.

### Business

-   Atlas Search demonstrates a viable path to reduce or eliminate
    Elasticsearch for the targeted Plan Library use cases.
-   The solution supports expected growth and onboarding of additional
    business units.
-   The architecture provides a foundation for future semantic search
    and Plan Library chatbot experiences.

------------------------------------------------------------------------

## 10. Recommended Next Steps

1.  Collect current collection statistics and BSON document-size
    distribution.
2.  Obtain representative user queries from configuration analysts and
    business users.
3.  Document the Elasticsearch queries/functionality currently used by
    Plan Library.
4.  Identify the exact fields required for text search, filtering,
    facets, and sorting.
5.  Build a deliberately scoped Atlas Search index.
6.  Benchmark representative lexical queries.
7.  Test the same benefit search against the existing aggregate and a
    benefit-oriented collection.
8.  Define relevance judgments with Plan Library business users.
9.  Add semantic/vector retrieval for mandates and benefits.
10. Test hybrid retrieval against real analyst questions.
11. Capture Search QPS, concurrency, latency, index size, and
    indexing/update rates.
12. Use POC measurements to finalize Atlas Search sizing and production
    architecture.

------------------------------------------------------------------------

## Recommended Architecture Direction

``` text
                    Plan Library Applications
                              │
                              ▼
                         MongoDB Atlas
                              │
               ┌──────────────┴──────────────┐
               │                             │
               ▼                             ▼
          Plan Collections             Search-Oriented Data
                                             │
                                  ┌──────────┴──────────┐
                                  ▼                     ▼
                             Plan Benefits        Mandates / Rules
                                  │                     │
                                  └──────────┬──────────┘
                                             ▼
                                      Atlas Search
                                             +
                                    Atlas Vector Search
                                             │
                           ┌─────────────────┴─────────────────┐
                           ▼                                   ▼
                    Search / Filter UI                  Chatbot / RAG
```

The key principle is to keep MongoDB as the system of record while
choosing retrieval units and indexes that are optimized for the actual
Plan Library search experience.
