import os
from google import genai
from google.genai import types

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set")

# Initialize the client (developer API mode)
client = genai.Client(api_key=API_KEY, vertexai=False)

def parse_transactions(raw_text):
    prompt = (
        "Extract all transactions from the text below. "
        "Return directly just the VALID JSON list where each item has fields: "
        "ticker, quantity, price, date (YYYY-MM-DD), label, and portfolio."
        "DO NOT ADD ANYTHING ELSE"
    )
    # Build your config object instead of passing temperature directly
    config = types.GenerateContentConfig(
        temperature=0.0,         # for deterministic parsing
        max_output_tokens=256    # enough room for the JSON
    )

    # Now pass it in via `config=`
    response = client.models.generate_content(
        model="gemini-2.0-flash-001",
        contents=[prompt, raw_text],
        config=config
    )

    # response.text holds the generated JSON string
    import json
    cleaned = response.text.strip("`\n ").replace('json', '')
    return json.loads(cleaned)
