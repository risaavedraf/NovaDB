# Demo Script — NovaDB

## Setup (Before Recording)

1. Start with a clean NovaDB instance
2. Open MindReader in browser at `http://localhost:8000`
3. Have a terminal ready with the NovaDB REPL or agent

## Scene 1: Empty Graph (30s)

**Narration:** "This is NovaDB — a semantic memory engine for AI agents. Right now the graph is empty."

- Show the MindReader dashboard with an empty state or single root node

## Scene 2: Storing Memories (60s)

**Narration:** "Let's feed it some knowledge and watch the hierarchy build itself."

Add memories one by one via the agent:

```
1. "My favorite band is Deftones"
2. "I also like Tool and A Perfect Circle"
3. "I went to a Deftones concert in 2024"
4. "My startup uses React and TypeScript"
5. "We deploy on AWS Lambda"
6. "Lambda was too expensive for our 5-minute jobs"
```

**What to show:** Watch nodes appear in the graph. After 3+ memories cluster, show a MEDIO forming automatically.

## Scene 3: Search — O(√N) (45s)

**Narration:** "Now let's search. The engine doesn't match text — it matches meaning."

```
User: "What music do I like?"
```

**What to show:** The graph highlights the path MACRO → MEDIO → MEMORIA. Only relevant nodes light up.

## Scene 4: Hierarchy Inspection (30s)

**Narration:** "Click any node to see its full context — origin, access count, relationships."

- Click a MEDIO node
- Show the side panel with metadata

## Scene 5: MCP Integration (45s)

**Narration:** "NovaDB works with any AI agent via MCP. Here it is powering OpenCode."

- Show agent conversation where it recalls stored memories
- Demonstrate `recordar`, `memorizar`, `analizar` tools

## Scene 6: Live Update (30s)

**Narration:** "And if we add a memory right now..."

- Type a new memory in terminal
- Watch the graph update in real-time (WebSocket or poll)

## Closing (15s)

**Narration:** "NovaDB — semantic memory that thinks in hierarchies. O(√N) search, automatic clustering, MCP-native."

- Show final graph state
- Flash the GitHub repo URL
