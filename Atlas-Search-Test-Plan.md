# Plan Library Atlas Search Test Plan & Runbook

**Owner:** Plan Library + MongoDB
**Audience:** Plan Library engineering, MongoDB search SME
**Target SLA:** Search results returned in **<= 6 seconds**
**Goal:** Validate MongoDB Atlas Search as a replacement for Elasticsearch across the Plan Library ecosystem

---

## 1. Background

Plan Library is migrating from on-prem to MongoDB Atlas on GCP. Several of the 15 micro-applications
today rely on Elasticsearch (Lucene + Kibana) for full-text and faceted search across mandates,
plans and benefits. Elastic licensing, Kibana overhead and per-node fees are driving a TCO review.

This runbook is the hands-on checklist the team will execute on a lower (non-prod) Atlas cluster
to prove out Atlas Search against the existing Elastic workflows before flipping the production
traffic.

### 1.1 Search Use Cases In Scope

| # | Use case | Source app(s) | Today (Elastic) | Target (Atlas) |
|---|---------|---------------|-----------------|---------------|
| 1 | Find mandates that mention a term (e.g., "co-pay") | Market Mandate Library | Lucene keyword lookup | Atlas Search (lexical) |
| 2 | Filter plans/views across many fields (state, plan code, benefit type, network tier) | Plan Library UI | Elastic filtered query | Atlas Search with `filter` clauses |
| 3 | Semantic similarity on mandate descriptions | Market Mandate / Ideate | not done today | Atlas Vector Search |
| 4 | Natural language Q&A on plans (chatbot / GenAI) | Mandy chatbot | manual lookup | Hybrid Search (lexical + vector) |

Use case 1 is the **must-pass** for the POC. Use cases 2-4 are **stretch** goals to size the
broader Elastic replacement roadmap.

### 1.2 Out of Scope

- Data migration to Atlas (separate runbook, handled by UCP / mongosync)
- Real-time streaming ingest (Kafka)
- Atlas cluster sizing (see sizing echo-back deck)
- GenAI / LLM selection (downstream of retrieval)

---

## 2. Success Criteria

The POC is successful when **all** of the following hold:

1. At least one scenario from sections 4-7 returns a non-empty relevant result set against a
   representative Plan Library sample.
2. p95 latency for that scenario is **<= 6 seconds** end-to-end (driver round-trip + pipeline).
3. Atlas Search index build completes with no failures on the sample dataset.
4. The team can articulate for each scenario: which Atlas feature replaced which Elastic feature,
   the rough cost delta, and any necessary data-model changes.
5. We have a written recommendation of "go" or "no-go" for use cases 1-4 with rationale.

---

## 3. Prerequisites

### 3.1 Environment

- Atlas cluster: Free / M10 / M20 on GCP, **MongoDB 7.0+** (8.0 preferred if vector/hybrid is in play).
- IP allowlist for the engineer's workstation plus the Plan Library lower env.
- `mongosh` 2.x or Atlas CLI installed locally.
- `npm`/`python` driver of choice installed for the query harness (section 8).
- Database user with `readWrite` on the `planlibrary_test` database and `search maintenance`
  privilege for index management.

### 3.2 Data

Load a representative sample (we recommend 50k-500k documents, not full corpus) into a fresh
`planlibrary_test` database. Suggested collections and minimum fields:

```
plans: { _id, planCode, planName, planType, state[], networkTier, inNetwork[], outNetwork[],
         deductible, oopMax, effectiveDate, summaryText }

mandates: { _id, mandateCode, title, description, jurisdiction (federal|state),
            state, appliesTo[], sourceUrl, effectiveDate, body (long text) }

benefits: { _id, planCode, benefitCode, name, copay, coinsurance, limit,
            description, network }

businessRules: { _id, ruleCode, ruleText, appliesTo[], jurisdiction, state, tags[] }
```

The `body` / `ruleText` / `description` fields are the primary search targets. If the team has
truncated samples, that's fine - just keep them realistic enough that search relevance is
comparable.

### 3.3 Sanity checks before any test

```
mongosh "mongodb+srv://<cluster>/planlibrary_test" --eval "db.mandates.countDocuments({})"
mongosh "mongodb+srv://<cluster>/planlibrary_test" --eval "db.getSearchIndexes('mandates')"
```

If the second command returns documents, the index may already exist from an earlier run -
review before creating duplicates.

### 3.4 Spring Boot stack baseline

Plan Library runs on Spring Boot microservices that the team is actively upgrading and
modularizing. Use the same baseline in the POC apps so we are measuring what production will
look like, not a toy harness.

| Layer | Recommended | Notes |
|-------|-------------|-------|
| JDK | 17 (LTS) or 21 (LTS) | Align with the team's Java upgrade track |
| Spring Boot | 3.2.x or newer | Brings Spring Data MongoDB 4.x with vector / hybrid support |
| Spring Data MongoDB | bundled with Spring Boot | drives the `MongoTemplate` aggregations |
| Build | Maven multi-module or Gradle, per team convention | one module per micro-app |
| Containerization | Docker + (eventually) K8s via the modernization roadmap | the `JDK_BASE_IMAGE` should match prod |
| Embeddings | **Atlas Vector Search auto-embedder with Voyage AI `voyage-4-large`** | configured at the Atlas cluster level; no app-side embedding SDK or batch job needed |

Minimum dependencies for the harness project (Gradle Kotlin DSL shown, Maven equivalent is fine):

```kotlin
dependencies {
    implementation("org.springframework.boot:spring-boot-starter-data-mongodb")
    implementation("org.springframework.boot:spring-boot-starter-web")

    // NO app-side embedding SDK - Atlas auto-embedder runs the voyage-4-large model
    // server-side at index build and at query time.

    testImplementation("org.springframework.boot:spring-boot-starter-test")
    testImplementation("org.testcontainers:mongodb:<version>")
}
```

If the production code base is still on Spring Boot 2.7 / Spring Data MongoDB 3.x, call that
out in the reporting template - some `$vectorSearch` and `$rankFusion` patterns work but the
driver version and reactive support differ.

Add this to `application.yml` (per Spring profile so prod / non-prod indexes don't collide):

```yaml
spring:
  data:
    mongodb:
      uri: ${MONGO_URI:mongodb+srv://localhost/planlibrary_test}
  # NO spring.ai.* - embeddings are produced by Atlas auto-embedder, not in the app

planlibrary:
  search:
    mandate-index: ${MANDATE_INDEX:mandates_lexical}
    plan-index:    ${PLAN_INDEX:plans_filtered}
    vector-index:  ${VECTOR_INDEX:mandates_vector}
    default-limit: 20
```

The `planlibrary.search.*` keys let us flip `mandates_lexical_dev` / `mandates_lexical_prod`
without code changes - flips the recommendation from section 12 in a single PR.

### 3.4.1 Atlas auto-embedder prerequisites

Atlas auto-embedder runs `voyage-4-large` server-side. Before any scenario in section 6 or 7
will work, the MongoDB cluster admin has to:

1. Enable the **Atlas Vector Search auto-embedder** feature on the cluster (UI: Search ->
   Manage your vector indexes, or via the Atlas Admin API).
2. Configure the **Vercel / Voyage AI integration** with the team's API key (sec-team storage
   only, never in source control).
3. Confirm `voyage-4-large` is the chosen model and that the chosen index dimensions match
   `voyage-4-large` defaults (typically 1024; the model also supports 256 / 512 / 2048 if
   the team has a reason to pick differently - confirm before writing the index).
4. Document the per-document token cost - `voyage-4-large` bills per token on both index
   build and every query that auto-embeds. The engineer running the POC needs to monitor
   spend on the Atlas billing page.

The Java / Spring Boot services do NOT call Voyage directly. They pass **text** to the
`$vectorSearch` stage and Atlas does the embedding. This is the contract surface that the
sections below assume.

### 3.5 Local-dev sanity check against Testcontainers

Before touching the shared Atlas cluster, run each scenario inside a Spring Boot test against
an ephemeral MongoDB container so the team owns a deterministic harness:

```java
@SpringBootTest
@Testcontainers
class MandateSearchIntegrationTest {

    @Container
    static MongoDBContainer mongo = new MongoDBContainer(DockerImageName.parse("mongo:7.0"));

    @DynamicPropertySource
    static void props(DynamicPropertyRegistry r) {
        r.add("spring.data.mongodb.uri", mongo::getReplicaSetUrl);
    }

    @Autowired MongoTemplate mongoTemplate;
    @Autowired SearchService searchService;

    @BeforeEach
    void seed() {
        mongoTemplate.dropCollection(Mandate.class);
        mongoTemplate.insert(mandateFixtures(), Mandate.class);
        // createSearchIndex is an aggregation - run it programmatically
        mongoTemplate.execute(Mandate.class,
            collection -> collection.createSearchIndex("mandates_lexical",
                AtlasSearchIndexDefinition.builder()
                    .path("src/test/resources/indexes/mandates_lexical.json")
                    .build()));
    }

    @Test void findMandatesByCoPay_returnsRelevantDocs() {
        var results = searchService.searchMandatesByText("co-pay", 20);
        assertThat(results).isNotEmpty()
            .allSatisfy(r -> assertThat(r.title() + r.body())
                .containsIgnoringCase("co-pay"));
    }
}
```

This pattern is what we recommend committing alongside the runbook so QA can rerun scenarios
in CI without standing up Atlas themselves.

---

## 4. Scenario 1 - Lexical search on Market Mandates (must-pass)

**Why:** This is the explicit Elastic replacement driver. Analysts need to find every mandate
that mentions a string ("co-pay", "preventive care", "out-of-network").

### 4.1 Index definition

Filename: `indexes/mandates_lexical.json`

```json
{
  "name": "mandates_lexical",
  "definition": {
    "mappings": {
      "dynamic": false,
      "fields": {
        "title":       { "type": "string", "analyzer": "lucene.standard" },
        "description": { "type": "string", "analyzer": "lucene.standard" },
        "body":        { "type": "string", "analyzer": "lucene.standard" },
        "mandateCode": { "type": "string", "analyzer": "lucene.keyword" },
        "jurisdiction":{ "type": "string", "analyzer": "lucene.keyword" },
        "state":       { "type": "string", "analyzer": "lucene.keyword" },
        "appliesTo":   { "type": "string", "analyzer": "lucene.keyword" },
        "tags":        { "type": "string", "analyzer": "lucene.keyword" },
        "effectiveDate": { "type": "date" }
      }
    }
  }
}
```

Create it:

```
db.runCommand({
  createSearchIndexes: "mandates",
  indexes: [ <contents of indexes/mandates_lexical.json> ]
})
```

### 4.2 Test queries

| # | User intent | Query | Expected |
|---|------------|-------|----------|
| 1.1 | "Find mandates that mention co-pay" | `text` operator on `body`, `description`, `title` with `"co-pay"` | >=1 mandate containing the term in body or description |
| 1.2 | Same as 1.1 but typo "copay" (Lucene handles via tokenizer - confirm) | same query | should also match |
| 1.3 | Federal mandates only, mention "preventive" | compound: `filter` on `jurisdiction=federal` plus `text` for "preventive" on `description` | only federal mandates returned |
| 1.4 | Mandates tagged `pediatric` in California | `filter` on `state=CA` plus `text` on tags | only CA + pediatric mandates |
| 1.5 | Phrase search - "out-of-network" | `phrase` operator on `body` | returns mandates with that exact phrase |

#### Sample aggregation for 1.1

```javascript
db.mandates.aggregate([
  {
    "$search": {
      "text": {
        "path": ["body", "description", "title"],
        "query": "co-pay"
      },
      "highlight": { "path": ["body", "description"] }
    }
  },
  { "$limit": 20 },
  {
    "$project": {
      "_id": 1,
      "title": 1,
      "jurisdiction": 1,
      "state": 1,
      "score": { "$meta": "searchScore" },
      "highlights": { "$meta": "searchHighlights" }
    }
  }
])
```

### 4.3 Pass criteria

- All 5 test queries return relevant results (manual eyeballing - sample 10 docs each).
- p95 latency for the aggregation is **<= 6 s** on the sample cluster.
- Highlights work for query 1.1 (proves `searchHighlights` plumbing).

---

## 5. Scenario 2 - Filtered / faceted search on Plan Library UI

**Why:** Today's Plan Library UI returns filtered grids driven by Elastic queries that combine
many optional fields. We need to confirm Atlas Search can express the same queries - and that
filter clauses (which do not contribute to score) keep the pipeline fast.

### 5.1 Index definition

Filename: `indexes/plans_filtered.json`

```json
{
  "name": "plans_filtered",
  "definition": {
    "mappings": {
      "dynamic": false,
      "fields": {
        "planCode":     { "type": "string", "analyzer": "lucene.keyword" },
        "planName":     { "type": "string", "analyzer": "lucene.standard" },
        "planType":     { "type": "string", "analyzer": "lucene.keyword" },
        "state":        { "type": "string", "analyzer": "lucene.keyword" },
        "networkTier":  { "type": "string", "analyzer": "lucene.keyword" },
        "inNetwork":    { "type": "string", "analyzer": "lucene.standard" },
        "outNetwork":   { "type": "string", "analyzer": "lucene.standard" },
        "summaryText":  { "type": "string", "analyzer": "lucene.standard" },
        "deductible":   { "type": "number" },
        "oopMax":       { "type": "number" },
        "effectiveDate":{ "type": "date" }
      }
    }
  }
}
```

### 5.2 Test queries

| # | User intent | Highlights | Result expectation |
|---|------------|-----------|-------------------|
| 2.1 | Plans in CA, type HMO, deductible <= 1500 | range + filtered keyword | subset of CA HMO plans |
| 2.2 | Plans mentioning "dental" in `inNetwork`, in MN | text + filter | MN plans that include dental |
| 2.3 | All gold-tier plans effective after 2024-01-01 | date range + filter | plans with effectiveDate > 2024-01-01 |
| 2.4 | Free-text on `summaryText` with multi-field filters (planType, state) | text + filter compound | relevant subset |

Pay attention to whether `score` mode is being used - for filtered grid views we recommend
**constantScore** so score doesn't re-rank on text and the UI grid stays stable.

#### Sample aggregation for 2.1

```javascript
db.plans.aggregate([
  {
    "$search": {
      "compound": {
        "mustNot": [],
        "should": [
          {
            "range": { "path": "deductible", "lte": 1500 }
          }
        ],
        "filter": [
          { "term": { "path": "state",     "query": "CA" } },
          { "term": { "path": "planType",  "query": "HMO" } }
        ]
      }
    }
  },
  { "$limit": 50 },
  { "$project": { "planCode": 1, "planName": 1, "deductible": 1, "state": 1 } }
])
```

### 5.3 Pass criteria

- All 4 queries return sensible results; explain to product why plan X came back.
- Filter combinations execute within SLA.
- Constant-score behavior confirmed for 2.1 and 2.2 (re-running with different text shouldn't
  reorder the result set).

---

## 6. Scenario 3 - Vector / semantic similarity on mandate descriptions (stretch)

**Why:** "Find mandates similar to this one" - replaces manual clerk pattern matching.
**Requires:** Atlas 7.0+ with Vector Search enabled, **Atlas auto-embedder configured with
Voyage AI `voyage-4-large`**.

With auto-embedder the Java service never touches the embedding model. Atlas runs
`voyage-4-large` server-side at index time and at query time, and Java just passes text.

### 6.1 Data prep

1. Make sure every mandate has a non-empty `description` field. The auto-embedder uses
   this text as the source for indexing. Trim leading whitespace, normalize newlines.
2. Confirm token usage / cost falls within the Atlas budget for the POC. `voyage-4-large`
   tokenizes at index creation time, so the dataset size drives a one-time bill.
3. Document any PII / PHI fields in `description` for the security team - embeddings are
   reversible to a degree and embedding-side logging should be governed.

No app-level batch job, no `descriptionEmbedding` field on the document. Atlas stores the
computed embedding internally.

### 6.2 Index definition

Filename: `indexes/mandates_vector.json`

```json
{
  "name": "mandates_vector",
  "type": "vectorSearch",
  "definition": {
    "fields": [
      {
        "type": "vector",
        "path": "description",
        "numDimensions": 1024,
        "similarity": "cosine",
        "quantization": "scalar"
      },
      { "type": "filter", "path": "jurisdiction" },
      { "type": "filter", "path": "state" }
    ]
  }
}
```

Notes:
- `path` is the source **text** field (`description`) because Atlas auto-embeds it for us.
  In a pre-embed setup the path would point at a `descriptionEmbedding` array on the
  document - we are not doing that here.
- `numDimensions` must match what `voyage-4-large` produces at index build. The default for
  Voyage 4-series models is 1024 dims; if SecOps / FinOps asks for a different dim
  (Voyage supports 256 / 512 / 1024 / 2048), change this value before the first
  `createSearchIndexes` call. You cannot change `numDimensions` on a live index without
  rebuilding it - plan for that.
- `quantization: "scalar"` is the cost-saving default; switch to `"none"` only if the POC
  shows a recall problem.

Once the integration is enabled, Atlas makes the `queryVector` parameter irrelevant - the
query language shifts to plain text through `query`. See 6.3.

### 6.3 Test queries

| # | User intent | Approach | Expected |
|---|------------|---------|----------|
| 3.1 | "Find mandates about pediatric preventive care" | `$vectorSearch` with text `query` | top-5 mandates semantically related, even if exact words differ |
| 3.2 | Pre-filter on `jurisdiction=federal` then semantic search | `filter` clause on vector index | only federal mandates, but semantically ranked |
| 3.3 | Out-of-vocabulary case ("wellness checkup" instead of "preventive visit") | text query "wellness checkup" | should still surface mandates about preventive care - proves semantic vs lexical |

#### Sample aggregation for 3.1 (text query, auto-embedded by Atlas)

```javascript
db.mandates.aggregate([
  {
    "$vectorSearch": {
      "index": "mandates_vector",
      "path": "description",
      "query": "pediatric preventive care mandates",
      "numCandidates": 100,
      "limit": 5
    }
  },
  {
    "$project": {
      "_id": 1, "title": 1, "jurisdiction": 1,
      "score": { "$meta": "vectorSearchScore" }
    }
  }
])
```

Compare against the pre-embedder form (DO NOT use this in production - here for reference
only):

```javascript
// NOT THIS ONE - kept for clarity. With auto-embedder we don't compute queryVector.
db.mandates.aggregate([
  {
    "$vectorSearch": {
      "index": "mandates_vector",
      "path": "description",
      "queryVector": [0.012, -0.044, ... ],   // <- float array Java / Python used to compute
      "numCandidates": 100,
      "limit": 5
    }
  }
])
```

### 6.4 Pass criteria

- Top-5 results for 3.1 are semantically plausible (judged by hand against 3 representative
  queries).
- 3.3 returns the right family of mandates despite paraphrase - confirms vector relevance
  is doing the work, not a coincidence from lexical overlaps in the source data.
- Pre-filter for 3.2 works without blowing up the latency budget.
- Auto-embedder per-query token spend lands in the agreed cost ceiling - capture
  from the Atlas billing page.

---

## 7. Scenario 4 - Hybrid search for the Mandy chatbot (stretch)

**Why:** Future-state: business user types "give me the plan code and deductible data for the
Texas PPO plan", chatbot returns the right plan even if the description doesn't contain
"Texas" verbatim.

**Requires:** MongoDB 8.0+ for `$rankFusion`.

### 7.1 Pre-conditions

- `mandates_lexical` and `mandates_vector` indexes from sections 4 and 6 already exist.
- Atlas auto-embedder with `voyage-4-large` is configured (see 3.4.1).
- The `mandates` collection has populated `description` (text) - Atlas auto-embeds it.

### 7.2 Pipeline pattern

```javascript
db.mandates.aggregate([
  {
    "$rankFusion": {
      "input": {
        "pipelines": {
          "lexical": [
            { "$search": { "text": { "path": "body", "query": "<user query>" } } }
          ],
          "semantic": [
            {
              "$vectorSearch": {
                "index": "mandates_vector",
                "path": "description",
                "query": "<user query>",       // TEXT - Atlas auto-embeds via voyage-4-large
                "numCandidates": 100,
                "limit": 20
              }
            }
          ]
        }
      }
    }
  },
  { "$limit": 10 },
  {
    "$project": {
      "_id": 1, "title": 1,
      "score": { "$meta": "score" },
      "sources": { "$meta": "rankFusionDetails" }
    }
  }
])
```

Two pipeline inputs, both running per query:
- `lexical` is cheap (no Voyage calls beyond what we already pay for indexing).
- `semantic` calls `voyage-4-large` once per query to embed `<user query>` - budget for this.

### 7.3 Test queries

1. Natural language "What's the preventive care mandate for Texas fully insured plans?"
2. Mixed "Pedi preventive California HMO deductible 500".
3. Pure typo case - confirm lexical pipeline rescues it.
4. Adversarial - same query verbatim against lexical-only vs hybrid to confirm `$rankFusion`
   is actually adding value, not just running two pipelines that agree.

### 7.4 Pass criteria

- Hybrid results are at least as relevant as lexical-only on the same query.
- Sources metadata shows contributions from both pipelines (proves `$rankFusion` ran both).
- Latency remains < 6 s; flag it if hybrid is materially slower (this impacts production
  sizing AND Voyage per-query spend).
- Combined Voyage + Atlas cost fits within the agreed POC budget.

---

## 8. Performance & cost measurement

For each scenario, run 100 iterations of the canonical query and capture:

- p50 / p95 / p99 latency (driver `explain` or Atlas profiler).
- Atlas Search nodes consumed (look at `atlas process` metrics during the test window).
- Index build time and index size on disk.

Capture the cluster tier used, so we can run the same suite against M10 / M20 / M30 to draw the
cost-vs-performance curve during Phase 2.

Template:

| Scenario | Cluster | Avg latency | p95 | p99 | Index size | Build time |
|----------|---------|-------------|-----|-----|-----------|-----------|
| 1.1 | _ | _ | _ | _ | _ | _ |
| ... | _ | _ | _ | _ | _ | _ |

Cost inputs to collect for the TCO proposal:

- Atlas search node hourly rate (current pricing tier).
- Index storage charges (vector indexes are bigger).
- Engineer hours to build vs current Kibana dashboarding work.

For Spring Boot specific measurement see section 9 (Micrometer / actuator). For Atlas-side
tracing correlate the Mongo slow-query log to the Java trace id (see 9.5).

---

## 9. Spring Boot integration patterns

The Plan Library micro-apps are Java / Spring Boot services talking to MongoDB via Spring
Data. This section collects the patterns every scenario depends on, so the team is not
re-deciding them per service.

### 9.1 Connection & read preference

`application.yml` notes for the Atlas replica:

```yaml
spring:
  data:
    mongodb:
      uri: ${MONGO_URI}
      auto-index-creation: false        # disable - we manage Atlas Search indexes out of band
```

Driver options that matter for Plan Library (set via `MongoClientSettingsBuilderCustomizer`
or `spring.data.mongodb.options.*`):

- `applicationName = "planlibrary-<service>"` - shows up in Atlas profiler.
- `retryReads=true`, `retryWrites=true` - driver default since 4.x; leave on.
- Pool sizing: 50-200 per service for steady state; tune via load test. Vector flows will
  spike concurrency during scenario 3+ if the embedding step happens in-process - prefer
  batching and async.
- Server selection timeout bumped to 30 s to ride out Atlas maintenance windows.
- Socket keep-alive on (default).

Add a custom `MongoClientSettingsBuilderCustomizer` if the team needs to inject
`serverSelectionTimeoutMS`, `socketTimeoutMS`, etc.:

```java
@Configuration
public class MongoClientConfig {

    @Bean
    MongoClientSettingsBuilderCustomizer planLibraryMongoSettings() {
        return builder -> builder
            .applicationName("planlibrary-" + System.getProperty("spring.application.name"))
            .applyToSocketSettings(s -> s.connectTimeout(5, SECONDS).readTimeout(15, SECONDS))
            .applyToClusterSettings(c -> c.serverSelectionTimeout(30, SECONDS));
    }
}
```

### 9.2 Repository / service patterns

The simplest pattern - a domain service that hides the aggregation behind a typed return
value - keeps the rest of Spring Boot unaware of `$search`:

```java
public record MandateHit(String id, String title, String jurisdiction,
                         String state, double score, Map<String, List<String>> highlights) {}

public interface MandateSearchService {
    List<MandateHit> searchMandatesByText(String query, int limit);
}
```

Implementation using the imperative driver (works on Spring Boot 2.7 and 3.x):

```java
@Service
@RequiredArgsConstructor
class MandateSearchServiceImpl implements MandateSearchService {

    private final MongoTemplate mongoTemplate;
    @Value("${planlibrary.search.mandate-index}") private String mandateIndex;

    @Override
    public List<MandateHit> searchMandatesByText(String query, int limit) {
        Document searchStage = new Document("$search",
            new Document("text", new Document("path", List.of("body", "description", "title"))
                .append("query", query))
                .append("highlight", new Document("path", List.of("body", "description"))));

        AggregationOperation search = ctx -> searchStage;

        Aggregation agg = Aggregation.newAggregation(
            search,
            Aggregation.limit(limit),
            Aggregation.project("title", "jurisdiction", "state")
                .and(MetaSearchScore.values()).as("score")
                .and(MetaSearchHighlights.values()).as("highlights"));

        return mongoTemplate.aggregate(agg, "mandates", Document.class)
            .getMappedResults().stream()
            .map(this::toHit)
            .toList();
    }
}
```

For filtered views (Scenario 2) swap `text` for `compound` and build the filter array from a
Spring `Specification`-style criteria object so the controller can pass UI filter state:

```java
public List<PlanHit> findPlans(String state, String planType, Double maxDeductible) {
    List<SearchOperator> filters = new ArrayList<>();
    if (state != null)     filters.add(SearchOperator.term("state", state, planIndex));
    if (planType != null)  filters.add(SearchOperator.term("planType", planType, planIndex));
    if (maxDeductible != null)
        filters.add(SearchOperator.range("deductible", "deductible", maxDeductible, null, null, planIndex));

    SearchOperator clause = SearchOperator.compound()
        .filter(filters.toArray(new SearchOperator[0]))
        .score(ScoreConstant.builder().build());    // don't re-rank on missing text

    Aggregation agg = Aggregation.newAggregation(
        ctx -> new Document("$search", clause.getClause()),
        Aggregation.limit(50));

    return mongoTemplate.aggregate(agg, "plans", Document.class).getMappedResults()
        .stream().map(planMapper::toHit).toList();
}
```

> Spring Data MongoDB ships the `org.springframework.data.mongodb.core.query.SearchOperator`
> helper starting in 4.3 (Spring Boot 3.2). If the team is on an older Spring Data version,
> fall back to building `Document` stages by hand - do not block on upgrading the whole
> modernization track for the POC.

### 9.3 Vector search (Scenario 3)

Vector queries are not yet a first-class Spring Data builder, so the raw `Document` stage is
fine for the POC. **With Atlas auto-embedder there is no EmbeddingClient** - we hand Mongo
plain text and Atlas calls `voyage-4-large` for us:

```java
@Service
@RequiredArgsConstructor
class MandateVectorSearchService {

    private final MongoTemplate mongoTemplate;
    @Value("${planlibrary.search.vector-index}") private String vectorIndex;

    public List<MandateHit> findSimilar(String naturalLanguageQuery, int limit) {
        Document stage = new Document("$vectorSearch",
            new Document("index", vectorIndex)
                .append("path", "description")          // text field; Atlas auto-embeds
                .append("query", naturalLanguageQuery)   // text, NOT queryVector
                .append("numCandidates", 100)
                .append("limit", limit));

        Aggregation agg = Aggregation.newAggregation(
            ctx -> stage,
            Aggregation.project("title", "jurisdiction")
                .and(MetaVectorSearchScore.values()).as("score"));

        return mongoTemplate.aggregate(agg, "mandates", Document.class)
            .getMappedResults().stream().map(this::toHit).toList();
    }
}
```

If a fallback path ever needs pre-computed embeddings (e.g. for an offline batch indexing
job that does not trust the integration), keep the `queryVector` branch in a clearly named
sibling service so the production code only ever sees the text form.

### 9.4 Hybrid search (Scenario 4)

`$rankFusion` is on Spring Boot 3.x with MongoDB driver 5.x. Use the same `Document` pattern
to keep it explicit, and pass plain text to both pipelines:

```java
public List<MandateHit> hybridQuery(String userQuery, int limit) {
    Document lexical = new Document("$search",
        new Document("text", new Document("path", "body").append("query", userQuery)));

    Document semantic = new Document("$vectorSearch",
        new Document("index", vectorIndex)
            .append("path", "description")                // text; Atlas auto-embeds
            .append("query", userQuery)                     // text, NOT queryVector
            .append("numCandidates", 100)
            .append("limit", 20));

    Document rankFusion = new Document("$rankFusion", new Document("input",
        new Document("pipelines", new Document()
            .append("lexical", List.of(lexical))
            .append("semantic", List.of(semantic)))));

    Aggregation agg = Aggregation.newAggregation(
        ctx -> rankFusion,
        Aggregation.limit(limit),
        Aggregation.project("title")
            .and(MetaScore.values()).as("score"));

    return mongoTemplate.aggregate(agg, "mandates", Document.class)
        .getMappedResults().stream().map(this::toHit).toList();
}
```

The semantic pipeline makes one Voyage call per query. Track this in the metrics tag
(`planlibrary.search.embed.calls`) so the team has a true cost-per-search number for the
production rollout.

### 9.5 Metrics and SLA enforcement

Atlas gives us most of what we need for free, so the JVM-side instrumentation should stay
thin:

- **Atlas Real Time Metrics** (cluster view -> Search) - per-second
  `SEARCH_LATENCY_MS`, `SEARCH_REQUESTS`, and p95/p99 percentiles broken down by index.
  This is the source of truth for the 6-second SLA on the runbook.
- **`system.profile` collection** - turn on `db.setProfilingLevel(2)` on the lower cluster
  during the POC and pull any search-driven aggregation that breaches SLA. Filter on
  `command.$search` to ignore non-search traffic.
- **Mongo driver metrics** - the Java driver publishes command timings via Micrometer
  (`mongodb.driver.command`) as long as a `MeterRegistry` bean exists in the context.
  No `Timer` wrapper around each search call is needed; the driver already times the
  round trip.

The only thing worth adding on the app side is an Atlas Alert on
`SEARCH_LATENCY_MS.p95 > 6000` for the `mandates_lexical` index during the POC window.

If your observability team already requires application-side metrics, the minimum useful
shape is:

```yaml
management:
  metrics:
    tags:
      service: ${spring.application.name}
      cluster: ${ATLAS_CLUSTER_PROFILE:dev}
    mongo:
      command:
        enabled: true
```

That's it - no `Timer`, no `Tracer`, no `traceId`-in-aggregation-comment trickery. Crash
any of those and Atlas Real Time Metrics plus a quick `system.profile` pull gives you the
same answer with one fewer moving part.

### 9.6 Testing strategy in Spring Boot

Layer the testing so we are not blocked on a live Atlas cluster:

1. **Unit** - mock the `MongoTemplate` and assert the `$search` / `$vectorSearch` Document
   shape via `ArgumentCaptor`. Critical: protect against accidental drift between repo and
   production.
2. **Slice** - `@DataMongoTest` against an in-memory `Flapdoodle` Mongo (NOT enough for
   `$search` - the engine is server-side). Confirm the aggregation is at least well-formed.
3. **Integration with Testcontainers** - see section 3.5 above. Use `mongo:7.0` image; if the
   team needs vector tests, switch to `mongo:8.0` and pre-create the index in `@BeforeAll`.
4. **End-to-end against the shared dev cluster** - the loop defined in section 8. Runs as
   a JMH or Gatling scenario, not as a JUnit test, so it doesn't gate the build.

### 9.7 Containerization & modernization alignment

The team is mid-way through containerization. The Atlas Search POC should not block on K8s,
but the Spring Boot fat-jar should be:

- Built with the layered Jar / Docker Spring Boot buildpacks so reload cycles during the
  POC stay short.
- Connected to Atlas via the UCP service mesh / private endpoint - never from the public
  internet. The connection string belongs in the cluster secret store, not in YAML.
- `spring.data.mongodb.uri` should NOT use TLS-disabled mode anywhere. Modernization track
  will tighten this for prod regardless.

### 9.8 Backend processing budget note

The SLAs on the table are 8-second API response and 30-second backend processing. Atlas
Search p95 of <= 6 s leaves room for the orchestration layer (Spring MVC, JSON marshalling,
authorization filter). Confirm that the orchestration layer adds < 1 s under load before
flipping use case 1 in production.

---

## 10. Reporting template

After running sections 4-9, fill this in and share with the steering team:

```markdown
## POC outcome: Atlas Search for Plan Library

### Use case status
- [ ] 1 - Lexical on mandates: GO / NO-GO - <reason>
- [ ] 2 - Filtered/faceted: GO / NO-GO - <reason>
- [ ] 3 - Vector semantic: GO / NO-GO - <reason>
- [ ] 4 - Hybrid (chatbot): GO / NO-GO - <reason>

### Spring Boot readiness
- Version of JDK / Spring Boot / Spring Data MongoDB we certified against
- Vector / hybrid scenarios that required upgrading past current production baseline
- Open issues with auto-index creation, slow-query profiler correlation

### Where Atlas wins over Elastic
- <bullet>

### Where Atlas loses vs Elastic
- <bullet>

### Data model changes needed
- <bullet>

### Cost delta estimate
- <bullet>

### Go / no-go recommendation
- <one paragraph>
```

---

## 11. Reference commands

List existing indexes before creating new ones:

```
db.getSearchIndexes("mandates")
db.<collection>.aggregate([{ "$indexStats": {} }])
```

Drop an index if a test needs to be re-run cleanly:

```
db.runCommand({ "dropSearchIndex": "mandates", "id": "mandates_lexical" })
```

Profile a slow query:

```
db.setProfilingLevel(2)
db.system.profile.find({ "command.$search": { $exists: true } }).sort({ ts: -1 }).limit(5)
```

---

## 12. Open questions / follow-ups

- Embedding model: **decided - `voyage-4-large` via Atlas auto-embedder.** (Was open in v1
  of this runbook.)
- Atlas admin action items: who configures the Voyage AI integration in the Atlas
  cluster, and which credentials vault is the API key parked in?
- Voyage dimensions: confirm 1024 (default) vs 256 / 512 / 2048 once FinOps weighs in. The
  vector index `numDimensions` must be set correctly on first build; rebuilding is
  expensive once we hold prod data.
- Are there any PII / HIPAA fields in `mandates.description` that need redaction before
  embedding? Auto-embedder sends the source text to Voyage - confirm with Security what is
  acceptable to ship.
- Confirm Atlas tier budget for the POC - free / M10 / M20.
- Per-query Voyage cost ceiling: agree in writing before the hybrid scenario runs, so the
  load test doesn't generate a surprise bill.
- Naming convention for indexes so both prod and non-prod indexes don't collide.
- Who owns the elastic decommissioning checklist once a use case flips to Atlas Search?
- Spring Boot / Spring Data baseline current prod (2.7? 3.x?) so the POC targets the right
  driver generation - especially relevant for vector / hybrid which require driver 5.x.
- Modularity plan: will the search service live in a shared library module each app pulls in,
  or per-app copy? Affects how we ship the test `SearchService` interface.
- Embedding-call tracing: how do we surface `voyage-4-large` per-call timing alongside the
  Atlas p95 metrics? `planlibrary.search.embed.calls` counter is a starting point but the
  team should pick the official approach.
