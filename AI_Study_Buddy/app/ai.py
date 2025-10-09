import openai
import re
import json

openai.api_key = "YOUR_API_KEY"

def summarize_text(text):
    prompt = f"Summarize the following study notes into 3-4 concise bullet points:\n\n{text}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response["choices"][0]["message"]["content"]

def generate_quiz(text):
    prompt = (
        "Generate 3 multiple-choice questions based on the following text. "
        "Each question should have 1 correct answer and 3 wrong options. "
        "Format as: Q1: [question]\\nA) ...\\nB) ...\\nC) ...\\nD) ...\\nAnswer: [letter]\n\n"
        f"{text}"
    )
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response["choices"][0]["message"]["content"]

def generate_structured_quiz(text):
    prompt = (
        "Generate a short quiz (3 multiple-choice questions) based on the following notes. "
        "Return your answer strictly in JSON format like this:\n\n"
        "[\n"
        "  {\n"
        '    "question": "What is ...?",\n'
        '    "options": ["Option A", "Option B", "Option C", "Option D"],\n'
        '    "answer": "Option A"\n'
        "  },\n"
        "  ...\n"
        "]\n\n"
        f"Notes:\n{text}"
    )

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    raw = response["choices"][0]["message"]["content"].strip()

    # Attempt to extract valid JSON
    try:
        quiz_data = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback if formatting is slightly off
        quiz_data = [{"question": "Error parsing AI output", "options": [], "answer": ""}]

    return quiz_data

def generate_feedback(note_title, questions, user_answers, correct_answers, score, total):
    """
    Generate AI feedback analyzing user's performance and recommending improvements.
    """
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

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
    )

    return response["choices"][0]["message"]["content"].strip()