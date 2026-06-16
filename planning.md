# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
It searches the mock listings dataset and returns up to 3 items that match the users' description, size and the price ceiling. The results are then ranked by the style tag overlap with the users' description so the most relevant items appears first.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): Text description of what the user is looking for. Matched (not case sensitive) against each listings' title, description and style tags 
- `size` (str): The users' size. It's case sensitive (substring) that matches against the listing's size field. If None, then the string filter is skipped entirely.
- `max_price` (float): Maximum price in US Dollars. If None, then no price filter is applied 

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
It will return a list of up to 3 listing dicts, each containing all original fields from"
     listings.json: id, title, description, category, style_tags, size, condition, price, colors, brand and platform.
The list is sorted descending by the number of style_tags that overlap with keywords extracted from the description.
Then we return an empty list [] if no listings pass all filters. 



**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
If the returned list is empty then the agent should not call any tools. It responds to the user by saying: 'NO listings matched your search-try a broader description, a different size format (ex: S/M instead of S), or a higher price limit'. The session will end there.

---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Given a specific thrifted item and the users' wardrobe, the tool will suggest one complete outfit by pairing the new item with a compatible wardrobe piece. 
The compatibility is determined by overlapping the style_tags and non-clashing colors

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): A single listing dict as returned by search_listings (all fields present: title, style_tags, colors, category etc.).
- `wardrobe` (dict): A wardrobe dict with an 'items'  key containing a list of wardrobe item dicts, each with id, name, category, colors, style_tags, and optional 'notes'. It comes from get_example_wardrobe() or get_empty_wardrobe().

**What it returns:**
<!-- Describe the return value -->
A string describing one complete outfit: which wardrobe pieces to pair with the new item, why they work together, and one specific styling tip.


**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
If `wardrobe["items"]` is an empty list, the agent does not attempt to generate an outfit. Instead it responds: "To suggest an outfit, I need to know a bit
about what you already own. Tell me 2–3 pieces from your wardrobe, for example, 'baggy jeans, white sneakers, black hoodie', and I'll put a full look together." The session pauses to wait for user input. The create_fit_card is not called until a valid outfit suggestion exists.
---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Generates a short, shareable outfit caption in the style of a real Instagram post: lowercase, casual, specific to the item and outfit. Produces a
different result for different inputs.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str):The outfit suggestion string returned by suggest_outfit.
- `new_item` (dict): The listing dict for the thrifted piece, used to pull specific details like price, platform, title, and colors.

**What it returns:**
<!-- Describe the return value -->
A single string of 1–3 sentences, lowercase, written in first person, that reads like something a real person would post. References the specific item, price, and platform. 

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
If `outfit` is an empty string or `new_item` is missing required fields (title, price, platform), the agent skips the fit card and instead
returns the outfit suggestion text directly with a note: "Here's how I'd style it — (fit card unavailable due to incomplete item data)."
---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
After receiving the user's query, the agent extracts three inputs from natural
language: `description`, `size` (optional), and `max_price` (optional). It then runs the following conditional logic:

1. Call `search_listings(description, size, max_price)`.
   - If result is `[]`: set `session["error"] = "no_listings"`, return the
     no-results message to the user, and stop. Do not proceed.
   - If result is non-empty: set `session["selected_item"] = result[0]`,
     set `session["search_results"] = result`, and continue.

2. Call `suggest_outfit(session["selected_item"], session["wardrobe"])`.
   - If `session["wardrobe"]["items"]` is `[]`: set
     `session["error"] = "empty_wardrobe"`, return the wardrobe-needed message,
     and pause. Do not call `create_fit_card`.
   - If outfit string is returned: set `session["outfit"] = outfit_string`
     and continue.

3. Call `create_fit_card(session["outfit"], session["selected_item"])`.
   - If fit card is returned: set `session["fit_card"] = fit_card_string`.
   - If fit card fails: fall back to returning `session["outfit"]` directly
     with the incomplete-data note.

4. Return the full session output to the user: top search result summary,
   outfit suggestion, and fit card (or fallback).

The loop does not retry automatically — it fails forward with a message.

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
All state is stored in a single `session` dictionary that is initialized at
the start of each interaction. It starts with the user's raw query and their
wardrobe, and gets written to after each tool call — `search_listings` adds
`selected_item` and `search_results`, `suggest_outfit` adds `outfit`, and
`create_fit_card` adds `fit_card`. If a tool fails, it writes an `error` key
instead and the loop stops. No tool re-reads the user's input or calls the
data loader directly — each one receives only what the session already contains.
---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query |"No listings matched your search — try a broader description, a different size format (e.g. 'S/M' instead of 'S'), or raising your price limit." Session ends.  |
| suggest_outfit | Wardrobe is empty |"To suggest an outfit, I need to know a bit about what you already own. Tell me 2–3 pieces — for example, 'baggy jeans, white sneakers, black hoodie' — and I'll put a full look together." Session pauses.  |
| create_fit_card | Outfit input is missing or incomplete |Returns the outfit suggestion text directly with a note: "Here's how I'd style it — (fit card unavailable due to incomplete item data)." | 

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     Use ASCII art or a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html).
     Do NOT embed an image — graders need to read your diagram directly in the file;
     an embedded image or screenshot cannot be evaluated.
     You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->




```
User query (natural language)
    │
    ▼
┌─────────────────────────────────────────┐
│             Planning Loop               │
│  Parse: description, size, max_price    │
│  Init: session = {query, wardrobe}      │
└──────────────────┬──────────────────────┘
                   │
                   ▼
    search_listings(description, size, max_price)
          │                    │
    results == []         results = [item, ...]
          │                    │
          ▼                    ▼
       [STOP]         session["selected_item"] = results[0]
  "No listings        session["search_results"] = results
   found. Try                  │
   adjusting."                 ▼
                suggest_outfit(selected_item, wardrobe)
                      │                  │
              wardrobe empty         outfit = "..."
                      │                  │
                      ▼                  ▼
                  [PAUSE]       session["outfit"] = outfit
             "Tell me a few             │
              pieces you own."          ▼
                      create_fit_card(outfit, selected_item)
                              │                 │
                         card fails         card = "..."
                              │                 │
                              ▼                 ▼
                      return outfit     session["fit_card"] = card
                      + "(fit card              │
                       unavailable)"            ▼
                                       Return to user:
                                       • Top search result
                                       • Outfit suggestion
                                       • Fit card caption
```
---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

**Milestone 4 — Planning loop and state management:**

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->

**Step 3:**
<!-- Continue until the full interaction is complete -->

**Final output to user:**
<!-- What does the user actually see at the end? -->
