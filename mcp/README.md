# Benzene Grid MCP

Ask Claude (or any MCP client) about the Great Britain grid connection queue, substation by substation.

- Who is queuing at a substation, for how many MW, and until when
- Which connection dates moved in the last few weeks, later or earlier
- Transmission connection points near a location
- Local distribution network headroom near a location
- Great Britain totals, Gate 1 and Gate 2

Data comes from NESO's Transmission Entry Capacity (TEC) register, Benzene's weekly copies of it (so we can see dates move), and network operators' published headroom data. It refreshes when NESO publishes a new register. Every site also has a public page at https://grid.benzene-group.com.

## Install

Claude Code:

```
claude mcp add benzene-grid -- uvx --from "git+https://github.com/Benzene-Group/benzene-data#subdirectory=mcp" benzene-grid-mcp
```

Claude Desktop or any client that takes a JSON config:

```json
{
  "mcpServers": {
    "benzene-grid": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/Benzene-Group/benzene-data#subdirectory=mcp", "benzene-grid-mcp"]
    }
  }
}
```

Needs `uv` (https://docs.astral.sh/uv/). No API key.

## Try asking

- "What's queued at Walpole 400kV and when?"
- "Which grid connection dates moved later in the last four weeks?"
- "What transmission substations are within 30 km of 52.75, 0.2, and how much local headroom is there?"

## Tools

| Tool | What it returns |
|---|---|
| `queue_summary` | GB totals from the latest register |
| `search_sites` | Connection points matching a name |
| `get_site_queue` | Every project at one site, plus date moves |
| `recent_date_moves` | Dates that moved in the last N weeks |
| `sites_near` | Connection points near a latitude and longitude |
| `local_headroom` | Distribution headroom near a latitude and longitude |

## Notes

Information only, not engineering, legal or investment advice. Locations are approximate. Not every network operator's headroom is included yet.

Need a written view on a specific site, or alerts when a queue changes? Benzene does screening reports and queue watch: https://www.benzene-group.com/pricing.html or info@benzene-group.com.

Data licences: NESO Open Data Licence; operators' headroom data under their stated licences (credited in each response). Code: MIT.
