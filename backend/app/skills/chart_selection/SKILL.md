---
name: chart-selection
version: "1.0"
description: Decision matrix for choosing the right visualization type
activation_conditions: [analyst]
tags: [visualization, charts]
---

# Chart Selection Guide

Use this guide to choose the correct chart type for every analytical output. The goal is clarity—pick the chart that communicates the insight with the least cognitive effort.

---

## Decision Matrix

| Data Shape | Recommended Chart | Notes |
|---|---|---|
| Single metric over time | **Line chart** | Use when showing a trend; X-axis is time |
| Comparing categories | **Horizontal bar chart** | Easier to read labels than vertical bars when category names are long |
| Ranking / Top-N | **Horizontal bar chart** (sorted) | Sort descending by value; show the metric value on or next to each bar |
| Part-of-whole (≤ 6 categories) | **Pie chart** or **donut chart** | Only when percentages are the focus; never use with >6 slices |
| Part-of-whole (> 6 categories) | **Stacked bar chart** | Group small categories into "Other" |
| Distribution of a single variable | **Histogram** | Choose sensible bin widths; avoid too many or too few bins |
| Relationship between two metrics | **Scatter plot** | Add trend line if correlation is being discussed |
| Multiple series over time | **Multi-line chart** | Limit to ≤ 5 series; use distinct colors; add a legend |
| Multiple series, emphasize total | **Stacked area chart** | Good for showing composition changes over time |
| Single KPI number | **Scorecard / Big Number** | Show the value, the comparison delta, and an arrow/color for direction |
| Two time periods compared | **Grouped bar chart** or **dual-axis line** | Clearly label which period is which |
| Funnel stages | **Funnel chart** | Show absolute count and conversion % at each stage |

---

## Anti-Patterns — Never Do These

### Pie Chart with Too Many Slices
If there are more than 6 categories, a pie chart becomes unreadable. Use a bar chart or group the smallest into "Other."

### 3D Charts
Never use 3D effects. They distort perception and add zero information. All charts should be flat/2D.

### Truncated Y-Axis
Starting the Y-axis at a non-zero value exaggerates differences. Always start at 0 unless:
- The data range is very narrow relative to the baseline (e.g., stock prices), AND
- You explicitly annotate that the axis is truncated.

### Dual Y-Axes Without Clear Labeling
Dual Y-axes are confusing. If you must use them, clearly color-code each axis to its series and add a note explaining the two scales.

### Too Many Colors
Limit to ≤ 7 distinct colors. Use a consistent color palette. If comparing current vs. previous period, use a bold color for current and a muted/lighter version for previous.

### Overloaded Charts
One chart should convey one insight. If you need to show multiple dimensions, use small multiples (faceted charts) instead of cramming everything into one plot.

---

## Annotation Rules

### When to Annotate

- **Min / Max points** on a time series when the user asks about peaks or troughs.
- **Anomalies** — any data point that deviates significantly from the trend. Call it out with a label.
- **Key events** — if a date corresponds to a known event (e.g., a promotion, a product launch), annotate it on the time axis.
- **Thresholds / targets** — if there's a goal line (e.g., "target: 5% conversion"), draw a horizontal reference line.

### When NOT to Annotate

- Don't annotate every data point — this creates clutter.
- Don't annotate if the insight is already obvious from the chart shape.

---

## Formatting Standards

- **Title:** Always include a descriptive title that states what the chart shows (e.g., "Monthly Revenue, Jan–Dec 2024").
- **Axis labels:** Always label both axes with units (e.g., "Revenue ($)", "Month").
- **Legend:** Include a legend when there are multiple series. Place it outside the plot area to avoid occlusion.
- **Number formatting:** Use thousands separators for large numbers. Use 1–2 decimal places for rates/percentages.
- **Sort order:** For categorical axes, sort by value (descending) unless there is a natural order (e.g., months, funnel stages).

---

## Vega-Lite Mapping

When generating chart specs, use these Vega-Lite mark types:

| Chart Type | `mark` | Key Encoding |
|---|---|---|
| Line chart | `line` | `x: temporal`, `y: quantitative` |
| Bar chart | `bar` | `x: nominal`, `y: quantitative` |
| Horizontal bar | `bar` | `y: nominal`, `x: quantitative` |
| Scatter plot | `point` | `x: quantitative`, `y: quantitative` |
| Area chart | `area` | `x: temporal`, `y: quantitative` |
| Histogram | `bar` + `bin: true` | `x: quantitative (binned)`, `y: count` |
| Stacked bar | `bar` | `color: nominal` + `stack: true` |
| Pie/donut | `arc` | `theta: quantitative`, `color: nominal` |
