# import os
# import requests
# from dotenv import load_dotenv


# load_dotenv()


# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# LLM_BASE = os.getenv("LLM_BASE")
# MODEL_ID = os.getenv("MODEL_ID")

# def query_text_only(prompt):
#     url = f"{LLM_BASE}/v1/chat/completions"
#     headers = {
#         "Authorization": f"Bearer {OPENAI_API_KEY}",
#         "Content-Type": "application/json"
#     }

#     payload = {
#         "model": MODEL_ID,
#         "messages": [
#             {"role": "system", "content": "You are an accessibility-focused assistant. Reword the navigation directions to be very easy for a person with disability to understand."},
#             {"role": "user", "content": prompt}
#         ],
#         "temperature": 0.2,
#         "max_tokens": 800
#     }

#     try:
#         response = requests.post(url, headers=headers, json=payload)
#         response.raise_for_status()
#         data = response.json()
#         return data["choices"][0]["message"]["content"]
#     except requests.exceptions.RequestException as e:
#         print("[ERROR] Failed to fetch from LLM:", e)
#         return "❗ Sorry, the AI could not generate optimized instructions at the moment."

import os
import requests
from dotenv import load_dotenv


load_dotenv()


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

def generate_llm_response(directions_text):
    try:
        prompt = f"Rewrite the following directions to be simple, step-by-step, and accessible to a person with disabilities:\n\n{directions_text}"

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    
    except Exception as e:
        print("[ERROR] Failed to fetch from Gemini LLM:", e)
        return "Sorry, I couldn't process the navigation instructions right now."
