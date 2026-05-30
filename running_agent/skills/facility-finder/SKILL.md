---
name: facility-finder
description: Locates runner-friendly facilities (convenience stores, cafes, restrooms, shower rooms) near the running course start point. Called after the route is confirmed.
---

# Facility Finder Skill

Searches for practical runner support facilities around the course start.
Always the **third** step in the running planner pipeline.

## Tools

- `search_nearby_facilities(location: str, type: str, radius_km: int = 3) -> dict`
  Returns: list of `facilities` each with `name`, `distance`, `note`.

## Defaults

| Parameter | Default |
|---|---|
| `type` | `"러너 편의시설"` |
| `radius_km` | `3` |

## Decision Rules

- Search around the route **start point** (same location as route planning).
- Always include stores with energy snacks, cafes with lockers/showers, and public restrooms.

## Example

```python
search_nearby_facilities(location="가평", type="러너 편의시설", radius_km=3)
```
