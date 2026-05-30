---
name: weather
description: Running-day weather forecasting. Returns rain probability, temperature, and running condition assessment. Triggers automatic rescheduling if rain_probability ≥ 0.5.
---

# Weather Skill

Provides weather forecasts to determine whether a planned run is safe.
Always the **first** step in the running planner pipeline.

## Tools

- `get_weather_forecast(location: str, date: str) -> dict`
  Returns: `rain_probability`, `forecast`, `temperature`, `running_condition`.

## Decision Rules

| rain_probability | Action |
|---|---|
| < 0.5 | Proceed to route planning |
| ≥ 0.5 | Reschedule to "다음 주말", call `get_weather_forecast` again |

## Example

```python
get_weather_forecast(location="가평", date="이번 주말")
# → rain_probability: 0.70 → reschedule
get_weather_forecast(location="가평", date="다음 주말")
# → rain_probability: 0.10 → proceed
```
