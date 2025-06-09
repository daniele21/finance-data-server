import os
import google.generativeai as genai

API_KEY = os.getenv("GEMINI_API_KEY")
# Allow selecting a custom model via environment variable. Defaults to the
# standard Gemini Pro model.  The integration tests set this to the Flash model.
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-pro")

def get_model():
    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY environment variable not set")
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
    return model

def parse_transactions(raw_text):
    """Use Gemini to parse raw transaction text into structured JSON."""
    model = get_model()
    prompt = (
        "Extract all transactions from the text below. "
        "Return a JSON list where each item has fields: ticker, quantity, "
        "price, date (YYYY-MM-DD), label, and portfolio."
    )
    response = model.generate_content([prompt, raw_text])
    try:
        # Gemini returns text; we expect the JSON to be in a code block or plain
        import json
        cleaned = response.text.strip('`\n ')
        return json.loads(cleaned)
    except Exception as e:
        raise RuntimeError(f"Failed to parse transactions: {e}")

