# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Tool Inventory

Your README submission must document each tool's name, inputs, and return value. **These must exactly match your actual function signatures in `tools.py`.** Your documented interfaces will be checked against your actual function signatures in `tools.py` — if the parameter count or types contradict what's in the code, you may not receive full credit for that tool.


### `search_listings(description, size, max_price)`
**Inputs:** `description` (str) — keywords describing the item; `size` (str | None) — case-insensitive substring match against listing size, skipped if None; `max_price` (float | None) — price ceiling in USD inclusive, skipped if None.
**Returns:** List of up to 3 matching listing dicts sorted by style tag overlap with the description. Returns `[]` if nothing matches — never raises.

---

### `suggest_outfit(new_item, wardrobe)`
**Inputs:** `new_item` (dict) — a listing dict from `search_listings`; `wardrobe` (dict) — a wardrobe dict with an `"items"` key containing the user's existing pieces.
**Returns:** A string describing one complete outfit pairing the new item with specific wardrobe pieces, plus one styling tip. If the wardrobe is empty, returns a `WARDROBE_EMPTY:`-prefixed message instead — never raises.

---

### `create_fit_card(outfit, new_item)`
**Inputs:** `outfit` (str) — the suggestion string from `suggest_outfit`; `new_item` (dict) — the listing dict for the thrifted item.
**Returns:** A 1–3 sentence lowercase Instagram-style caption referencing the item's name, price, and platform. Returns a descriptive error string if `outfit` is empty or fields are missing — never raises.

---
## Planning Loop

The agent runs a conditional loop which means it does not call all three tools unconditionally. 
First it parses the user's query with regex to extract a description, size, and price ceiling. Then it calls `search_listings` and checks the result immediately. If the list is empty, it sets an error message and stops. No further tools are called. If results exist, it picks `results[0]` as the selected item and calls `suggest_outfit`. If the wardrobe is empty (detected by the `WARDROBE_EMPTY:` prefix on the response), it shows that message and stops without calling `create_fit_card`. Only if a real outfit suggestion comes back does the agent proceed to `create_fit_card`. The loop always checks what the previous tool returned before deciding whether to continue.

---
## State Management

All state lives in a single `session` dictionary initialized at the start of each interaction. It starts with the user's raw query and wardrobe, and gets written to after each tool call — `search_listings` adds `selected_item` and `search_results`, `suggest_outfit` adds `outfit_suggestion`, and `create_fit_card` adds `fit_card`. If a tool fails, it writes an `error` key instead and the loop stops. No tool re-reads the user's input or reloads data since each one receives only what the session already contains.
---

## Interaction Walkthrough

<!-- Walk through a complete interaction step by step: natural language query → each tool call (and why) → final fit card.
     Walk through this carefully — it's how graders follow your agent's reasoning without a live demo.
     Use a specific example — do not leave this as a template. -->

**User query:** "looking for a vintage graphic tee under $30"

**Step 1 — Tool called:**
- Tool: `search_listings`
- Input: `description="vintage graphic tee"`, `size=None`, `max_price=30.0`
- Why this tool: `search_listings` is always called first — it's the entry point for every interaction. The query is parsed for keywords and price ceiling before anything else runs.
- Output: Three matching listings sorted by style tag overlap. The Y2K Baby Tee ($18, Depop) ranks first and is stored as `session["selected_item"]`.

**Step 2 — Tool called:**
- Tool: `suggest_outfit`
- Input: `new_item=` Y2K Baby Tee listing dict, `wardrobe=` example wardrobe (10 items)
- Why this tool: `search_listings` returned results, so the agent proceeds. The wardrobe is non-empty, so the LLM generates a real outfit using named pieces from the user's closet.
- Output: "Pair this Y2K baby tee with your baggy dark-wash jeans and chunky white sneakers for a retro streetwear look. Layer your vintage black denim jacket on top and front-tuck the tee slightly to define your waist against the wide leg."

**Step 3 — Tool called:**
- Tool: `create_fit_card`
- Input: `outfit=` suggestion from Step 2, `new_item=` Y2K Baby Tee listing dict
- Why this tool: A valid outfit suggestion exists in the session, so the agent proceeds to generate the shareable caption.
- Output: "just thrifted this y2k butterfly tee off depop for $18 and it was made for my baggy jeans 🦋 denim jacket over top, front tuck, chunky sneakers — the full fit is locked"

**Final output to user:**
The three Gradio panels populate: the top listing panel shows the Y2K Baby Tee with price, platform, size, condition, and tags; the outfit panel shows the styling suggestion from Step 2; the fit card panel shows the caption from Step 3.


---

## Error Handling and Fail Points

<!-- For each tool, describe the specific failure mode and what your agent does in response.
     This maps to the error handling section of the rubric (F5-C1). -->

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` |No listings match the description, size, and price filters combined. |Returns `[]` without raising. The agent tells the user: "No listings matched your search — try a broader description, a different size format (e.g. 'S/M' instead of 'S'), or a higher price limit." The interaction ends here — `suggest_outfit` is never called. |
| `suggest_outfit` |`wardrobe["items"]` is an empty list. |Skips the LLM call and returns a `WARDROBE_EMPTY:`-prefixed message: "To suggest an outfit, I need to know a bit about what you already own. Tell me 2–3 pieces — for example, 'baggy jeans, white sneakers, black hoodie' — and I'll put a full look together." The interaction stops here — `create_fit_card` is never called. |
| `create_fit_card` |`outfit` is an empty or whitespace-only string. |Returns "Error: fit card unavailable — outfit description was empty. Here's the item: [title] from [platform]." without calling the LLM. The outfit suggestion from Step 2 is still shown to the user. |

---

## Spec Reflection

<!-- Answer both questions with at least 2–3 sentences each. -->

**One way planning.md helped during implementation:**
Having the planning loop written out as specific steps made it really easy to translate directly into code. I didn't have to make decisions while coding because I had already made them in the spec. It also helped me catch early that `suggest_outfit` should never get called with empty input which is something I might've missed if I'd just started coding.


**One divergence from your spec, and why:**
In my spec I wrote that the agent would "pause" if the wardrobe was empty and wait for the user to add items. That didn't work in practice because Gradio handles one request at a time and doesn't hold state between submissions. Instead the agent just shows the WARDROBE_EMPTY message in the first panel and stops, which gets the same point across.

---
## AI Tool Usage

**Instance 1 — `tools.py` implementation:**
I gave Claude the Tool 1, 2, and 3 spec blocks from `planning.md` along with the `load_listings()` and `load_wardrobe_schema()` signatures from `data_loader.py`. It generated all three function implementations. Before using them I checked that the size filter used substring matching, results were capped at 3 and sorted by tag overlap, and the empty wardrobe branch returned a sentinel string rather than raising. I kept the `WARDROBE_EMPTY:` prefix as a machine-readable sentinel so the planning loop could detect it without parsing natural language.

**Instance 2 — `agent.py` planning loop:**
I gave Claude the Architecture diagram and the State Management paragraph from `planning.md` and asked it to implement `run_agent()`. The generated code correctly branched on empty `search_results` and checked for the `WARDROBE_EMPTY` sentinel before calling `create_fit_card`. Claude's initial suggestion used an LLM call to parse the user's query — I overrode that with a regex-based `_parse_query()` function instead, since deterministic parsing is faster and doesn't cost an API call.
## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.
