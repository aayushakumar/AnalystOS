---
name: ambiguity-handling
version: "1.0"
description: Rules and templates for resolving ambiguous user queries
activation_conditions: [clarifier, planner, intent_classifier]
tags: [clarification, ux]
---

# Ambiguity Handling

When a user's question is unclear, under-specified, or could be interpreted in multiple ways, use these rules to decide whether to ask for clarification or proceed with a reasonable default.

---

## Core Rules

1. **Never guess a metric definition.** If the user says "sales" and you're unsure whether they mean revenue, order count, or units sold—ask.
2. **Always ask for a time range** when the question involves trends, comparisons, or changes over time and no period is specified.
3. **Never assume a segment.** If the user says "top customers" without specifying the dimension (by revenue? by order count? by recency?), ask.
4. **Resolve entity ambiguity.** If a term maps to multiple columns or tables (e.g., "date" could be order_date, ship_date, or created_at), ask which one.
5. **Clarify comparison anchors.** "How are we doing?" compared to what—last month, last year, a target?

---

## When NOT to Ask

Do **not** ask for clarification when:

- The question has a single obvious interpretation ("What was total revenue last month?").
- A reasonable default exists and is stated in the metric definitions skill (e.g., revenue always means completed orders).
- The missing detail doesn't change the answer materially (e.g., asking whether to include cents in a revenue figure).
- The user has already provided the detail earlier in the conversation—reuse context.
- Asking would feel pedantic or slow ("Did you mean calendar month or 30-day rolling?" — just use calendar month unless stated otherwise).

**Guiding principle:** Ask when the answer would be *meaningfully different* depending on the interpretation. Don't ask when it wouldn't.

---

## Clarification Templates

Use natural, conversational language. Never present raw column names to the user.

### Missing Time Range
> I can look that up! What time period are you interested in? For example: last 7 days, last month, Q4 2024, or year-to-date.

### Ambiguous Metric
> When you say "**{term}**", do you mean:
> 1. **{interpretation_1}** — {brief description}
> 2. **{interpretation_2}** — {brief description}
>
> (This matters because the numbers can be quite different.)

### Missing Segment / Dimension
> I can break that down! Would you like to see it by:
> - **{dimension_1}** (e.g., product category)
> - **{dimension_2}** (e.g., customer region)
> - **Overall** (no breakdown)

### Ambiguous Comparison
> You'd like to compare performance — what should I compare against?
> - **Previous period** (e.g., this month vs. last month)
> - **Same period last year** (YoY)
> - **A specific target or benchmark**

### Multiple Possible Entities
> The term "**{term}**" could refer to a few things in our data:
> - **{entity_1}** — {description}
> - **{entity_2}** — {description}
>
> Which one did you have in mind?

---

## Examples

### Example 1: Ambiguous — Ask

**User:** "Show me sales by region."

**Problem:** "Sales" is ambiguous (revenue? order count?), and no time range is given.

**Correct response:**
> Sure! Two quick questions:
> 1. By "sales," do you mean **total revenue** or **number of orders**?
> 2. What time period? (e.g., last month, last quarter, YTD)

### Example 2: Ambiguous — Ask

**User:** "How are our top products performing?"

**Problem:** "Top" is undefined (by revenue? by units?), "performing" is vague, no time range.

**Correct response:**
> Happy to dig into that! To get you the right data:
> 1. How should I rank "top" products — by **revenue**, **units sold**, or **order count**?
> 2. How many top products? (e.g., top 5, top 10)
> 3. What time period are you looking at?

### Example 3: Clear — Proceed

**User:** "What was the conversion rate last week?"

**Analysis:** Metric is defined in our standards, time range is provided. No ambiguity.

**Correct response:** Proceed directly to planning and SQL generation.

### Example 4: Clear — Proceed with Default

**User:** "Revenue this quarter."

**Analysis:** "Revenue" has a canonical definition. "This quarter" is clear enough. No clarification needed.

**Correct response:** Proceed directly.

---

## Priority Order

When multiple ambiguities exist, ask about all of them in a single message. Never ask one question, wait for the answer, then ask another—this feels like an interrogation. Bundle them.
