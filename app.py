"""
app.py
Gradio interface for FitFindr. The layout and wiring are already set up —
your job is to fill in handle_query() so it calls run_agent() and maps
the session results to the three output panels.
"""

import gradio as gr
from agent import run_agent
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


# ── query handler ─────────────────────────────────────────────────────────────

def handle_query(user_query: str, wardrobe_choice: str) -> tuple[str, str, str]:
    """
    Called by Gradio when the user submits a query.
    """
    # Step 1: Guard against empty query
    if not user_query or not user_query.strip():
        return "Please enter a search query.", "", ""

    # Step 2: Select wardrobe
    wardrobe = (
        get_empty_wardrobe()
        if wardrobe_choice == "Empty wardrobe (new user)"
        else get_example_wardrobe()
    )

    # Step 3: Run the agent
    session = run_agent(user_query.strip(), wardrobe)

    # Step 4: Handle early-exit error
    if session["error"]:
        return session["error"], "", ""

    # Step 5: Format and return all three panels
    item = session["selected_item"]
    listing_text = (
        f"{item['title']}\n\n"
        f"💰 ${item['price']:.2f}  ·  {item['platform'].capitalize()}\n"
        f"📐 Size: {item['size']}\n"
        f"✅ Condition: {item['condition'].capitalize()}\n"
        f"🏷️ Brand: {item.get('brand') or 'Unbranded'}\n"
        f"🎨 Colors: {', '.join(item['colors'])}\n\n"
        f"🔖 Tags: {', '.join(item['style_tags'])}\n\n"
        f"{item['description']}"
    )

    return listing_text, session["outfit_suggestion"], session["fit_card"]


# ── interface ─────────────────────────────────────────────────────────────────

EXAMPLE_QUERIES = [
    "vintage graphic tee under $30",
    "90s track jacket in size M",
    "flowy midi skirt under $40",
    "black combat boots size 8",
    "designer ballgown size XXS under $5",   # deliberate no-results test
]


def build_interface():
    with gr.Blocks(title="FitFindr", theme=gr.themes.Soft(
        primary_hue="pink",
        secondary_hue="purple",
        neutral_hue="rose",
        font=gr.themes.GoogleFont("DM Sans"),
).set(
    body_background_fill="#fff0f6",
    body_background_fill_dark="#fff0f6",
    block_background_fill="#ffe4f0",
    block_background_fill_dark="#ffe4f0",
    input_background_fill="#fff7fb",
    input_background_fill_dark="#fff7fb",
    body_text_color="#3d1a2e",
    body_text_color_dark="#3d1a2e",
    table_row_focus="#ffd6eb",
    block_label_background_fill="#ffb3d9",
    block_label_background_fill_dark="#ffb3d9",
    table_even_background_fill="#fff0f6",
    table_even_background_fill_dark="#fff0f6",
    table_odd_background_fill="#ffe4f0",
    table_odd_background_fill_dark="#ffe4f0",
)) as demo:
        gr.Markdown("""
# FitFindr 🛍️
Find secondhand pieces and get outfit ideas based on your wardrobe.
Describe what you're looking for — include size and price if you want to filter.
        """)

        with gr.Row():
            query_input = gr.Textbox(
                label="What are you looking for?",
                placeholder="e.g. vintage graphic tee under $30, size M",
                lines=2,
                scale=3,
            )
            wardrobe_choice = gr.Radio(
                choices=["Example wardrobe", "Empty wardrobe (new user)"],
                value="Example wardrobe",
                label="Wardrobe",
                scale=1,
            )

        submit_btn = gr.Button("Find it", variant="primary")

        with gr.Row():
            listing_output = gr.Textbox(
                label="🛍️ Top listing found",
                lines=8,
                interactive=False,
            )
            outfit_output = gr.Textbox(
                label="👗 Outfit idea",
                lines=8,
                interactive=False,
            )
            fitcard_output = gr.Textbox(
                label="✨ Your fit card",
                lines=8,
                interactive=False,
            )

        gr.Examples(
            examples=[[q, "Example wardrobe"] for q in EXAMPLE_QUERIES],
            inputs=[query_input, wardrobe_choice],
            label="Try these queries",
        )

        submit_btn.click(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[listing_output, outfit_output, fitcard_output],
        )
        query_input.submit(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[listing_output, outfit_output, fitcard_output],
        )

    return demo


if __name__ == "__main__":
    demo = build_interface()
    demo.launch()