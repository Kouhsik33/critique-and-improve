import os
from dotenv import load_dotenv

# Load env
load_dotenv()

# Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

print("🚀 Testing APIs...\n")

# =========================
# GEMINI TEST
# =========================
def test_gemini():
    try:
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Hello from Gemini!"
        )

        print("🔹 Gemini API")
        print("✅ Success")
        print("Response:", response.text, "\n")

    except Exception as e:
        print("🔹 Gemini API")
        print("❌ Failed")
        print("Error:", e, "\n")


# =========================
# OPENAI TEST
# =========================
def test_openai():
    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)

        res = client.responses.create(
            model="gpt-4.1-mini",
            input="Hello from OpenAI!"
        )

        print("🔹 OpenAI API")
        print("✅ Success")
        print("Response:", res.output[0].content[0].text, "\n")

    except Exception as e:
        print("🔹 OpenAI API")
        print("❌ Failed")
        print("Error:", e, "\n")


# =========================
# GROQ TEST (FREE 🔥)
# =========================
def test_groq():
    try:
        from groq import Groq

        client = Groq(api_key=GROQ_API_KEY)

        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": "Hello from Groq!"}
            ]
        )

        print("🔹 Groq API")
        print("✅ Success")
        print("Response:", res.choices[0].message.content, "\n")

    except Exception as e:
        print("🔹 Groq API")
        print("❌ Failed")
        print("Error:", e, "\n")


# =========================
# RUN ALL
# =========================
if __name__ == "__main__":
    test_gemini()   # may fail (quota)
    test_openai()   # ✅ working
    test_groq()     # ✅ free + fast