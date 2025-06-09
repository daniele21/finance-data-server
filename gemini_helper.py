import os
import google.generativeai as genai

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY not set")

genai.configure(api_key=API_KEY)

def parse_transactions(raw_text):
    prompt = (
        "Extract all transactions from the text below. "
        "Return directly just the VALID JSON list where each item has fields: "
        "ticker, quantity, price, date (YYYY-MM-DD), label, and portfolio."
        "DO NOT ADD ANYTHING ELSE"
    )
    model_name = os.getenv("GEMINI_MODEL", "gemini-pro")
    model = genai.GenerativeModel(model_name)
    config = genai.GenerationConfig(temperature=0.0, max_output_tokens=256)
    response = model.generate_content([prompt, raw_text], generation_config=config)

    # response.text holds the generated JSON string
    import json
    cleaned = response.text.strip("`\n ").replace('json', '')
    return json.loads(cleaned)
