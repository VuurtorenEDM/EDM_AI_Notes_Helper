import os 
import json
from google import genai
from google.genai import types

# --- Client Initialization ---
# Initialize the Gemini client. It will automatically use the GEMINI_API_KEY 
# environment variable or look for credentials in your environment.
try:
    client = genai.Client()
except Exception as e:
    # Handle case where API key is not found (for debugging)
    print(f"Error initializing Gemini client: {e}")
    client = None

# Using gemini-2.5-flash for speed and JSON support.

def summarize_text(text):
    """Summarizes study notes into concise bullet points using Gemini."""
    if not client: return "Error: Gemini client not initialized."
    
    prompt = f"Summarize the following study notes into 3-4 concise bullet points:\n\n{text}"
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.7
        )
    )
    return response.text.strip()

def generate_quiz(text):
    """Generates a raw, formatted multiple-choice quiz using Gemini."""
    if not client: return "Error: Gemini client not initialized."
    
    prompt = (
        "Generate 3 multiple-choice questions based on the following text. "
        "Each question should have 1 correct answer and 3 wrong options. "
        "Format as: Q1: [question]\\nA) ...\\nB) ...\\nC) ...\\nD) ...\\nAnswer: [letter]\n\n"
        f"{text}"
    )
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.7
        )
    )
    return response.text.strip()

def generate_structured_quiz(text):
    """Generates a quiz and enforces strict JSON output format using Gemini."""
    if not client: return [{"question": "Error: Gemini client not initialized.", "options": [], "answer": ""}]

    # Define the JSON structure using a Schema (Pydantic style, but using types.Schema)
    quiz_schema = types.Schema(
        type=types.Type.ARRAY,
        items=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "question": types.Schema(type=types.Type.STRING),
                "options": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
                "answer": types.Schema(type=types.Type.STRING)
            },
            required=["question", "options", "answer"]
        )
    )

    prompt = f"Generate a short quiz (3 multiple-choice questions) based on the following notes. Return the output as a JSON array of question objects.\n\nNotes:\n{text}"

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
            response_mime_type="application/json",
            response_schema=quiz_schema
        )
    )

    # Gemini's structured output response content is guaranteed to be valid JSON string
    raw = response.text.strip()

    try:
        # Parse the JSON output
        quiz_data = json.loads(raw)
    except json.JSONDecodeError:
        # Should rarely happen with structured output, but included for safety
        quiz_data = [{"question": "Error parsing AI output", "options": [], "answer": ""}]

    return quiz_data

def generate_feedback(note_title, questions, user_answers, correct_answers, score, total):
    """Generate AI feedback analyzing user's performance and recommending improvements."""
    if not client: return "Error: Gemini client not initialized."

    prompt = f"""
You are an intelligent study coach. The user has taken a quiz on the topic "{note_title}".
The quiz had {total} questions, and they scored {score}/{total}.

Here are the questions, the user's answers, and the correct answers:
{[
    {
        "question": q,
        "user_answer": u,
        "correct_answer": c
    } for q, u, c in zip(questions, user_answers, correct_answers)
]}

Please write a short feedback paragraph (3-5 sentences) identifying what the user did well,
where they struggled, and specific study recommendations to improve for next time.
Keep it encouraging and informative.
"""

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.6
        )
    )
    return response.text.strip()