# FitFindr 🛍️

FitFindr is a tool-using agent that helps you shop secondhand. You describe what
you're looking for in plain English; FitFindr searches a mock listings dataset,
picks the best match, styles it against your wardrobe, and writes a shareable
"fit card" caption for the find — all in one pass.

> **Example:** *"I'm looking for a vintage graphic tee under $30."* → finds a
> matching tee → suggests pairing it with your baggy jeans and chunky sneakers →
> writes an Instagram caption mentioning the price and platform.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file in the repo root (never commit it — it's gitignored):

```
GROQ_API_KEY=your_key_here
```

Get a free key at [console.groq.com](https://console.groq.com). Two of the three
tools call Groq's `llama-3.3-70b-versatile` model.

## Running

```bash
python app.py          # launch the Gradio UI (URL printed in terminal)
python agent.py        # run the CLI happy-path + no-results demo
python -m pytest tests/   # run the tool tests
```

---

## Tool Inventory

### 1. `search_listings(description, size, max_price) -> list[dict]`

| | |
|---|---|
| **Inputs** | `description` (`str`) — keywords describing the item; `size` (`str \| None`) — size filter, case-insensitive substring match (`"M"` matches `"S/M"`), or `None` to skip; `max_price` (`float \| None`) — inclusive price ceiling, or `None` to skip |
| **Output** | `list[dict]` — matching listing dicts sorted by relevance (best first). Each dict has `id, title, description, category, style_tags, size, condition, price, colors, brand, platform`. Returns `[]` when nothing matches — never raises. |
| **Purpose** | Filter and rank the mock dataset. Applies the price and size filters first, then scores each remaining listing by keyword overlap between `description` and the listing's title/description/category/style_tags, drops zero-score items, and sorts descending. |

### 2. `suggest_outfit(new_item, wardrobe) -> str`

| | |
|---|---|
| **Inputs** | `new_item` (`dict`) — a listing dict (the item being considered); `wardrobe` (`dict`) — wardrobe with an `items` list of pieces (each with `name`, `category`, etc.); may be empty |
| **Output** | `str` — 1–2 outfit suggestions. With a populated wardrobe it names specific owned pieces; with an empty wardrobe it gives general styling advice. Always a non-empty string. |
| **Purpose** | Turn a found item into a wearable look using the user's actual closet. Calls the LLM with a wardrobe-aware prompt. |

### 3. `create_fit_card(outfit, new_item) -> str`

| | |
|---|---|
| **Inputs** | `outfit` (`str`) — the suggestion string from `suggest_outfit`; `new_item` (`dict`) — the listing dict for the find |
| **Output** | `str` — a 2–4 sentence casual OOTD caption mentioning the item name, price, and platform once each. If `outfit` is empty/whitespace/`None`, returns a descriptive error string instead — never raises. |
| **Purpose** | Generate a shareable, post-ready caption. Uses LLM temperature `0.9` so the output varies across runs and inputs. |

---

## How the Planning Loop Works

`run_agent(query, wardrobe)` in `agent.py` is the planning loop. It is **not** a
fixed pipeline — its branches depend on what each tool returns.

1. **Initialize** a session dict (`_new_session`) that holds the query, parsed
   params, tool results, and an `error` slot.
2. **Parse** the natural-language query with regex: extract a `max_price` from a
   `$NN` token, a `size` from a `size <X>` token, and treat the remaining text as
   the `description`. Store all three in `session["parsed"]`.
3. **Search** via `search_listings(...)` with the parsed params; store the list
   in `session["search_results"]`.
4. **Branch on the result** — this is the decision point:
   - **Empty results** → set `session["error"]` to a helpful message and
     **return early**. `suggest_outfit` and `create_fit_card` are never called,
     so `fit_card` stays `None`.
   - **Non-empty** → set `session["selected_item"] = results[0]` and continue.
5. **Suggest outfit** with the selected item + wardrobe → `outfit_suggestion`.
6. **Create fit card** with that suggestion + selected item → `fit_card`.
7. **Return** the completed session.

Because step 4 short-circuits, the agent behaves differently for a query that
matches nothing (one tool, then stop) versus one that matches (all three tools).

---

## State Management

A single **session dict**, created per interaction by `_new_session()`, is the
one source of truth. Each step writes its output back into the session, and later
steps read from it — the user never re-enters anything.

| Key | Written by | Read by |
|---|---|---|
| `query` | entry point | parser |
| `parsed` (`description/size/max_price`) | parser | `search_listings` |
| `search_results` | `search_listings` | the empty-result branch |
| `selected_item` | loop (`results[0]`) | `suggest_outfit`, `create_fit_card` |
| `outfit_suggestion` | `suggest_outfit` | `create_fit_card` |
| `fit_card` | `create_fit_card` | UI |
| `error` | any failed step | UI (shown instead of results) |

The found listing flows from `search_listings` → `selected_item` →
`suggest_outfit` → `create_fit_card` without re-entry. `app.py` reads the final
session and maps `selected_item`, `outfit_suggestion`, and `fit_card` to the three
UI panels (or shows `error` in the first panel if set).

---

## Error Handling Strategy

Each tool owns its failure mode and degrades gracefully rather than crashing.

| Tool | Failure mode | Response |
|---|---|---|
| `search_listings` | No listing matches the query | Returns `[]`; the loop sets `session["error"]` = *"No items found matching your criteria. Try widening your price range or search terms."* and stops before styling. |
| `suggest_outfit` | Wardrobe has no items | Detects `wardrobe["items"] == []` and switches to a general-styling prompt; still returns useful advice. |
| `create_fit_card` | `outfit` is empty / whitespace / `None` | Returns *"Error: Could not generate a caption because the outfit suggestion failed or is empty."* instead of calling the LLM or raising. |

**Concrete example (tested):** querying `"designer ballgown size XXS under $5"`
yields zero matches. `search_listings` returns `[]`, the loop sets `error` and
returns early, and `session["fit_card"]` stays `None` — confirmed by the
no-results case in `agent.py` and `tests/test_tools.py::test_search_listings_failure_mode`.
The UI shows the "No items found…" message in the listing panel and leaves the
outfit and fit-card panels empty.

---

## Spec Reflection

**One way the spec helped:** Writing the Tool 1–3 blocks in `planning.md` before
coding forced me to fix each function's signature, return type, and failure mode
up front. Implementation became transcription — e.g. "return `[]`, don't raise"
and "guard empty outfit, return a string" were decided on paper, so the tools
matched the agent's expectations the first time they were wired together.

**One way implementation diverged:** The plan treated query parsing as a clean
extraction of `description / size / max_price`. In practice, regex on a verbose
sentence leaves conversational filler in the `description`, so I added cleanup
steps (stripping the matched price/size phrases and a leading "looking for a")
to keep the search keywords focused. The branching logic matched the plan
exactly; only the parsing needed more real-world handling than the spec implied.

---

## AI Usage

**1 — Implementing the tools (Milestone 3).** I gave Claude each tool's
`planning.md` block (inputs, return value, failure mode) one at a time and asked
it to implement the function in `tools.py` using `load_listings()` for the data.
It produced the keyword-scoring filter and the two Groq calls. I reviewed each
against the spec before trusting it: I confirmed `search_listings` filtered by all
three params and returned `[]` (not `None`) on no match, and that the empty-outfit
guard in `create_fit_card` ran *before* the API call. I raised `create_fit_card`'s
temperature to `0.9` so repeated runs vary, per the spec.

**2 — Wiring the planning loop (Milestone 4).** I gave Claude the Architecture
diagram plus the Planning Loop and State Management sections and asked it to
implement `run_agent()`. The first version called all three tools in sequence; I
overrode it to add the early-return branch on empty `search_results` so the agent
responds to context instead of running a fixed pipeline, and made sure every
intermediate value was written back into the session dict rather than passed via
local variables.
