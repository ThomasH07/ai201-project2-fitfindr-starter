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
 Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): Keywords describing what the user is looking for (e.g., "vintage graphic tee").
- `size` (str): Size string to filter by, or None to skip size filtering. Matching is case-insensitive (e.g., "M" matches "S/M").
- `max_price` (float): Maximum price (inclusive), or None to skip price filtering.

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
A list of matching listing dicts, sorted by relevance (best match first). Returns an empty list if nothing matches — does NOT raise an exception.

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
FitFindr tells the user what to try differently and stops — it does not call suggest_outfit with empty input.
---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.
**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): A listing dict (the item the user is considering buying).
- `wardrobe` (dict): A wardrobe dict with an 'items' key containing a list of wardrobe item dicts. May be empty — handle this gracefully.

**What it returns:**
<!-- Describe the return value -->
 A non-empty string with outfit suggestions. 
**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
If the wardrobe is empty, offer general styling advice for the item. Rather than raising an exception or returning an empty string.
---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
Generate a short, shareable outfit caption for the thrifted find.
**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): The outfit suggestion string from suggest_outfit().
- `new_item`(dict): The listing dict for the thrifted item.
**What it returns:**
<!-- Describe the return value -->
 A 2–4 sentence string usable as an Instagram/TikTok caption. 
**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
If outfit is empty or missing, return a descriptive error message. string — do NOT raise an exception.
---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->

     Initialize: Call _new_session(query, wardrobe) to create the state dictionary.

     Parse: Extract the description, size, and max_price from the user's natural language query using regex. Store these in session["parsed"].

     Execute Search: Pass the parsed parameters into search_listings(). Store the returned list in session["search_results"].

     Conditional Branch (Check Results): * If session["search_results"] is empty: Set session["error"] = "No items found matching your criteria. Try widening your price range or removing the size filter." Return the session early and terminate the loop.

     If session["search_results"] is NOT empty: Set session["selected_item"] = session["search_results"][0] and proceed to the next step.

     Execute Outfit Generation: Pass session["selected_item"] and session["wardrobe"] into suggest_outfit(). Store the returned string in session["outfit_suggestion"].

     Execute Fit Card Generation: Pass session["outfit_suggestion"] and session["selected_item"] into create_fit_card(). Store the returned string in session["fit_card"].

     Complete: Return the fully populated session dictionary.
   
---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
The agent uses a dictionary, initialized via _new_session(), to store and pass state.

The raw query is broken into description, size, and max_price, which are stored in session["parsed"].

These parsed parameters are passed as arguments into search_listings(). The first returned listing is saved to session["selected_item"].

session["selected_item"] and the original session["wardrobe"] are passed into suggest_outfit(). The resulting string is saved to session["outfit_suggestion"], which is then immediately passed alongside session["selected_item"] into create_fit_card().

If any step fails (e.g., search returns an empty list), session["error"] is populated with a descriptive string, and the loop terminates early, returning the current session state back to the UI.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | "No items found. Try widening your price range or search terms." |
| suggest_outfit | Wardrobe is empty | "Found [Item]! Since your closet is empty, try styling this with classic denim or black trousers." |
| create_fit_card | Outfit input is missing or incomplete | "Error: Could not generate a caption because the outfit suggestion failed."|

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->
```mermaid
graph TD
    A[User Query & Wardrobe] --> B[Planning Loop: run_agent]
    B --> C[Parse Query]
    C --> D{search_listings}

    D -- "results = []" --> E[Session: error = 'No items found...']
    E --> F[Return Session Early]
    
    D -- "results = [item, ...]" --> G[Session: selected_item = results[0]]
    G --> H[suggest_outfit]
    
    H --> I[Session: outfit_suggestion = '...']
    I --> J[create_fit_card]
    
    J --> K[Session: fit_card = '...']
    K --> L[Return Final Session]
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
Tool: Python + Groq API

Input: I will provide the tool specifications from this document alongside the stubbed functions in tools.py.

Task: Implement the search_listings filtering and keyword-scoring logic using standard Python structures. For suggest_outfit and create_fit_card, implement the Groq API calls (e.g., client.chat.completions.create) using custom system prompts based directly on the conditions defined in the spec.

Verification: I will write isolated test scripts calling each function with mock inputs (e.g., passing get_example_wardrobe() to suggest_outfit) and print the outputs to ensure edge cases (like an empty wardrobe or missing outfit strings) resolve exactly as described in the Error Handling section.

**Milestone 4 — Planning loop and state management:**
Tool: Python (Regex / String manipulation)

Input: The state management plan and architecture flowchart from this document, plus the stubbed run_agent() function.

Task: Implement query parsing using basic regex to extract sizes and prices, then write the sequential logic to chain search_listings, suggest_outfit, and create_fit_card while actively updating the session dictionary.

Verification: I will execute the agent.py CLI tests at the bottom of the file to verify both the happy path (finding a graphic tee) and the no-results path (designer ballgown under $5), ensuring session["error"] catches the failure properly.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
The agent parses the user's query. It extracts description = "vintage graphic tee", max_price = 30.0, and size = None. It calls search_listings("vintage graphic tee", size=None, max_price=30.0).

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
search_listings filters the mock dataset and scores the items, returning a list of matches. The top result, "lst_006" (Graphic Tee — 2003 Tour Bootleg Style for $24.00), is saved to session["selected_item"]. The agent then calls suggest_outfit(selected_item, wardrobe).

**Step 3:**
<!-- Continue until the full interaction is complete -->
suggest_outfit constructs a prompt for the LLM featuring the bootleg tee and the user's existing wardrobe items. The LLM returns a styling suggestion: "Pair the bootleg graphic tee with your baggy straight-leg dark wash jeans and chunky white sneakers for a relaxed, streetwear-inspired 90s silhouette." This is stored in session["outfit_suggestion"]. The agent calls create_fit_card(outfit_suggestion, selected_item). create_fit_card sends the outfit string and item details to the LLM. It generates an authentic caption, storing it in session["fit_card"].

**Final output to user:**
<!-- What does the user actually see at the end? -->

Final output to user:
The user sees the bootleg tee listing details in the first panel, the specific styling advice using their jeans and sneakers in the second panel, and a trendy, ready-to-share caption mentioning the $24 Depop find in the third panel.
