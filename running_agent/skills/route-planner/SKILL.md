---
name: route-planner
description: Running route and elevation analysis. Selects a course matching the user's target distance and fitness level. Called after weather is confirmed safe.
---

# Route Planner Skill

Finds the optimal running course for a given location and distance target.
Always the **second** step in the running planner pipeline.

## Tools

- `get_route_elevation(location: str, distance: str, max_elevation_gain: str) -> dict`
  Returns: `route_name`, `start`, `destination`, `distance`, `elevation_gain`, `surface`, `difficulty`.

## Defaults

| Parameter | Default |
|---|---|
| `distance` | `"5km"` |
| `max_elevation_gain` | `"50m"` |

## Decision Rules

- Use user-supplied distance if provided; otherwise default to `"5km"`.
- Keep `max_elevation_gain` at `"50m"` unless user specifies a different limit.
- Use the confirmed (possibly rescheduled) date from the weather step.

## Example

```python
get_route_elevation(location="가평", distance="10km", max_elevation_gain="50m")
```
