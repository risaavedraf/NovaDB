# How NovaDB Works

## The Problem

Traditional databases fail for AI memory:

- **SQL/MongoDB** — Exact matches only. Ask "what do I like?" and they return nothing unless you stored that exact string.
- **Vector DBs** (ChromaDB) — Understand meaning but have no structure. Flat lists of vectors with no parent-child relationships.
- **Graph DBs** (Neo4j) — Powerful relationships but require manual wiring. No automatic clustering.

NovaDB combines all three.

## The Three Layers

Every piece of knowledge lives in one of three tiers:

### MACRO — The Big Picture
Abstract concepts that span multiple domains. Think "Cloud Architectures" or "Startup Technologies". These are the gravitational centers of the knowledge graph.

### MEDIO — The Cluster
Natural groupings that emerge from semantic similarity. "AWS Services", "Google Cloud Tools". These form dynamically — you don't create them manually.

### MEMORIA — The Detail
Surgical facts. "r1cky thought Lambda was too expensive for a 5-minute process". This is where the raw knowledge lives.

## How Memories Cluster

1. You store a memory with text → Gemini converts it to a vector
2. NovaDB compares the vector against existing nodes using **cosine similarity**
3. If similarity exceeds a threshold → the new memory becomes a child of the best-match parent
4. If no parent is close enough → a new MEDIO cluster forms automatically
5. When enough MEDIOs cluster around a theme → a MACRO emerges

This is **induced hierarchy** — structure that builds itself from content.

## Temporal Decay

Memories have a `relevancia` score that decays over time:

- Fresh memories score higher
- Frequently accessed memories get a boost
- The consolidator periodically rebalances the tree based on these scores

## Search: O(√N) Guaranteed

Traditional linear search checks every node. NovaDB uses hierarchical indices:

1. Match the query against MACRO nodes first (fewest nodes)
2. Drill into the winning MACRO's MEDIOs
3. Drill into the winning MEDIO's MEMORIAS

Result: **O(√N) search time** regardless of graph size.

## Persistence

Two formats:
- **JSON** — Human-readable, good for debugging
- **MessagePack** — Binary, fast, compact for production
