# Plan Library Search POC

Starter repo for evaluating MongoDB Atlas Search and Atlas Vector Search against Plan Library data.

## Includes
- Plan Library notes and search recommendations
- Sample plan and mandate data
- Atlas Search index config
- Scripts for data loading, BSON sizing, keyword search, filtered search, and vector search
- Example business queries

## Install
```bash
pip install -r requirements.txt
```

Update the connection constants at the top of each script, then run:

```bash
python scripts/inspect_document_sizes.py
python scripts/load_sample_data.py
python scripts/create_search_index.py
python scripts/keyword_search.py
python scripts/filtered_search.py
python scripts/hybrid_search.py
```

The POC will validate full-text search, filters/facets, nested benefit search, relevance, semantic/hybrid retrieval, and whether the current large plan document is the right search retrieval unit.
