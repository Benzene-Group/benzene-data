"""Benzene Grid MCP server: the Great Britain grid connection queue, by substation.

Data: https://grid.benzene-group.com/api/queue.json (NESO TEC register, Benzene's weekly copies,
network operators' published headroom data). Refreshed when NESO publishes a new register.
"""
import json, math, time, urllib.request
from mcp.server.mcpserver import MCPServer

FEEDS = ["https://grid.benzene-group.com/api/queue.json",
         "https://raw.githubusercontent.com/Benzene-Group/benzene-data/main/docs/api/queue.json"]
FOOT = ("Source: NESO TEC register via Benzene (benzene-group.com). Information only, not engineering, legal or investment advice. "
        "For a written screening report on a specific site, or alerts when this queue changes, see https://www.benzene-group.com/pricing.html")
mcp = MCPServer("benzene-grid")
_cache = {"t": 0, "d": None}


def data():
    if _cache["d"] and time.time() - _cache["t"] < 6 * 3600:
        return _cache["d"]
    last = None
    for u in FEEDS:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "benzene-grid-mcp/0.1"})
            with urllib.request.urlopen(req, timeout=30) as r:
                _cache.update(t=time.time(), d=json.load(r))
                return _cache["d"]
        except Exception as e:  # try the next mirror
            last = e
    raise RuntimeError(f"Could not load the Benzene queue feed: {last}")


def _km(a1, o1, a2, o2):
    p = math.pi / 180
    h = math.sin((a2 - a1) * p / 2) ** 2 + math.cos(a1 * p) * math.cos(a2 * p) * math.sin((o2 - o1) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def _find(site):
    q = site.lower().strip()
    S = data()["sites"]
    exact = [s for s in S if s["name"].lower() == q or s["short"].lower() == q or s["slug"] == q]
    return exact or sorted([s for s in S if q in s["name"].lower()], key=lambda s: -s["queued_mw"])


def _brief(s):
    return {k: s[k] for k in ("name", "to", "queued_mw", "connected_mw", "gate2_mw", "url")} | {"projects": len(s["projects"])}


@mcp.tool()
def queue_summary() -> dict:
    """Great Britain totals from the latest NESO TEC register: projects, MW queued and connected, Gate 1 and Gate 2 split."""
    d = data()
    return {"register_date": d["register_date"], "totals": d["head"], "note": FOOT}


@mcp.tool()
def search_sites(query: str, limit: int = 10) -> dict:
    """Find grid connection points (substations) by name, e.g. 'Walpole' or 'Grimsby West'. Returns MW waiting and a link per site."""
    hits = sorted(_find(query), key=lambda s: -s["queued_mw"])[:max(1, min(limit, 50))]
    return {"register_date": data()["register_date"], "matches": [_brief(s) for s in hits], "note": FOOT}


@mcp.tool()
def get_site_queue(site: str) -> dict:
    """Everything queued at one connection point: each project, customer, MW, contracted date, stage and Gate, plus date moves of a month or more since our weekly copies began."""
    hits = _find(site)
    if not hits:
        return {"error": f"No connection point matches '{site}'. Try search_sites first."}
    s = hits[0]
    mv = [m for m in data()["moves"] if m["site"] == s["name"]]
    return {"register_date": data()["register_date"], "site": s, "date_moves": mv,
            "other_matches": [h["name"] for h in hits[1:6]], "note": FOOT}


@mcp.tool()
def recent_date_moves(weeks: int = 4, min_months: float = 1.0, direction: str = "any") -> dict:
    """Connection dates that moved in NESO's register in the last N weeks. direction: 'later', 'earlier' or 'any'."""
    d = data()
    import datetime as dt
    since = (dt.date.today() - dt.timedelta(weeks=max(1, min(weeks, 52)))).isoformat()
    out = [m for m in d["moves"] if m["week"] >= since and abs(m["months"]) >= min_months
           and (direction == "any" or (direction == "later") == (m["months"] > 0))]
    return {"since": since, "count": len(out), "moves": out[:200], "note": FOOT}


@mcp.tool()
def sites_near(lat: float, lon: float, radius_km: float = 30) -> dict:
    """Transmission connection points near a location, nearest first, with MW waiting. Locations are approximate."""
    out = []
    for s in data()["sites"]:
        if s["lat"] is None:
            continue
        k = _km(lat, lon, s["lat"], s["lon"])
        if k <= radius_km:
            out.append(_brief(s) | {"distance_km": round(k, 1)})
    return {"sites": sorted(out, key=lambda r: r["distance_km"])[:25], "note": FOOT}


@mcp.tool()
def local_headroom(lat: float, lon: float, radius_km: float = 15) -> dict:
    """Distribution substations near a location with published generation and demand headroom (MW), from network operators' open data. Not every operator is covered."""
    d = data()
    f = d["headroom_fields"]
    out = []
    for r in d["headroom"]:
        k = _km(lat, lon, r[4], r[5])
        if k <= radius_km:
            out.append(dict(zip(f, r)) | {"distance_km": round(k, 1)})
    return {"substations": sorted(out, key=lambda r: r["distance_km"])[:25], "credits": d["headroom_credits"], "note": FOOT}


def main():
    mcp.run()


if __name__ == "__main__":
    main()
