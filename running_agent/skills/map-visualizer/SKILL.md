---
name: map-visualizer
description: Generates a real running course map image using Google Maps Grounding, Routes API (walking polyline), and Static Maps API. Called last in the pipeline.
---

# Map Visualizer Skill

Searches for real running venues near the location and produces a visual map.
Always the **fourth (final)** step in the running planner pipeline.

## Tools

- `search_running_course(tool_context: ToolContext, location: str, distance_km: float = 5.0) -> str`
  - Queries Gemini with Google Maps grounding for parks/trails near `location`.
  - Resolves start coordinates via Places API.
  - Computes a walking polyline via Routes API.
  - Saves a Static Maps PNG to `/tmp/running_course_map.png` for the server to serve.
  - Returns course description text + directions link.

## Defaults

| Parameter | Default |
|---|---|
| `distance_km` | `5.0` |

## Fallback Behaviour

| Condition | Behaviour |
|---|---|
| No `GOOGLE_MAPS_API_KEY` | Returns Gemini text + Maps search link only (no image) |
| Place geocoding fails | Returns text + Maps search link only |
| Polyline API fails | Shows start/end markers without path overlay |

## Output

- `/tmp/running_course_map.png` — picked up by `server.py` and forwarded to the frontend as base64.
- Directions URL for the user to open in Google Maps.

## Example

```python
search_running_course(tool_context=ctx, location="가평", distance_km=10.0)
```
